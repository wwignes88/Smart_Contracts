// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.7.5;
pragma abicoder v2;

import '@v3PeripheryMOCKS/interfaces/IStructs.sol'; 
import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';
/// @title Non-fungible token for positions
/// @notice Wraps Uniswap V3 positions in a non-fungible token interface which allows for them to be transferred
/// and authorized.
interface IMNonfungiblePositionManagerII is IStructs{

    //
    function positions(uint256 tokenId)
        external
        view
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
        );
    // 
    struct CollectParams {
        uint256 tokenId;
        address recipient;
        uint128 amount0Max;
        uint128 amount1Max;
        }

    function ERC721Manager_Add_Liquidity(
        AddLiquidityParams memory params,  
        int8 option) 
    external             
        returns (
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1,
            IUniswapV3Pool pool
        );

    function collect(CollectParams calldata params, int8 revert_option) external payable returns (uint256 amount0, uint256 amount1);
    //
    function mapPoolKey(MintParams calldata params, 
                        uint256 tokenId,
                        uint128 liquidity,
                        int8 option,
                        IUniswapV3Pool pool)
        external;
    //
    struct IncreaseLiquidityParams {
        uint256 tokenId;
        uint256 amount0Desired;
        uint256 amount1Desired;
        uint256 amount0Min;
        uint256 amount1Min;
        uint256 deadline;
        }

    function increaseLiquidity(IncreaseLiquidityParams calldata params, int8 revert_option)
        external
        payable
        returns (
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1
        );
    //
    struct DecreaseLiquidityParams {
        uint256 tokenId;
        uint128 liquidity;
        uint256 amount0Min;
        uint256 amount1Min;
        uint256 deadline;
        }
    function decreaseLiquidity(DecreaseLiquidityParams calldata params, int8 revert_option)
        external
        payable
        returns (uint256 amount0, uint256 amount1);
    //
    function _getAndIncrementNonceII(uint256 tokenId) external  returns (uint256) ;
    function deletePosition(uint256 tokenId) external;
}