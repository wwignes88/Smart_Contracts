// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;
pragma abicoder v2;

import './interfaces/IUniswapV3Staker.sol';
import './libraries/IncentiveId.sol';
import './libraries/RewardMath.sol';
import './libraries/NFTPositionInfo.sol';
import './libraries/TransferHelperExtended.sol';

import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol';
import '@v3MOCKS/MERC20.sol';

import '@uniswap/v3-periphery/contracts/base/Multicall.sol';

/// @title Uniswap V3 canonical staking interface
contract MLiquidityStaker is IUniswapV3Staker, Multicall {
    //VARIABLE 
        /// @notice Represents a staking incentive
        struct Incentive {
            uint256 totalRewardUnclaimed;
            uint160 totalSecondsClaimedX128;
            uint96 numberOfStakes;
        }

        /// @notice Represents the deposit of a liquidity NFT
        struct Deposit {
            address owner;
            address operator;
            uint48 numberOfStakes;
            int24 tickLower;
            int24 tickUpper;
        }

        /// @notice Represents a staked liquidity NFT
        struct Stake {
            uint160 secondsPerLiquidityInsideInitialX128;
            uint96 liquidityNoOverflow;
            uint128 liquidityIfOverflow;
        }

        bytes32[] public incentiveIds;
        /// @inheritdoc IUniswapV3Staker
        IUniswapV3Factory public immutable override factory;
        /// @inheritdoc IUniswapV3Staker
        //INonfungiblePositionManager public immutable override nonfungiblePositionManager;

        /// @inheritdoc IUniswapV3Staker
        uint256 public immutable override maxIncentiveStartLeadTime;
        /// @inheritdoc IUniswapV3Staker
        uint256 public immutable override maxIncentiveDuration;

        /// @dev bytes32 refers to the return value of IncentiveId.compute
        mapping(bytes32 => Incentive) public override incentives;

        /// @dev bytes32 refers to the return value of IncentiveId.compute
        mapping(bytes32 => IncentiveKey) public incentiveKeys;

        /// @dev deposits[tokenId] => Deposit
        mapping(uint256 => Deposit) public override deposits;

        /// @dev stakes[tokenId][incentiveHash] => Stake
        mapping(uint256 => mapping(bytes32 => Stake)) private _stakes;

        
        mapping(bytes32 => bool) public incentiveExists;

        /// @inheritdoc IUniswapV3Staker
        mapping(MERC20 => mapping(address => uint256)) public override rewards;

        /// @param _factory the Uniswap V3 factory
        /// @param _nonfungiblePositionManager the NFT position manager contract address
        /// @param _maxIncentiveStartLeadTime the max duration of an incentive in seconds
        /// @param _maxIncentiveDuration the max amount of seconds into the future the incentive startTime can be set
        constructor(
            IUniswapV3Factory _factory,
            INonfungiblePositionManager _nonfungiblePositionManager,
            uint256 _maxIncentiveStartLeadTime,
            uint256 _maxIncentiveDuration
        ) {
            factory = _factory;
            nonfungiblePositionManager = _nonfungiblePositionManager;
            maxIncentiveStartLeadTime = _maxIncentiveStartLeadTime;
            maxIncentiveDuration = _maxIncentiveDuration;
        }
        //
    //

    //          --------------------------------------
    //          --------------- VIEW FUNCS -----------
    //          --------------------------------------


    function compute_incentiveId(IncentiveKey memory key) public view returns (bytes32 key_Id){
        key_Id = IncentiveId.compute(key);
    }
    
    function numIncentives() public view returns (uint){
        return incentiveIds.length;
    }

    function incentiveId_by_index(uint index) public view returns (bytes32) {
        require(index < incentiveIds.length, "Index out of bounds");
        require(index >= 0, "Index < 0");
        return incentiveIds[index];
    }

    function getIncentiveKey(bytes32 incentiveId) public view returns (
        address rewardToken,
        address pool,
        uint256 startTime,
        uint256 endTime,
        address refundee,
        bool _exists
    ) {
        if(incentiveExists[incentiveId] ==  false){
            _exists = false;
        }
        
        IncentiveKey storage key = incentiveKeys[incentiveId];
        rewardToken  =  address(key.rewardToken);
        pool      =  address(key.pool);
        startTime =  key.startTime;
        endTime   =  key.endTime;
        refundee  =  key.refundee;
    }

    /// @inheritdoc IUniswapV3Staker
        /// @dev rewards[rewardToken][owner] => uint256
    function stakes(uint256 tokenId, bytes32 incentiveId)
        public
        view
        override
        returns (uint160 secondsPerLiquidityInsideInitialX128, uint128 liquidity)
    {
        Stake storage stake = _stakes[tokenId][incentiveId];
        secondsPerLiquidityInsideInitialX128 = stake.secondsPerLiquidityInsideInitialX128;
        liquidity = stake.liquidityNoOverflow;
        if (liquidity == type(uint96).max) {
            liquidity = stake.liquidityIfOverflow;
        }
    }

    /// @inheritdoc IUniswapV3Staker
    function getRewardInfo(IncentiveKey memory key, uint256 tokenId)
        external
        view
        override
        returns (uint256 reward, uint160 secondsInsideX128)
     {
        bytes32 incentiveId = IncentiveId.compute(key);

        (uint160 secondsPerLiquidityInsideInitialX128, uint128 liquidity) = stakes(tokenId, incentiveId);
        require(liquidity > 0, 'UniswapV3Staker::getRewardInfo: stake does not exist');

        Deposit memory deposit = deposits[tokenId];
        Incentive memory incentive = incentives[incentiveId];

        (, uint160 secondsPerLiquidityInsideX128, ) =
            key.pool.snapshotCumulativesInside(deposit.tickLower, deposit.tickUpper);

        (reward, secondsInsideX128) = RewardMath.computeRewardAmount(
            incentive.totalRewardUnclaimed,
            incentive.totalSecondsClaimedX128,
            key.startTime,
            key.endTime,
            liquidity,
            secondsPerLiquidityInsideInitialX128,
            secondsPerLiquidityInsideX128,
            block.timestamp
        );
    }


    //          --------------------------------------
    //          ------- STATE CHANGING FUNCS ---------
    //          --------------------------------------

    /// @notice Upon receiving a Uniswap V3 ERC721 token [a deposit], 
        // creates the token deposit setting deposit owner to `from` address. 
        // MStaker.sol will of course be the ERC721 token owner. Also stakes token
        /// in one or more incentives if properly formatted `data` has a length > 0.
        /// @inheritdoc IERC721Receiver
    function onERC721Received(
        address,
        address from,
        uint256 tokenId,
        bytes calldata data
    ) external override returns (bytes4) {

        require(
            msg.sender == address(nonfungiblePositionManager),
            'UniswapV3Staker::onERC721Received: not a univ3 nft'
        );

        // assign an EOA operator to deposit.
        address EOAoperater = abi.decode(data, (address));

        (, , , , , int24 tickLower, int24 tickUpper, , , , , ) 
            = nonfungiblePositionManager.positions(tokenId);
        
        deposits[tokenId] = Deposit({owner: from, 
                                    operator: EOAoperater,
                                    numberOfStakes: 0, 
                                    tickLower: tickLower, 
                                    tickUpper: tickUpper});

        emit DepositTransferred(tokenId, from, from, EOAoperater);

        /*
        if (data.length > 0) {
            if (data.length == 160) {
                _stakeToken(abi.decode(data, (IncentiveKey)), tokenId);
            } else {
                IncentiveKey[] memory keys = abi.decode(data, (IncentiveKey[]));
                for (uint256 i = 0; i < keys.length; i++) {
                    _stakeToken(keys[i], tokenId);
                }
            }
        }*/
        return this.onERC721Received.selector;
    }


    /// @inheritdoc IUniswapV3Staker
    function createIncentive(IncentiveKey memory key, uint256 reward) external override {
        require(reward > 0, 'UniswapV3Staker::createIncentive: reward must be positive');
        require(
            block.timestamp <= key.startTime,
            'UniswapV3Staker::createIncentive: start time must be now or in the future'
        );
        require(
            key.startTime - block.timestamp <= maxIncentiveStartLeadTime,
            'UniswapV3Staker::createIncentive: start time too far into future'
        );
        require(key.startTime < key.endTime, 'UniswapV3Staker::createIncentive: start time must be before end time');
        require(
            key.endTime - key.startTime <= maxIncentiveDuration,
            'UniswapV3Staker::createIncentive: incentive duration is too long'
        );

        bytes32 incentiveId = IncentiveId.compute(key);

        // update incentiveId array(s)
        incentiveIds.push(incentiveId);
        incentiveExists[incentiveId] = true;
        // map id to incentive key
        incentiveKeys[incentiveId] = key;
        // map id to incentive
        incentives[incentiveId].totalRewardUnclaimed += reward;

        TransferHelperExtended.safeTransferFrom(address(key.rewardToken), msg.sender, address(this), reward);

        emit IncentiveCreated(key.rewardToken, key.pool, key.startTime, key.endTime, key.refundee, reward, incentiveId);
    }

    /// @inheritdoc IUniswapV3Staker
    function endIncentive(IncentiveKey memory key) external override returns (uint256 refund) {
        require(block.timestamp >= key.endTime, 'UniswapV3Staker::endIncentive: cannot end incentive before end time');

        bytes32 incentiveId = IncentiveId.compute(key);
        incentiveExists[incentiveId] = false;
        Incentive storage incentive = incentives[incentiveId];

        refund = incentive.totalRewardUnclaimed;

        require(refund > 0, 'UniswapV3Staker::endIncentive: no refund available');
        require(
            incentive.numberOfStakes == 0,
            'UniswapV3Staker::endIncentive: cannot end incentive while deposits are staked'
        );

        // issue the refund
        incentive.totalRewardUnclaimed = 0;
        TransferHelperExtended.safeTransfer(address(key.rewardToken), key.refundee, refund);

        // note we never clear totalSecondsClaimedX128

        emit IncentiveEnded(incentiveId, refund);
    }

    /// @inheritdoc IUniswapV3Staker
    function transferDeposit(uint256 tokenId, address newOwner, address operator_) external override depositOnwership(tokenId) {
        require(newOwner != address(0), 'UniswapV3Staker::transferDeposit: invalid transfer recipient');
        address oldOwner  = deposits[tokenId].owner;
        deposits[tokenId].owner = newOwner;
        deposits[tokenId].operator = operator_;
        emit DepositTransferred(tokenId, oldOwner, newOwner, operator_);
    }

    /// @inheritdoc IUniswapV3Staker
    function withdrawToken(
        uint256 tokenId,
        address to,
        bytes memory data
     ) external override  depositOnwership(tokenId){
        require(to != address(this), 'UniswapV3Staker::withdrawToken: cannot withdraw to staker contract');
        Deposit memory deposit = deposits[tokenId];
        require(deposit.numberOfStakes == 0, 'UniswapV3Staker::withdrawToken: cannot withdraw token while staked');

        delete deposits[tokenId];
        emit DepositTransferred(tokenId, deposit.owner, address(0), deposit.operator);
        nonfungiblePositionManager.safeTransferFrom(address(this), to, tokenId, data);
    }

    /// @inheritdoc IUniswapV3Staker
    function stakeToken(IncentiveKey memory key, uint256 tokenId) external override depositOnwership(tokenId) {
        _stakeToken(key, tokenId);
    }

    /// @inheritdoc IUniswapV3Staker
    function unstakeToken(IncentiveKey memory key, uint256 tokenId) external override depositOnwership(tokenId){
        Deposit memory deposit = deposits[tokenId];
        // anyone can call unstakeToken if the block time is after the end time of the incentive
        if (block.timestamp < key.endTime) {
            require(
                deposit.owner == msg.sender || deposit.operator == msg.sender,
                'UniswapV3Staker::unstakeToken: only owner/ operator can withdraw token before incentive end time'
            );
        }


        bytes32 incentiveId = IncentiveId.compute(key);

        (uint160 secondsPerLiquidityInsideInitialX128, uint128 liquidity) = stakes(tokenId, incentiveId);

        require(liquidity != 0, 'UniswapV3Staker::unstakeToken: stake does not exist');

        Incentive storage incentive = incentives[incentiveId];

        deposits[tokenId].numberOfStakes--;
        incentive.numberOfStakes--;

        (, uint160 secondsPerLiquidityInsideX128, ) =
            key.pool.snapshotCumulativesInside(deposit.tickLower, deposit.tickUpper);
        (uint256 reward, uint160 secondsInsideX128) =
            RewardMath.computeRewardAmount(
                incentive.totalRewardUnclaimed,
                incentive.totalSecondsClaimedX128,
                key.startTime,
                key.endTime,
                liquidity,
                secondsPerLiquidityInsideInitialX128,
                secondsPerLiquidityInsideX128,
                block.timestamp
            );

        // if this overflows, e.g. after 2^32-1 full liquidity seconds have been claimed,
        // reward rate will fall drastically so it's safe
        incentive.totalSecondsClaimedX128 += secondsInsideX128;
        // reward is never greater than total reward unclaimed
        incentive.totalRewardUnclaimed -= reward;
        // this only overflows if a token has a total supply greater than type(uint256).max
        rewards[key.rewardToken][deposit.owner] += reward;

        Stake storage stake = _stakes[tokenId][incentiveId];
        delete stake.secondsPerLiquidityInsideInitialX128;
        delete stake.liquidityNoOverflow;
        if (liquidity >= type(uint96).max) delete stake.liquidityIfOverflow;
        emit TokenUnstaked(tokenId, incentiveId);
    }

    /// @inheritdoc IUniswapV3Staker
    function claimReward(
        MERC20 rewardToken,
        address to,
        uint256 amountRequested
     ) external override returns (uint256 reward) {
        reward = rewards[rewardToken][msg.sender];
        if (amountRequested != 0 && amountRequested < reward) {
            reward = amountRequested;
        }

        rewards[rewardToken][msg.sender] -= reward;
        TransferHelperExtended.safeTransfer(address(rewardToken), to, reward);

        emit RewardClaimed(to, reward);
    }

    /// @dev Stakes a deposited token without doing an ownership check
    function _stakeToken(IncentiveKey memory key, uint256 tokenId) private {
        require(block.timestamp >= key.startTime, 'UniswapV3Staker::stakeToken: incentive not started');
        require(block.timestamp < key.endTime, 'UniswapV3Staker::stakeToken: incentive ended');

        bytes32 incentiveId = IncentiveId.compute(key);

        require(
            incentives[incentiveId].totalRewardUnclaimed > 0,
            'UniswapV3Staker::stakeToken: non-existent incentive'
        );
        require(
            _stakes[tokenId][incentiveId].liquidityNoOverflow == 0,
            'UniswapV3Staker::stakeToken: token already staked'
        );

        (IUniswapV3Pool pool, int24 tickLower, int24 tickUpper, uint128 liquidity) =
            NFTPositionInfo.getPositionInfo(factory, nonfungiblePositionManager, tokenId);

        require(pool == key.pool, 'UniswapV3Staker::stakeToken: token pool is not the incentive pool');
        require(liquidity > 0, 'UniswapV3Staker::stakeToken: cannot stake token with 0 liquidity');

        deposits[tokenId].numberOfStakes++;
        incentives[incentiveId].numberOfStakes++;

        (, uint160 secondsPerLiquidityInsideX128, ) = pool.snapshotCumulativesInside(tickLower, tickUpper);

        if (liquidity >= type(uint96).max) {
            _stakes[tokenId][incentiveId] = Stake({
                secondsPerLiquidityInsideInitialX128: secondsPerLiquidityInsideX128,
                liquidityNoOverflow: type(uint96).max,
                liquidityIfOverflow: liquidity
            });
        } else {
            Stake storage stake = _stakes[tokenId][incentiveId];
            stake.secondsPerLiquidityInsideInitialX128 = secondsPerLiquidityInsideX128;
            stake.liquidityNoOverflow = uint96(liquidity);
        }

        emit TokenStaked(tokenId, incentiveId, liquidity);
    }

    modifier depositOnwership(uint256 tokenId) {
        require(
            deposits[tokenId].owner == msg.sender || deposits[tokenId].operator == msg.sender,
            'UniswapV3Staker::only deposit owner or operator'
            );
        _;
    }

    function _safeTransferFrom_w_data(
        address from,
        address to,
        uint256 tokenId,
        bytes memory _data
    ) public {
        nonfungiblePositionManager.safeTransferFrom(from, to, tokenId, _data);
    }


}
