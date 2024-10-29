// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;
 


// my mock contracts
import '@v3PeripheryMOCKS/libraries/MPoolAddress.sol';
import '@v3PeripheryMOCKS/base/MPeripheryPayments.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3PoolII.sol';
import '@v3PeripheryMOCKS/libraries/MCallbackValidation.sol';
import '@v3PeripheryMOCKS/interfaces/IStructs.sol'; 

import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol';
import '@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3MintCallback.sol';
import '@uniswap/v3-core/contracts/libraries/TickMath.sol';


import '@uniswap/v3-periphery/contracts/libraries/LiquidityAmounts.sol';
//import '@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol'; 

/// @title Liquidity management functions
/// @notice Internal functions for safely managing liquidity in Uniswap V3
abstract contract MLiquidityManager is 
    IUniswapV3MintCallback, 
    MPeripheryPayments,
    IStructs{

    address public immutable  factoryAddress;
    address public immutable  factoryIIAddress;
    address  Weth9;

    constructor(
        address _factory, 
        address _factoryII, 
        address _WETH9) MPeripheryPayments(_WETH9){
        factoryAddress   = _factory;
        factoryIIAddress = _factoryII;
    }


    struct MintCallbackData {
        MPoolAddress.PoolKey poolKey;
        address payer;
        int8 Option;
    }


    event MintPayAmounts(
        address Payer,
        address indexed token0,
        address indexed token1,
        uint256 amount0,
        uint256 amount1
    );

    /// @inheritdoc IUniswapV3MintCallback
    function uniswapV3MintCallback(
        uint256 amount0Owed,
        uint256 amount1Owed,
        bytes calldata data
    ) external override {
        // data =  abi.encode(MintCallbackData({poolKey: poolKey, payer: msg.sender, DataOption: option}))
        MintCallbackData memory decoded = abi.decode(data, (MintCallbackData));
        (IUniswapV3Pool pool, IUniswapV3PoolII poolII) = 
                MPoolAddress.get_pools(factoryAddress,
                                        factoryIIAddress,
                                        decoded.poolKey.token0,
                                        decoded.poolKey.token1,
                                        decoded.poolKey.fee);

        int8 option = decoded.Option;
        if (option == 8){revert(" verifying callback [not implemented] 8");}  

        // payer [nonfung]  // receiver [pool]
        if (amount0Owed > 0) pay(decoded.poolKey.token0, decoded.payer, address(pool), amount0Owed, option);

        // payer [nonfung]  // receiver [pool]
        if (amount1Owed > 0) pay(decoded.poolKey.token1, decoded.payer, address(pool), amount1Owed, option);
        if (option == 9){ revert("  paid  9 ") ;}

        emit MintPayAmounts(decoded.payer, decoded.poolKey.token0, decoded.poolKey.token1, amount0Owed, amount1Owed);
    }




    /// @notice Add liquidity to an initialized pool
    function addLiquidity(AddLiquidityParams memory params,  int8 option)
        internal
        returns (
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1,
            IUniswapV3Pool pool
        )
    {
        IUniswapV3PoolII poolII;
        (pool,  poolII) = MPoolAddress.get_pools(factoryAddress,
                                        factoryIIAddress,
                                        params.token0,
                                        params.token1,
                                        params.fee);

        // compute the liquidity amount
        {
            (uint160 sqrtPriceX96, , , , , , ) = pool.slot0();
            uint160 sqrtRatioAX96 = TickMath.getSqrtRatioAtTick(params.tickLower);
            uint160 sqrtRatioBX96 = TickMath.getSqrtRatioAtTick(params.tickUpper);

            liquidity = LiquidityAmounts.getLiquidityForAmounts(
                sqrtPriceX96,
                sqrtRatioAX96,
                sqrtRatioBX96,
                params.amount0Desired,
                params.amount1Desired
            );
        }
        MPoolAddress.PoolKey memory poolKey =
            MPoolAddress.PoolKey({token0: params.token0, token1: params.token1, fee: params.fee});
        if (option == 5){revert("LManager :: minting to pool...");}

        //*Note: payer is msg.sender according to NPM contract. NPM then calls NPMII with this sender=params.Payer.
        bytes memory data = abi.encode(MintCallbackData({poolKey: poolKey, payer: params.Payer, Option: option}));
        // see MUniswapV3PoolII.sol for mintII function
        (amount0, amount1) = poolII.mintII(
            pool,
            params.recipient,
            params.tickLower,
            params.tickUpper,
            liquidity,
            data,
            option
        );
                                                            //^^ msg.sendder [payer] is nonfungiblePositionManager

        
    }



}