// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

// my contracts
import '@v3PeripheryMOCKS/MNonfungiblePositionManager.sol';
import '@v3PeripheryMOCKS/MNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/interfaces/IMNonfungiblePositionManager.sol';
import '@v3PeripheryMOCKS/interfaces/IMNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/interfaces/IStructs.sol';
import '@v3PeripheryMOCKS/MNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/libraries/MTransferHelper.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';

import '@uniswap/v3-core/contracts/libraries/SafeCast.sol';
import '@uniswap/v3-core/contracts/libraries/SqrtPriceMath.sol';
import '@uniswap/v3-core/contracts/libraries/TickMath.sol';
import '@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol';
import '@uniswap/v3-periphery/contracts/libraries/LiquidityAmounts.sol';

import "@openzeppelin/contracts/utils/Address.sol";


contract MliquidityMiner is IERC721Receiver{
    using Address for address;
    using SafeCast for uint256;
    using SafeCast for int256;

    // VARIABLES
        MNonfungiblePositionManager public immutable nonfungiblePositionManager;
        MNonfungiblePositionManagerII public immutable nonfungiblePositionManagerII;

        /// @notice Represents the deposit of an NFT
        struct Deposit {
            address owner;
            uint128 liquidity;
            address token0;
            address token1;
        }

        mapping (address => uint256[]) public tokenOwnership;

        /// @dev deposits[tokenId] => Deposit
        mapping(uint256 => Deposit) public deposits;


        constructor( 
                    MNonfungiblePositionManager _nonfungiblePositionManager,
                    MNonfungiblePositionManagerII _nonfungiblePositionManagerII
        ){
                nonfungiblePositionManager = _nonfungiblePositionManager;
                nonfungiblePositionManagerII = _nonfungiblePositionManagerII;
        }
    //

    // Implementing `onERC721Received` so this contract can receive custody of erc721 tokens
    function onERC721Received(
        address operator,
        address,
        uint256 tokenId,
        bytes calldata
     ) external override returns (bytes4) {
        // get position information

        _createDeposit(operator, tokenId);

        return this.onERC721Received.selector;
    }

    function _createDeposit(address owner, uint256 tokenId) internal {
        (, , address token0, address token1, , , , uint128 liquidity, , , , ) =
            nonfungiblePositionManagerII.positions(tokenId);

        // set the owner and data for position
        // operator is msg.sender
        deposits[tokenId] = Deposit({owner: owner, liquidity: liquidity, token0: token0, token1: token1});
    }

    // set/ get min mint amounts
    uint256 Amount0Min;
    uint256 Amount1Min;
    function setMinMintAmounts(uint256 amount0Min, uint256 amount1Min) external {
        Amount0Min = amount0Min;
        Amount1Min = amount1Min;
    }
    function getMinMintAmounts() external view returns (uint256 _Amount0Min, uint256 _Amount1Min){
        _Amount0Min = Amount0Min;
        _Amount1Min = Amount1Min;
    }

    //require(amount0 >= myMintParams.Amount0Min && amount1 >= myMintParams.Amount1Min, 'Price slippage check');
    struct myMintParams{
        address tokenA;
        address tokenB;
        uint256 amount0ToMint;
        uint256 amount1ToMint;
        uint256 Amount0Min;
        uint256 Amount1Min;
        int24 tickLower;
        int24 tickUpper;
        uint24 poolFee;
    }



    /// mint
            // revert_option input is for troubleshooting; triggers 'if' statements that hold 
            // revert conditions if option == [some number]
            // this lets the user know how far / where the transaction made it successfully.
    function mintNewPosition(
                myMintParams memory _params,
                int8 option)
            external
            returns (
                uint256 tokenId,
                uint128 liquidity,
                uint256 amount0,
                uint256 amount1
            ){ 

            MTransferHelper.safeTransferFrom(
                                    _params.tokenA,
                                    msg.sender,       // from
                                    address(this),    // to
                                    _params.amount0ToMint);
                if (option == 1){revert("transfered tokenA to liquid");}
            MTransferHelper.safeTransferFrom(
                                    _params.tokenB, 
                                    msg.sender, 
                                    address(this), 
                                    _params.amount1ToMint);
                if (option == 2){revert("transfered tokenB to liquid");}
            MTransferHelper.safeApprove(_params.tokenA, address(nonfungiblePositionManagerII), _params.amount0ToMint);
                if (option == 3){ revert( "approved nonfungII for amount0" ); }
            MTransferHelper.safeApprove(_params.tokenB, address(nonfungiblePositionManagerII), _params.amount1ToMint);
                if (option == 4){ revert( "approved nonfungII for amount1" ); }
        
            IStructs.MintParams memory params =
                IStructs.MintParams({
                    token0        : _params.tokenA,
                    token1        : _params.tokenB,
                    fee           : _params.poolFee,
                    tickLower     : _params.tickLower,
                    tickUpper     : _params.tickUpper,
                    amount0Desired: _params.amount0ToMint,
                    amount1Desired: _params.amount1ToMint,
                    amount0Min    : Amount0Min,
                    amount1Min    : Amount1Min,
                    recipient     : address(this),
                    deadline      : block.timestamp
            });
            (tokenId, liquidity, amount0, amount1) = nonfungiblePositionManager.mint(params, option);
            require(amount0 >= _params.Amount0Min && amount1 >= _params.Amount1Min, 'Price slippage check');

            if (option == 13){ revert("[MLMiner] 13"); }

            if (option < 50){ 
                tokenOwnership[msg.sender].push(tokenId);
                _createDeposit(msg.sender, tokenId);

                // refunds
                    if (amount0 < _params.amount0ToMint) {
                            //MTransferHelper.safeApprove(_params.tokenA, address(nonfungiblePositionManager), 0);
                            uint256 refund0 = _params.amount0ToMint - amount0;
                            if (option == 14){revert("approved/ transfered something....");}
                            MTransferHelper.safeTransfer(
                                                    _params.tokenA,
                                                    msg.sender,    // to
                                                    refund0);
                        }


                    if (amount1 < _params.amount1ToMint) {
                        //MTransferHelper.safeApprove(_params.tokenB, address(nonfungiblePositionManager), 0);
                        if (option == 15){revert("approved/ transfered something....");}
                        uint256 refund1 = _params.amount1ToMint - amount1;
                        MTransferHelper.safeTransfer(
                                                _params.tokenB,
                                                msg.sender,    // to
                                                refund1);
                    }
            }
    }

    function burnPosition(uint256 tokenId) external{
        address depositOwner = deposits[tokenId].owner;
        require(msg.sender == depositOwner, "dep. owner");
        nonfungiblePositionManager.burn( tokenId);
    }

    //========== UNTESTED
    // decrease liquidity of position by 1/frac 
    function decreaseLiquidity(
        uint256 tokenId, 
        uint8 frac,
        int8 option) external returns (
                        uint256 amount0, 
                        uint256 amount1) {
        require(msg.sender == deposits[tokenId].owner, 'Not the owner');
        (, , , , , , , uint128 liquidity, , , , ) = nonfungiblePositionManagerII.positions(tokenId);
        uint128 L_burn = liquidity / frac;
        IMNonfungiblePositionManagerII.DecreaseLiquidityParams memory params =
            IMNonfungiblePositionManagerII.DecreaseLiquidityParams({
                tokenId: tokenId,
                liquidity: L_burn,
                amount0Min: 0,
                amount1Min: 0,
                deadline: block.timestamp
            });
        (amount0, amount1) = nonfungiblePositionManagerII.decreaseLiquidity(params, option);

    }

    function _sendToOwner(
        uint256 tokenId,
        uint256 amount0,
        uint256 amount1
        ) internal {
        // get owner of contract
        address owner  = deposits[tokenId].owner;
        address token0 = deposits[tokenId].token0;
        address token1 = deposits[tokenId].token1;
        // send collected fees to owner
        MTransferHelper.safeTransfer(token0, owner, amount0);
        MTransferHelper.safeTransfer(token1, owner, amount1);
    }
    
    function increaseL(
        uint256 tokenId,
        uint256 amountAdd0,
        uint256 amountAdd1,
        int8 revert_option
        )
        external
        returns (
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1
        ) {

        MTransferHelper.safeTransferFrom(deposits[tokenId].token0, msg.sender, address(this), amountAdd0);
        MTransferHelper.safeTransferFrom(deposits[tokenId].token1, msg.sender, address(this), amountAdd1);
            if (revert_option == 1){
                revert("transferFrom executed");
            }

        MTransferHelper.safeApprove(deposits[tokenId].token0, address(nonfungiblePositionManagerII), amountAdd0);
        MTransferHelper.safeApprove(deposits[tokenId].token1, address(nonfungiblePositionManagerII), amountAdd1);
            if (revert_option == 2){
                revert("approvals done");
            }

        IMNonfungiblePositionManagerII.IncreaseLiquidityParams memory params = IMNonfungiblePositionManagerII.IncreaseLiquidityParams({
            tokenId: tokenId,
            amount0Desired: amountAdd0,
            amount1Desired: amountAdd1,
            amount0Min: 0,
            amount1Min: 0,
            deadline: block.timestamp
        });

        (liquidity, amount0, amount1) = nonfungiblePositionManagerII.increaseLiquidity(params, revert_option);

    }

    function collectFees(
        uint256 tokenId, 
        uint128 _amount0Max,
        uint128 _amount1Max,
        int8 revert_option) public returns (uint256 amount0, uint256 amount1) {
        // Caller must own the ERC721 position, meaning it must be a deposit

        // set amount0Max and amount1Max to uint256.max to collect all fees
        // alternatively can set recipient to msg.sender and avoid another transaction in `sendToOwner`
        IMNonfungiblePositionManagerII.CollectParams memory params =
            IMNonfungiblePositionManagerII.CollectParams({
                tokenId: tokenId,
                recipient: address(this),
                amount0Max: _amount0Max,
                amount1Max: _amount1Max
        });

        (amount0, amount1) = nonfungiblePositionManagerII.collect(params, revert_option);
        if (revert_option == 1){revert("nonfung collect");}
        // send collected feed back to owner
        _sendToOwner(tokenId, amount0, amount1);
    }

    /// @notice Transfers the NFT to the owner
    function retrieveNFT(uint256 tokenId) external {
        // must be the owner of the NFT
        require(msg.sender == deposits[tokenId].owner, 'Not the owner');
        // transfer ownership to original owner
        nonfungiblePositionManager.safeTransferFrom(address(this), msg.sender, tokenId);
        //remove information related to tokenId
        delete deposits[tokenId];
    }

    /*
    function transferToStaker(
            address from,
            address staker, 
            uint256 tokenId,
            address deposit_EOA_operator
        ) public {
            require(deposits[tokenId].owner == msg.sender , "only token minter");
            // send 'to' address as encoded data for 'onERC721Received'
            // which will set 'to' as owner of the deposit
            bytes memory _data = abi.encode(deposit_EOA_operator);
            nonfungiblePositionManager.safeTransferFrom(from, staker, tokenId, _data);
    }
    */

    //========== MY FUNCTIONS
    // NFT functions
        // get tokenIds of owner
        function getTokenIds(address tokenOwner) external view returns (uint256[] memory) {
            return tokenOwnership[tokenOwner];
        }

        // count tokens held by owner
        function getTokenCount(address account) external view returns (uint256) {
            return tokenOwnership[account].length;
        }

        // retrieve deposit
        function getDeposit(uint256 tokenId) public view returns (Deposit memory) {
            return deposits[tokenId];
        }
    //



}