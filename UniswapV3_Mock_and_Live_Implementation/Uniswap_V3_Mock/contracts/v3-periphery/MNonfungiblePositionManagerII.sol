// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

// my contracts
import '@v3PeripheryMOCKS/base/MLiquidityManager.sol'; 
import '@v3PeripheryMOCKS/interfaces/IMNonfungiblePositionManagerII.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';


import '@uniswap/v3-core/contracts/libraries/FullMath.sol';
import '@uniswap/v3-periphery/contracts/libraries/PositionKey.sol';

//* add in transfer functionality
import "@openzeppelin/contracts/utils/Address.sol";


contract MNonfungiblePositionManagerII is 
    MLiquidityManager,
    IMNonfungiblePositionManagerII
 {
    using Address for address;

    //address factoryAddress;
    //address factoryIIAddress;
    constructor(
        address _factory,
        address _factoryII, 
        address _WETH9) MLiquidityManager(_factory, _factoryII, _WETH9) {}
            //factoryAddress = _factory;
            //factoryIIAddress = _factoryII;
    //
    
    // VARIABLES
        
        /// @dev IDs of pools assigned by this contract
        mapping(address => uint80) public  _poolIds;

        /// @dev Pool keys by pool ID, to save on SSTOREs for position data
        mapping(uint80 => MPoolAddress.PoolKey) public _poolIdToPoolKey;

        /// @dev The token ID position data
        mapping(uint256 => Position_) public _positions;

        uint80 public _nextPoolId = 1;

    //

    function positions(uint256 tokenId)
        external
        view
        override
        returns (
            uint96 nonce,
            address operator,
            address token0,
            address token1,
            uint24 fee,
            int24 tickLower,
            int24 tickUpper,
            uint128 liquidity,
            uint256 feeGrowthInside0LastX128,
            uint256 feeGrowthInside1LastX128,
            uint128 tokensOwed0,
            uint128 tokensOwed1
        )
     {
        Position_ memory position = _positions[tokenId];
        require(position.poolId != 0, '[Nonfung :: pos} Invalid token ID');
        MPoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];
        return (
            position.nonce,
            position.operator,
            poolKey.token0,
            poolKey.token1,
            poolKey.fee,
            position.tickLower,
            position.tickUpper,
            position.liquidity,
            position.feeGrowthInside0LastX128,
            position.feeGrowthInside1LastX128,
            position.tokensOwed0,
            position.tokensOwed1
        );
    }
    //
    function get_poolIdToPoolKey(uint80 poolID) 
        external 
        view 
        returns(MPoolAddress.PoolKey memory pool_key){
            pool_key = _poolIdToPoolKey[poolID];
    }
    // add only ERC721Manager modifier!!
    function ERC721Manager_Add_Liquidity(AddLiquidityParams memory params, int8 option)  
        external 
        override 
        returns (
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1,
            IUniswapV3Pool pool
        ){ 
            (liquidity, amount0, amount1, pool) = addLiquidity(params, option);
    }

    function increaseLiquidity(IncreaseLiquidityParams calldata params, int8 option)
        external
        payable
        override
        returns (
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1
        )
     {
            
        //Position_ storage position = _positions[params.tokenId];
        Position_ storage position = _positions[params.tokenId];
        MPoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];

        IUniswapV3Pool pool;
        (liquidity, amount0, amount1, pool) = addLiquidity(
            AddLiquidityParams({
                token0: poolKey.token0,
                token1: poolKey.token1,
                recipient: address(this),
                fee: poolKey.fee,
                tickLower: position.tickLower,
                tickUpper: position.tickUpper,
                amount0Desired: params.amount0Desired,
                amount1Desired: params.amount1Desired,
                Payer : msg.sender
            }),
            option
        );
            if (option == 102){
                revert("added liquidity");
            }
        bytes32 positionKey = PositionKey.compute(address(this), position.tickLower, position.tickUpper);

        // this is now updated to the current transaction
        (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) = pool.positions(positionKey);

        position.tokensOwed0 += uint128(
            FullMath.mulDiv(
                feeGrowthInside0LastX128 - position.feeGrowthInside0LastX128,
                position.liquidity,
                FixedPoint128.Q128
            )
        );
        position.tokensOwed1 += uint128(
            FullMath.mulDiv(
                feeGrowthInside1LastX128 - position.feeGrowthInside1LastX128,
                position.liquidity,
                FixedPoint128.Q128
            )
        );
        position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
        position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
        position.liquidity += liquidity;
    }
    // 
    function decreaseLiquidity(DecreaseLiquidityParams calldata params, int8 option)
        external
        payable
        override
        returns (uint256 amount0, uint256 amount1)
     {
            require(params.liquidity > 0, "L <= 0");
        Position_ storage position = _positions[params.tokenId];
        MPoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[position.poolId];
        uint128 positionLiquidity = position.liquidity;
            require(positionLiquidity >= params.liquidity, "pos. L < L");
        (IUniswapV3Pool pool, IUniswapV3PoolII poolII) = MPoolAddress.get_pools(factoryAddress,
                                                                            factoryIIAddress,
                                                                            poolKey.token0,
                                                                            poolKey.token1,
                                                                            poolKey.fee);
        if (option == 1){ revert("[MNPM II] 1"); }
        (amount0, amount1) = poolII.burnII(pool, position.tickLower, position.tickUpper, params.liquidity, option);
        if (option == 2){ revert("[MNPM II] 2"); }
            require(amount0 >= params.amount0Min && amount1 >= params.amount1Min, 'Price slippage check');
        bytes32 positionKey = PositionKey.compute(address(this), position.tickLower, position.tickUpper);
        (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) = pool.positions(positionKey);

        // adjust tokens owed 
            position.tokensOwed0 +=
                uint128(amount0) +
                uint128(
                    FullMath.mulDiv(
                        feeGrowthInside0LastX128 - position.feeGrowthInside0LastX128,
                        positionLiquidity,
                        FixedPoint128.Q128
                    )
                );
            position.tokensOwed1 +=
                uint128(amount1) +
                uint128(
                    FullMath.mulDiv(
                        feeGrowthInside1LastX128 - position.feeGrowthInside1LastX128,
                        positionLiquidity,
                        FixedPoint128.Q128
                    )
                );

        //
        position.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
        position.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
        // subtraction is safe because we checked positionLiquidity is gte params.liquidity
        position.liquidity = positionLiquidity - params.liquidity;

    }

    function cachePoolKey(address pool, MPoolAddress.PoolKey memory poolKey) private returns (uint80 poolId) {
        poolId = _poolIds[pool];
        if (poolId == 0) {
            _poolIds[pool] = (poolId = _nextPoolId++);
            _poolIdToPoolKey[poolId] = poolKey;
        }
    }

    function mapPoolKey(MintParams calldata params, 
                        uint256 tokenId,
                        uint128 liquidity,
                        int8 option,
                        IUniswapV3Pool pool)
        public override { 

        bytes32 positionKey = PositionKey.compute(address(this), params.tickLower, params.tickUpper);
        (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) = pool.positions(positionKey);

        // idempotent set
        uint80 poolId =
            cachePoolKey(
                address(pool),
                MPoolAddress.PoolKey({token0: params.token0, token1: params.token1, fee: params.fee})
            );

        if (option == 11){ revert("[NonfungII :: mapKey]  11");}
        _positions[tokenId] = Position_({
            nonce: 0,
            operator: address(0),
            poolId: poolId,
            tickLower: params.tickLower,
            tickUpper: params.tickUpper,
            liquidity: liquidity,
            feeGrowthInside0LastX128: feeGrowthInside0LastX128,
            feeGrowthInside1LastX128: feeGrowthInside1LastX128,
            tokensOwed0: 0,
            tokensOwed1: 0
        });
        if (option == 12){ revert("[NonfungII :: mapKey] 12");}

        

    }

    function collect(CollectParams calldata params, int8 option)
        external
        payable
        override
        returns (uint256 amount0, uint256 amount1)
     {
        require(params.amount0Max > 0 || params.amount1Max > 0, "amnt <= 0");
        // allow collecting to the nft position manager address with address 0
        address recipient = params.recipient == address(0) ? address(this) : params.recipient;
        
        Position_ storage NPMposition = _positions[params.tokenId];
        MPoolAddress.PoolKey memory poolKey = _poolIdToPoolKey[NPMposition.poolId];
        (IUniswapV3Pool pool, IUniswapV3PoolII poolII) = MPoolAddress.get_pools(
                                                                            factoryAddress,
                                                                            factoryIIAddress,
                                                                            poolKey.token0,
                                                                            poolKey.token1,
                                                                            poolKey.fee);  
        //IUniswapV3Pool pool = IUniswapV3Pool(PoolAddress.computeAddress(factory, poolKey));
        (uint128 tokensOwed0, uint128 tokensOwed1) = (NPMposition.tokensOwed0, NPMposition.tokensOwed1);

        // trigger an update of the position fees owed and fee growth snapshots if it has any liquidity
        if (NPMposition.liquidity > 0) {
            poolII.burnII(pool, NPMposition.tickLower, NPMposition.tickUpper, 0, option);
            (, uint256 feeGrowthInside0LastX128, uint256 feeGrowthInside1LastX128, , ) =
                pool.positions(PositionKey.compute(address(this), NPMposition.tickLower, NPMposition.tickUpper));
            if (option == 1){ revert("[NMPII::collect] 1"); }
            tokensOwed0 += uint128(
                FullMath.mulDiv(
                    feeGrowthInside0LastX128 - NPMposition.feeGrowthInside0LastX128,
                    NPMposition.liquidity,
                    FixedPoint128.Q128
                )
            );
            tokensOwed1 += uint128(
                FullMath.mulDiv(
                    feeGrowthInside1LastX128 - NPMposition.feeGrowthInside1LastX128,
                    NPMposition.liquidity,
                    FixedPoint128.Q128
                )
            );

            NPMposition.feeGrowthInside0LastX128 = feeGrowthInside0LastX128;
            NPMposition.feeGrowthInside1LastX128 = feeGrowthInside1LastX128;
        }
 
        // compute the arguments to give to the pool#collect method
        (uint128 amount0Collect, uint128 amount1Collect) =
            (
                params.amount0Max > tokensOwed0 ? tokensOwed0 : params.amount0Max,
                params.amount1Max > tokensOwed1 ? tokensOwed1 : params.amount1Max
            );

        // the actual amounts collected are returned
        if (option == 2){ revert("[NMP::collect] 2"); }
        (amount0, amount1) = poolII.collectII(
            pool,
            recipient,
            NPMposition.tickLower,
            NPMposition.tickUpper,
            amount0Collect,
            amount1Collect
        );

        if (option == 3){  revert("[NPMII::collect] 3");  }

        // sometimes there will be a few less wei than expected due to rounding down in core, but we just subtract the full amount expected
        // instead of the actual amount so we can burn the token
        (NPMposition.tokensOwed0, NPMposition.tokensOwed1) = (tokensOwed0 - amount0Collect, tokensOwed1 - amount1Collect);
    }

    function _getAndIncrementNonceII(uint256 tokenId) external override returns (uint256) {
        return uint256(_positions[tokenId].nonce++);
    }

    function deletePosition(uint256 tokenId) external override {
        delete _positions[tokenId];
    }
}