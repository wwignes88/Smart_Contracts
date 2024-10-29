// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;
pragma abicoder v2;

import '@uniswap/v3-periphery/contracts/libraries/TransferHelper.sol';
import '@v3PeripheryMOCKS/libraries/MTransferHelper.sol';
import '@v3PeripheryMOCKS/interfaces/IMSwapRouter.sol';
import '@uniswap/v3-periphery/contracts/libraries/Path.sol';


contract MSwapper {
    using Path for bytes;
    IMSwapRouter public immutable swapRouter;
    uint24 public poolFee;
    constructor(uint24  _fee,
                IMSwapRouter _swapRouter) {
                    poolFee = _fee;
                    swapRouter = _swapRouter;
    }

    function MultiHop_Input(uint256 amountIn,
                            uint256 amountOutMin,
                            address tokenA,
                            address tokenB,
                            address tokenC,
                            int8 option
                            ) external returns (uint256 amountOut) {

        // Transfer `amountIn` of tokenA to this contract.
        MTransferHelper.safeTransferFrom(tokenA, msg.sender, address(this), amountIn);
        if (option == 1){ revert("[Swapper :: MultiHop_Input] exasafeTransfered");}

        // Approve the router to spend tokenA.
        MTransferHelper.safeApprove(tokenA, address(swapRouter), amountIn);
        if (option == 2){ revert("[Swapper :: MultiHop_Input] safeApproved");}

        bytes memory PATH = abi.encodePacked(tokenA, poolFee, tokenB, poolFee, tokenC);
        
        IMSwapRouter.ExactInputParams memory params =
            IMSwapRouter.ExactInputParams({
                path: PATH,
                recipient: msg.sender,
                deadline: block.timestamp,
                amountIn: amountIn,
                amountOutMinimum: amountOutMin,
                option: option
            });
                // Executes the swap.
        amountOut = swapRouter.exactInput(params);
    }


    function MultiHop_Output(uint256 amountOut,
                            uint256 amountInMax,
                            uint256 payAmount,
                            address tokenA,
                            address tokenB,
                            address tokenC,
                            address transferToken,
                            int8 option
                            ) external returns (uint256 amountIn) {
        
        if (option <= 19) {
            // Transfer `amountIn` of tokenA to this contract.
            MTransferHelper.safeTransferFrom(transferToken, msg.sender, address(this), payAmount);
            if (option == 1){ revert("[Swapper :: MultiHop_Output] safeTransfered");}

            // Approve the router to spend tokenA.
            MTransferHelper.safeApprove(transferToken, address(swapRouter), payAmount);
            if (option == 2){ revert("[Swapper :: MultiHop_Output] safeApproved"); }
        }

        bytes memory PATH = abi.encodePacked(tokenC, poolFee, tokenB, poolFee, tokenA);
        
        IMSwapRouter.ExactOutputParams memory params =
            IMSwapRouter.ExactOutputParams({
                path: PATH,
                recipient: msg.sender, 
                deadline: block.timestamp,
                amountOut: amountOut,
                amountInMaximum: amountInMax,
                option: option
            });
                // Executes the swap.
        amountIn = swapRouter.exactOutput(params);
    }

    



}