// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.5.0;
pragma abicoder v2;

import '@uniswap/v3-core/contracts/interfaces/pool/IUniswapV3PoolImmutables.sol';
import '@uniswap/v3-core/contracts/interfaces/pool/IUniswapV3PoolState.sol';
import '@uniswap/v3-core/contracts/interfaces/pool/IUniswapV3PoolDerivedState.sol';
// not used:
    // import '@uniswap/v3-core/contracts/interfaces/pool/IUniswapV3PoolActions.sol';
import '@uniswap/v3-core/contracts/interfaces/pool/IUniswapV3PoolOwnerActions.sol';
import '@uniswap/v3-core/contracts/interfaces/pool/IUniswapV3PoolEvents.sol';
import '@uniswap/v3-core/contracts/libraries/Position.sol';

/// @title The interface for a Uniswap V3 Pool
/// @notice A Uniswap pool facilitates swapping and automated market making between any two assets that strictly conform
/// to the ERC20 specification
/// @dev The pool interface is broken up into many smaller pieces
interface IUniswapV3Pool is
    IUniswapV3PoolImmutables,
    IUniswapV3PoolState,
    IUniswapV3PoolDerivedState,
    IUniswapV3PoolEvents
{

    struct Info {
        // the amount of liquidity owned by this position
        uint128 liquidity;
        // fee growth per unit of liquidity as of the last update to liquidity or fees owed
        uint256 feeGrowthInside0LastX128;
        uint256 feeGrowthInside1LastX128;
        // the fees owed to the position owner in token0/token1
        uint128 tokensOwed0;
        uint128 tokensOwed1;
    }

    function _modifyPosition(address owner, 
                            int24 tickLower, 
                            int24 tickUpper, 
                            int128 liquidityDelta, 
                            int8 modify_option)
        external
        returns (
            Position.Info memory position,
            int256 amount0,
            int256 amount1
    );

    function initialize(uint160 sqrtPriceX96) external;

    function swap(
        address recipient,
        bool zeroForOne,
        int256 amountSpecified,
        uint160 sqrtPriceLimitX96,
        bytes calldata data
    ) external returns (int256 amount0, int256 amount1);

    function increaseObservationCardinalityNext(uint16 observationCardinalityNext) external;

    // option 50
    event SwapAmounts(
        bool firstPool,
        address indexed sender,
        address recipient,
        bool zeroForOne,
        int256 amount0,
        int256 amount1
    );
    // option 51
    event SteppedAmounts(
        int24 indexed tickNext,
        int256 amountSpecifiedRemaining,
        int256 amountCalculated
    );
    // option 52
    event SteppedPrices(
        int24 indexed tickNext,
        uint160 sqrtPriceX96,
        uint256 sqrtPriceNextX96,
        uint256 sqrtPriceTargetX96
    );
    // option 53
    event SwapStepAmounts(
        int24 indexed tickNext,
        uint256 amountIn,
        uint256 amountOut,
        uint256 feeAmount
    );
    // option 53
    event modifyAmounts(
        int128 liquidityDelta,
        int256 amount0,
        int256 amount1
    );
    
    function poolII_transfer(bool zeroOrOne, address recipient, uint256 amount) external;

    function modifyTokensOwed(
        address owner,
        int24 tickLower,
        int24 tickUpper,
        uint128 _tokensOwed0,
        uint128 _tokensOwed1
    ) external;

    function getPoolPosition(
        address owner,
        int24 tickLower,
        int24 tickUpper
    ) external view returns(Position.Info memory position);

    function setFeeProtocol(uint8 feeProtocol0, uint8 feeProtocol1) external;

    function collectProtocol(
        address recipient,
        uint128 amount0Requested,
        uint128 amount1Requested
    ) external returns (uint128 amount0, uint128 amount1);
}


