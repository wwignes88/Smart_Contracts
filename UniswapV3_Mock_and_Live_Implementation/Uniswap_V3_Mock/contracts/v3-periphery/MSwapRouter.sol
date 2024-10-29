// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;
pragma abicoder v2;

import '@uniswap/v3-core/contracts/libraries/SafeCast.sol';
import '@uniswap/v3-core/contracts/libraries/TickMath.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';
import '@v3PeripheryMOCKS/interfaces/IMSwapRouter.sol'; 
import './libraries/MPoolAddress.sol';
import './libraries/MCallbackValidation.sol';

import '@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol';
import '@uniswap/v3-periphery/contracts/base/PeripheryValidation.sol';
import '@uniswap/v3-periphery/contracts/base/PeripheryPaymentsWithFee.sol';
    //  PeripheryPayments
        // '../libraries/TransferHelper.sol';
import '@uniswap/v3-periphery/contracts/base/Multicall.sol';
import '@uniswap/v3-periphery/contracts/base/SelfPermit.sol';
import '@uniswap/v3-periphery/contracts/libraries/Path.sol';

import '@openzeppelin/contracts/token/ERC20/IERC20.sol';
import '@uniswap/v3-periphery/contracts/interfaces/external/IWETH9.sol';


/// @title Uniswap V3 Swap Router
/// @notice Router for stateless execution of swaps against Uniswap V3
contract MSwapRouter is
    IMSwapRouter,
    PeripheryImmutableState,
    PeripheryValidation,
    PeripheryPaymentsWithFee,
    Multicall,
    SelfPermit
{
    // VARIABLES
        using Path for bytes;
        using SafeCast for uint256;

        /// @dev Used as the placeholder value for amountInCached, because the computed amount in for an exact output swap
        /// can never actually be this value
        uint256 private constant DEFAULT_AMOUNT_IN_CACHED = type(uint256).max;

        /// @dev Transient storage variable used for returning the computed amount in for an exact output swap.
        uint256 public amountInCached = DEFAULT_AMOUNT_IN_CACHED;
        function getAmountInCache() external view returns (uint256 amountInCached_){
            amountInCached_ = amountInCached;
        }

        constructor(address _factory, address _WETH9) PeripheryImmutableState(_factory, _WETH9) {}

        /// @dev Returns the pool for the given token pair and fee. The pool contract may or may not exist.
        function getPool(
                address tokenA,
                address tokenB,
                uint24 fee
            ) public view returns (IUniswapV3Pool) {
                return IUniswapV3Pool(MPoolAddress.computePoolAddress(factory, tokenA, tokenB, fee));
        }

        function revertOption(bool firstPool, int8 option, uint8 trigger, string memory locationString) public {
            // Convert option to uint8 and store the result
            uint8 absOption = uint8(option);

            // Construct the full message string
            if (absOption == trigger){
                string memory message;
                if (firstPool) {
                    message = "[1]: ";
                } else {
                    message = "[2]: ";
                }
                // Append the dynamic part of the message
                message = string(abi.encodePacked(message, locationString));

                // Use the constructed message in the revert()
                if (option > 0 && firstPool){
                    revert(message);
                }
                if (option < 0 && firstPool==false){
                    revert(message);
                }
            }

        }

        /// @inheritdoc IUniswapV3SwapCallback
        function uniswapV3SwapCallback(
            int256 amount0Delta,
            int256 amount1Delta,
            bytes calldata _data
         ) external override {


            SwapCallbackData memory data = abi.decode(_data, (SwapCallbackData));
            if (data.Ropt <= 19){
                require(amount0Delta > 0 || amount1Delta > 0, "delta"); // swaps entirely within 0-liquidity regions are not supported
            }
            int8 option = data.Ropt;
            (address tokenIn, address tokenOut, uint24 fee) = data.path.decodeFirstPool();
            
            MCallbackValidation.verifyCallback(factory, tokenIn, tokenOut, fee);
            

            revertOption( data.multiPools, data.Ropt, 10, "[router :: uniCallback] 10 ");

            (bool isExactInput, uint256 amountToPay) =
                amount0Delta > 0
                    ? (tokenIn < tokenOut, uint256(amount0Delta))
                    : (tokenOut < tokenIn, uint256(amount1Delta));
            emit SwapCallback(tokenIn, tokenOut, amountToPay, isExactInput, msg.sender);
            
            if (isExactInput) {
                revertOption( data.multiPools, data.Ropt, 11, "[router :: uniCallback] 11A ");
                if (data.Ropt <= 19){
                    pay(tokenIn, data.payer, msg.sender, amountToPay);
                }
                emit paidInexact(tokenIn, data.payer, msg.sender, amountToPay);
            } else {
                // either initiate the next swap or pay
                if (data.path.hasMultiplePools()) {
                    data.path = data.path.skipToken();
                    data.multiPools = false;
                    revertOption( false, data.Ropt, 11, "[router :: uniCallback] 11B ");
                    exactOutputInternal(amountToPay, msg.sender, 0, data);
                } else {
                    amountInCached = amountToPay;
                    tokenIn = tokenOut; // swap in/out because exact output swaps are reversed
                    revertOption( data.multiPools, data.Ropt, 11, "[router :: uniCallback] 11C ");
                    if (data.Ropt <= 19){
                        pay(tokenIn, data.payer, msg.sender, amountToPay);
                    }
                    emit paidExact(tokenIn, data.payer, msg.sender, amountToPay);
                }
            } 
         }

//======================== INPUT SWAPS =====================

    struct SwapCallbackData {
        bytes path;
        address payer;
        int8 Ropt;
        bool exactInput;
        bool multiPools;
    }

    function exactInput(ExactInputParams memory params)
        external
        payable
        override
        checkDeadline(params.deadline)
        returns (uint256 amountOut)
     {
        address payer = msg.sender; // msg.sender pays for the first hop

        while (true) {
                bool hasMultiplePools = params.path.hasMultiplePools();
                
                // the outputs of prior swaps become the inputs to subsequent ones
                params.amountIn = exactInputInternal(
                    params.amountIn,
                    hasMultiplePools ? address(this) : params.recipient, // for intermediate swaps, this contract custodies
                    0,
                    SwapCallbackData({
                        path : params.path, // only the first pool in the path is necessary
                        payer: payer, // msg.sender
                        Ropt : params.option,
                        exactInput: params.amountIn > 0,
                        multiPools: hasMultiplePools
                    })
                );

                    // decide whether to continue or terminate
                    if (hasMultiplePools) {
                        payer = address(this);
                        params.path = params.path.skipToken();
                    } else {
                        amountOut = params.amountIn;
                        break;
                    }
            }

            if (params.option <= 19    ){
                require(amountOut >= params.amountOutMinimum, 'Too little received');
            }
    }

    function exactInputInternal(
        uint256 amountIn,         
        address recipient,           
        uint160 sqrtPriceLimitX96,   
        SwapCallbackData memory data 
     ) private returns (uint256 amountOut) {

        //if (data.Ropt == 4 && data.firstPool  ){revert("[router :: exactInputInternal] 4");}
        //if (data.Ropt == 104 ){revert("[router :: exactInputInternal] 104");}
        revertOption( data.multiPools, data.Ropt, 4, "[router :: exactInInternal] 4 ");

        if (recipient == address(0)) recipient = address(this);
        (address tokenIn, address tokenOut, uint24 fee) = data.path.decodeFirstPool();
        bool zeroForOne = tokenIn < tokenOut;
        
        (int256 amount0, int256 amount1) =
            getPool(tokenIn, tokenOut, fee).swap(
                recipient,
                zeroForOne,
                amountIn.toInt256(),
                sqrtPriceLimitX96 == 0
                    ? (zeroForOne ? TickMath.MIN_SQRT_RATIO + 1 : TickMath.MAX_SQRT_RATIO - 1)
                    : sqrtPriceLimitX96,
                abi.encode(data)
            );
        
        emit exactInInternal(tokenIn, tokenOut,  zeroForOne); 
        return uint256(-(zeroForOne ? amount1 : amount0));
    }

    function exactInputSingle(ExactInputSingleParams calldata params, int8 option)
        external
        payable
        override
        checkDeadline(params.deadline)
        returns (uint256 amountOut)
     {

        amountOut = exactInputInternal(
            params.amountIn,
            params.recipient,
            params.sqrtPriceLimitX96,
            SwapCallbackData({path: abi.encodePacked(params.tokenIn, params.fee, params.tokenOut), 
                            payer: msg.sender, 
                            Ropt: option,
                            exactInput: params.amountIn > 0,
                            multiPools: false}));
        if (option <= 19  ){
            require(amountOut >= params.amountOutMinimum, 'Too little received');
        }
    }

//=============================== OUTPUT SWAPS ==========================


    /// @dev Performs a single exact output swap
    //exactOutputInternal(amountToPay, msg.sender, 0, data);
    function exactOutputInternal(
        uint256 amountOut,
        address recipient,
        uint160 sqrtPriceLimitX96,
        SwapCallbackData memory data
     ) private returns (uint256 amountIn) {

        revertOption( data.multiPools, data.Ropt, 4, "[router :: exactOutInternal] 4 ");
        
        // allow swapping to the router address with address 0
        if (recipient == address(0)) recipient = address(this);
        (address tokenOut, address tokenIn, uint24 fee) = data.path.decodeFirstPool();
        bool zeroForOne = tokenIn < tokenOut;
        emit exactOutInternal(tokenIn, tokenOut, zeroForOne);

        ( int256 amount0Delta, int256 amount1Delta ) =
            getPool(tokenIn, tokenOut, fee).swap(
                recipient,
                zeroForOne,
                -amountOut.toInt256(),
                sqrtPriceLimitX96 == 0
                    ? (zeroForOne ? TickMath.MIN_SQRT_RATIO + 1 : TickMath.MAX_SQRT_RATIO - 1)
                    : sqrtPriceLimitX96,
                abi.encode(data)
            );
            bool hasMultiplePools = data.path.hasMultiplePools();

        uint256 amountOutReceived;
        (amountIn, amountOutReceived) = zeroForOne
            ? (uint256(amount0Delta), uint256(-amount1Delta))
            : (uint256(amount1Delta), uint256(-amount0Delta));
        // it's technically possible to not receive the full output amount,
        // so if no price limit has been specified, require this possibility away
        if (data.Ropt <= 19  ){
            if (sqrtPriceLimitX96 == 0) require(amountOutReceived == amountOut);
        }

    }

    // see IMSwapRouter
    function exactOutput(ExactOutputParams calldata params)
        external
        payable
        override
        checkDeadline(params.deadline)
        returns (uint256 amountIn)
     {

        // it's okay that the payer is fixed to msg.sender here, as they're only paying for the "final" exact output
        // swap, which happens first, and subsequent swaps are paid for within nested callback frames
        exactOutputInternal(
            params.amountOut,
            params.recipient,
            0,
            SwapCallbackData({path: params.path, 
                                payer: msg.sender, 
                                Ropt: params.option, 
                                exactInput: false,
                                multiPools: params.path.hasMultiplePools()})
        );

        amountIn = amountInCached;
        if (params.option <= 19  ){
            require(amountIn <= params.amountInMaximum, 'Too much requested');
        }
        amountInCached = DEFAULT_AMOUNT_IN_CACHED;
    }

    // *NOTE: exactInput: params.amount < 0 because 
    //  A) exactInput has here been incorporated into swapCallback data
    //  B) exactOutputInternal [above] puts a negative sign on amount
    function exactOutputSingle(ExactOutputSingleParams calldata params, int8 option)
        external
        payable
        override
        checkDeadline(params.deadline)
        returns (uint256 amountIn)
     {

        // avoid an SLOAD by using the swap return data
        // exactOutputInternal(amountToPay, msg.sender, 0, data);
        amountIn = exactOutputInternal(
            params.amountOut,
            params.recipient,
            params.sqrtPriceLimitX96,
            SwapCallbackData({path: abi.encodePacked(params.tokenOut, params.fee, params.tokenIn), 
                            payer: msg.sender, 
                            Ropt: option,
                            exactInput: false,
                            multiPools: false})
        );
        if (option <= 19 ){
            require(amountIn <= params.amountInMaximum, 'Too much requested');
        }

        amountInCached = DEFAULT_AMOUNT_IN_CACHED;
    }
    }