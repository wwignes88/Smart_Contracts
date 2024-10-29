// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.7.5;
pragma abicoder v2;

import '@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3SwapCallback.sol';

/// @title Router token swapping functionality
/// @notice Functions for swapping tokens via Uniswap V3
interface IMSwapRouter is IUniswapV3SwapCallback {
    struct ExactInputParams {
        bytes path;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        int8    option;
    }
    struct ExactOutputParams {
        bytes path;
        address recipient;
        uint256 deadline;
        uint256 amountOut;
        uint256 amountInMaximum;
        int8    option;
    }

    function exactInput(ExactInputParams calldata params) external payable returns (uint256 amountOut);
    function exactOutput(ExactOutputParams calldata params) external payable returns (uint256 amountIn);

    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24  fee;
        address recipient;
        uint256 deadline;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
        int8    option;
    }
    struct ExactOutputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 deadline;
        uint256 amountOut;
        uint256 amountInMaximum;
        uint160 sqrtPriceLimitX96;
        int8    option;
    }

    function exactOutputSingle(ExactOutputSingleParams calldata params, int8 option) external payable returns (uint256 amountIn);
    function exactInputSingle(ExactInputSingleParams calldata params, int8 option) external payable returns (uint256 amountOut);

    event paidInexact(address tokenIn, 
                        address payer, 
                        address recipient, 
                        uint256 amount);
    event paidExact(address tokenIn, 
                    address payer, 
                    address recipient, 
                    uint256 amount);

    event SwapCallback( address tokenIn,
                        address tokenOut,
                        uint256 amountToPay,
                        bool isExactInput,
                        address sender);  
    event exactInInternal(  address tokenIn,
                            address tokenOut,
                            bool zeroForOne);
    event exactOutInternal(  address tokenIn,
                            address tokenOut,
                            bool zeroForOne);
}


