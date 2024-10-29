// SPDX-License-Identifier: BUSL-1.1
pragma solidity 0.7.6; 
pragma abicoder v2;

// *flash deleted from IUniswapV3Pool and this contract to reduce size
// my contracts
import '@v3CoreMOCKS/MNoDelegateCall.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';

import '@uniswap/v3-core/contracts/libraries/LowGasSafeMath.sol';
import '@uniswap/v3-core/contracts/libraries/SafeCast.sol';
import '@uniswap/v3-core/contracts/libraries/Tick.sol';
import '@uniswap/v3-core/contracts/libraries/TickBitmap.sol';
import '@uniswap/v3-core/contracts/libraries/Position.sol';
import '@uniswap/v3-core/contracts/libraries/Oracle.sol';

import '@uniswap/v3-core/contracts/libraries/FullMath.sol';
import '@uniswap/v3-core/contracts/libraries/FixedPoint128.sol';
import '@uniswap/v3-core/contracts/libraries/TransferHelper.sol';
import '@uniswap/v3-core/contracts/libraries/TickMath.sol';
import '@uniswap/v3-core/contracts/libraries/LiquidityMath.sol';
import '@uniswap/v3-core/contracts/libraries/SqrtPriceMath.sol';
import '@uniswap/v3-core/contracts/libraries/SwapMath.sol';

//import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol';
import '@uniswap/v3-core/contracts/interfaces/IUniswapV3PoolDeployer.sol';
import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol';
import '@uniswap/v3-core/contracts/interfaces/IERC20Minimal.sol';
import '@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3SwapCallback.sol';
import '@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3FlashCallback.sol';

contract MUniswapV3Pool is IUniswapV3Pool, MNoDelegateCall {
    // variables
        using LowGasSafeMath for uint256;
        using LowGasSafeMath for int256;
        using SafeCast for uint256;
        using SafeCast for int256;
        using Tick for mapping(int24 => Tick.Info);
        using TickBitmap for mapping(int16 => uint256);
        using Position for mapping(bytes32 => Position.Info);
        using Position for Position.Info;
        using Oracle for Oracle.Observation[65535];

        /// @inheritdoc IUniswapV3PoolImmutables
        address public immutable override factory;
        /// @inheritdoc IUniswapV3PoolImmutables
        address public immutable override token0;
        /// @inheritdoc IUniswapV3PoolImmutables
        address public immutable override token1;
        /// @inheritdoc IUniswapV3PoolImmutables
        uint24 public immutable override fee;

        /// @inheritdoc IUniswapV3PoolImmutables
        int24 public immutable override tickSpacing;

        /// @inheritdoc IUniswapV3PoolImmutables
        uint128 public immutable override maxLiquidityPerTick;

        struct Slot0 {
            // the current price
            uint160 sqrtPriceX96;
            // the current tick
            int24 tick;
            // the most-recently updated index of the observations array
            uint16 observationIndex;
            // the current maximum number of observations that are being stored
            uint16 observationCardinality;
            // the next maximum number of observations to store, triggered in observations.write
            uint16 observationCardinalityNext;
            // the current protocol fee as a percentage of the swap fee taken on withdrawal
            // represented as an integer denominator (1/x)%
            uint8 feeProtocol;
            // whether the pool is locked
            bool unlocked;
        }
        /// @inheritdoc IUniswapV3PoolState
        Slot0 public override slot0;

        /// @inheritdoc IUniswapV3PoolState
        uint256 public override feeGrowthGlobal0X128;
        /// @inheritdoc IUniswapV3PoolState
        uint256 public override feeGrowthGlobal1X128;

        // accumulated protocol fees in token0/token1 units
        struct ProtocolFees {
            uint128 token0;
            uint128 token1;
        } 
        /// @inheritdoc IUniswapV3PoolState
        ProtocolFees public override protocolFees; 
        /// @inheritdoc IUniswapV3PoolState
        uint128 public override liquidity;
        /// @inheritdoc IUniswapV3PoolState
        mapping(int24 => Tick.Info) public override ticks;
        /// @inheritdoc IUniswapV3PoolState
        mapping(int16 => uint256) public override tickBitmap;
        /// @inheritdoc IUniswapV3PoolState
        mapping(bytes32 => Position.Info) public override positions;
        /// @inheritdoc IUniswapV3PoolState
        Oracle.Observation[65535] public override observations;

        /// @dev Mutually exclusive reentrancy protection into the pool to/from a method. This method also prevents entrance
        /// to a function before the pool is initialized. The reentrancy guard is required throughout the contract because
        /// we use balance checks to determine the payment status of interactions such as mint, swap and flash.
    //
    modifier lock() {
        require(slot0.unlocked, 'LOK');
        slot0.unlocked = false;
        _;
        slot0.unlocked = true;
    }

    /// @dev Prevents calling a function from anyone except the address returned by IUniswapV3Factory#owner()
    modifier onlyFactoryOwner() {
        require(msg.sender == IUniswapV3Factory(factory).owner());
        _;
    }

    constructor() {
        int24 _tickSpacing;
        (factory, token0, token1, fee, _tickSpacing) = IUniswapV3PoolDeployer(msg.sender).parameters();
        tickSpacing = _tickSpacing;

        maxLiquidityPerTick = Tick.tickSpacingToMaxLiquidityPerTick(_tickSpacing);
    }

    /// @dev Common checks for valid tick inputs.
    function checkTicks(int24 tickLower, int24 tickUpper) private pure {
        require(tickLower < tickUpper, 'TLU');
        require(tickLower >= TickMath.MIN_TICK, 'TLM');
        require(tickUpper <= TickMath.MAX_TICK, 'TUM');
    }

    /// @dev Returns the block timestamp truncated to 32 bits, i.e. mod 2**32. This method is overridden in tests.
    function _blockTimestamp() internal view virtual returns (uint32) {
        return uint32(block.timestamp); // truncation is desired
    }


    /// @dev Get the pool's balance of token0
    /// @dev This function is gas optimized to avoid a redundant extcodesize check in addition to the returndatasize
    /// check
    function balance0() private view returns (uint256) {
        (bool success, bytes memory data) =
            token0.staticcall(abi.encodeWithSelector(IERC20Minimal.balanceOf.selector, address(this)));
        require(success && data.length >= 32);
        return abi.decode(data, (uint256));
    }

    /// @dev Get the pool's balance of token1
    /// @dev This function is gas optimized to avoid a redundant extcodesize check in addition to the returndatasize
    /// check
    function balance1() private view returns (uint256) {
        (bool success, bytes memory data) =
            token1.staticcall(abi.encodeWithSelector(IERC20Minimal.balanceOf.selector, address(this)));
        require(success && data.length >= 32);
        return abi.decode(data, (uint256));
    }

    /// @inheritdoc IUniswapV3PoolDerivedState
    function snapshotCumulativesInside(int24 tickLower, int24 tickUpper)
        external
        view
        override
        noDelegateCall
        returns (
            int56 tickCumulativeInside,
            uint160 secondsPerLiquidityInsideX128,
            uint32 secondsInside
        )
    {
        checkTicks(tickLower, tickUpper);

        int56 tickCumulativeLower;
        int56 tickCumulativeUpper;
        uint160 secondsPerLiquidityOutsideLowerX128;
        uint160 secondsPerLiquidityOutsideUpperX128;
        uint32 secondsOutsideLower;
        uint32 secondsOutsideUpper;

        {
            Tick.Info storage lower = ticks[tickLower];
            Tick.Info storage upper = ticks[tickUpper];
            bool initializedLower;
            (tickCumulativeLower, secondsPerLiquidityOutsideLowerX128, secondsOutsideLower, initializedLower) = (
                lower.tickCumulativeOutside,
                lower.secondsPerLiquidityOutsideX128,
                lower.secondsOutside,
                lower.initialized
            );
            require(initializedLower);

            bool initializedUpper;
            (tickCumulativeUpper, secondsPerLiquidityOutsideUpperX128, secondsOutsideUpper, initializedUpper) = (
                upper.tickCumulativeOutside,
                upper.secondsPerLiquidityOutsideX128,
                upper.secondsOutside,
                upper.initialized
            );
            require(initializedUpper);
        }

        Slot0 memory _slot0 = slot0;

        if (_slot0.tick < tickLower) {
            return (
                tickCumulativeLower - tickCumulativeUpper,
                secondsPerLiquidityOutsideLowerX128 - secondsPerLiquidityOutsideUpperX128,
                secondsOutsideLower - secondsOutsideUpper
            );
        } else if (_slot0.tick < tickUpper) {
            uint32 time = _blockTimestamp();
            (int56 tickCumulative, uint160 secondsPerLiquidityCumulativeX128) =
                observations.observeSingle(
                    time,
                    0,
                    _slot0.tick,
                    _slot0.observationIndex,
                    liquidity,
                    _slot0.observationCardinality
                );
            return (
                tickCumulative - tickCumulativeLower - tickCumulativeUpper,
                secondsPerLiquidityCumulativeX128 -
                    secondsPerLiquidityOutsideLowerX128 -
                    secondsPerLiquidityOutsideUpperX128,
                time - secondsOutsideLower - secondsOutsideUpper
            );
        } else {
            return (
                tickCumulativeUpper - tickCumulativeLower,
                secondsPerLiquidityOutsideUpperX128 - secondsPerLiquidityOutsideLowerX128,
                secondsOutsideUpper - secondsOutsideLower
            );
        }
    }

    /// @inheritdoc IUniswapV3PoolDerivedState
    function observe(uint32[] calldata secondsAgos)
        external
        view
        override
        noDelegateCall
        returns (int56[] memory tickCumulatives, uint160[] memory secondsPerLiquidityCumulativeX128s)
    {
        return
            observations.observe(
                _blockTimestamp(),
                secondsAgos,
                slot0.tick,
                slot0.observationIndex,
                liquidity,
                slot0.observationCardinality
            );
    }

    // see IUniswapV3PoolActions -- !! not implemented in interface !!
    function increaseObservationCardinalityNext(uint16 observationCardinalityNext)
        external
        override
        lock
        noDelegateCall
    {
        uint16 observationCardinalityNextOld = slot0.observationCardinalityNext; // for the event
        uint16 observationCardinalityNextNew =
            observations.grow(observationCardinalityNextOld, observationCardinalityNext);
        slot0.observationCardinalityNext = observationCardinalityNextNew;
        if (observationCardinalityNextOld != observationCardinalityNextNew)
            emit IncreaseObservationCardinalityNext(observationCardinalityNextOld, observationCardinalityNextNew);
    }

    // see IUniswapV3PoolActions
    function initialize(uint160 sqrtPriceX96) external override {
        require(slot0.sqrtPriceX96 == 0, 'AI');
        int24 tick = TickMath.getTickAtSqrtRatio(sqrtPriceX96);
        (uint16 cardinality, uint16 cardinalityNext) = observations.initialize(_blockTimestamp());
        slot0 = Slot0({
            sqrtPriceX96: sqrtPriceX96,
            tick: tick,
            observationIndex: 0,
            observationCardinality: cardinality,
            observationCardinalityNext: cardinalityNext,
            feeProtocol: 0,
            unlocked: true
        });

        emit Initialize(sqrtPriceX96, tick);
    }

    function getPoolPosition(
        address owner,
        int24 tickLower,
        int24 tickUpper
    ) external view override returns(Position.Info memory position){
        position = positions.get(owner, tickLower, tickUpper);
    }

    // to be called by poolII
    function modifyTokensOwed(
        address owner,
        int24 tickLower,
        int24 tickUpper,
        uint128 _tokensOwed0,
        uint128 _tokensOwed1
    ) external override {
        Position.Info storage position = positions.get(owner, tickLower, tickUpper);
        position.tokensOwed0 = position.tokensOwed0 + _tokensOwed0;
        position.tokensOwed1 = position.tokensOwed1 + _tokensOwed1;
    }

    function _modifyPosition(address owner, 
                            int24 tickLower, 
                            int24 tickUpper, 
                            int128 liquidityDelta, 
                            int8 option)
        external
        override
        returns (
            Position.Info memory position,
            int256 amount0,
            int256 amount1
        )
    {
        checkTicks(tickLower, tickUpper);

        Slot0 memory _slot0 = slot0; // SLOAD for gas optimization
        if (option == 21){ revert(" --- [_mod]  21 ");}

        if (option < 50){ 
            position = _updatePosition(
                owner,
                tickLower,
                tickUpper,
                liquidityDelta,
                _slot0.tick,
                option
            );
        }

        if (liquidityDelta != 0) {
            if (_slot0.tick < tickLower) {
                // current tick is below the passed range; liquidity can only become in range by crossing from left to
                // right, when we'll need _more_ token0 (it's becoming more valuable) so user must provide it
                amount0 = SqrtPriceMath.getAmount0Delta(
                    TickMath.getSqrtRatioAtTick(tickLower),
                    TickMath.getSqrtRatioAtTick(tickUpper),
                    liquidityDelta
                );
                if (option == 22){ revert(" [_mod :: t0 < tL]  22 ");}

            } else if (_slot0.tick < tickUpper) {
                // current tick is inside the passed range
                uint128 liquidityBefore = liquidity; // SLOAD for gas optimization

                // write an oracle entry
                if (option < 50){ 
                    (slot0.observationIndex, slot0.observationCardinality) = observations.write(
                        _slot0.observationIndex,
                        _blockTimestamp(),
                        _slot0.tick,
                        liquidityBefore,
                        _slot0.observationCardinality,
                        _slot0.observationCardinalityNext
                    );
                }
                
                if (option == 22){ revert(" [_mod :: tL < t0 < tU]  22 ");}

                amount0 = SqrtPriceMath.getAmount0Delta(
                    _slot0.sqrtPriceX96,
                    TickMath.getSqrtRatioAtTick(tickUpper),
                    liquidityDelta
                );
                amount1 = SqrtPriceMath.getAmount1Delta(
                    TickMath.getSqrtRatioAtTick(tickLower),
                    _slot0.sqrtPriceX96,
                    liquidityDelta
                );

                if (option < 50){ 
                    liquidity = LiquidityMath.addDelta(liquidityBefore, liquidityDelta);
                }
            } else {
                // current tick is above the passed range; liquidity can only become in range by crossing from right to
                // left, when we'll need _more_ token1 (it's becoming more valuable) so user must provide it
                amount1 = SqrtPriceMath.getAmount1Delta(
                    TickMath.getSqrtRatioAtTick(tickLower),
                    TickMath.getSqrtRatioAtTick(tickUpper),
                    liquidityDelta
                );
                if (option == 22){ revert(" [_mod :: tU < t0]  22 ");}
            }
        }
        emit modifyAmounts(liquidityDelta, amount0, amount1);
    }

    // only poolII
    function poolII_transfer(bool zeroOrOne, address recipient, uint256 amount) external override{
        address trasnferToken;
        if (zeroOrOne){
            trasnferToken = token0;
        }else{
            trasnferToken = token1;
        }
        TransferHelper.safeTransfer(trasnferToken, recipient, amount);
    }

    function _updatePosition(
        address owner,
        int24 tickLower,
        int24 tickUpper,
        int128 liquidityDelta,
        int24 tick,
        int8 option
    ) private returns (Position.Info storage position) {
        position = positions.get(owner, tickLower, tickUpper);
        uint256 _feeGrowthGlobal0X128 = feeGrowthGlobal0X128; // SLOAD for gas optimization
        uint256 _feeGrowthGlobal1X128 = feeGrowthGlobal1X128; // SLOAD for gas optimization

        // if we need to update the ticks, do it
        bool flippedLower;
        bool flippedUpper;
        if (liquidityDelta != 0) {
            uint32 time = _blockTimestamp();
            (int56 tickCumulative, uint160 secondsPerLiquidityCumulativeX128) =
                observations.observeSingle(
                    time,
                    0,
                    slot0.tick,
                    slot0.observationIndex,
                    liquidity,
                    slot0.observationCardinality
                );

            if (option == 31){ revert(" _up :: 31 ");}
            
            flippedLower = ticks.update(
                tickLower,
                tick,
                liquidityDelta,
                _feeGrowthGlobal0X128,
                _feeGrowthGlobal1X128,
                secondsPerLiquidityCumulativeX128,
                tickCumulative,
                time,
                false,
                maxLiquidityPerTick
            );
            flippedUpper = ticks.update(
                tickUpper,
                tick,
                liquidityDelta,
                _feeGrowthGlobal0X128,
                _feeGrowthGlobal1X128,
                secondsPerLiquidityCumulativeX128,
                tickCumulative,
                time,
                true,
                maxLiquidityPerTick
            );

            if (option == 32){ revert(" _up ::  32 ");}

            if (flippedLower) {
                tickBitmap.flipTick(tickLower, tickSpacing);
            }
            if (flippedUpper) {
                tickBitmap.flipTick(tickUpper, tickSpacing);
            }
            if (option == 33){ revert(" _up ::  33 ");}
        }

        (uint256 feeGrowthInside0X128, uint256 feeGrowthInside1X128) =
            ticks.getFeeGrowthInside(tickLower, tickUpper, tick, _feeGrowthGlobal0X128, _feeGrowthGlobal1X128);

        position.update(liquidityDelta, feeGrowthInside0X128, feeGrowthInside1X128);

        if (option == 34){ revert(" _up ::  34 ");}
        
        // clear any tick data that is no longer needed
        if (liquidityDelta < 0) {
            if (flippedLower) {
                ticks.clear(tickLower);
            }
            if (flippedUpper) {
                ticks.clear(tickUpper);
            }
        }

    }

    struct SwapCache {
        // the protocol fee for the input token
        uint8 feeProtocol;
        // liquidity at the beginning of the swap
        uint128 liquidityStart;
        // the timestamp of the current block
        uint32 blockTimestamp;
        // the current value of the tick accumulator, computed only if we cross an initialized tick
        int56 tickCumulative;
        // the current value of seconds per liquidity accumulator, computed only if we cross an initialized tick
        uint160 secondsPerLiquidityCumulativeX128;
        // whether we've computed and cached the above two accumulators
        bool computedLatestObservation;
    }

    // the top level state of the swap, the results of which are recorded in storage at the end
    struct SwapState {
        // the amount remaining to be swapped in/out of the input/output asset
        int256 amountSpecifiedRemaining;
        // the amount already swapped out/in of the output/input asset
        int256 amountCalculated;
        // current sqrt(price)
        uint160 sqrtPriceX96;
        // the tick associated with the current price
        int24 tick;
        // the global fee growth of the input token
        uint256 feeGrowthGlobalX128;
        // amount of input token paid as protocol fee
        uint128 protocolFee;
        // the current liquidity in range
        uint128 liquidity;
    }
 
    struct StepComputations {
        // the price at the beginning of the step
        uint160 sqrtPriceStartX96;
        //
        uint160 sqrtPriceTartgetX96;
        // the next tick to swap to from the current tick in the swap direction
        int24 tickNext;
        // whether tickNext is initialized or not
        bool initialized;
        // sqrt(price) for the next tick (1/0)
        uint160 sqrtPriceNextX96;
        // how much is being swapped in in this step
        uint256 amountIn;
        // how much is being swapped out
        uint256 amountOut;
        // how much fee is being paid in
        uint256 feeAmount;
    }

    // SwapCallbackData added to pool so that two parameters can be used in swap(...); Ropt and exactIinput
        // Ropt : revert option for troubleshooting [see readme file]
        // exactInput : In the uniswapV3 protocol this parameter is declared in swap(...). 
        // Here passed to the pool instead because A) swap(...) is broken into two separate functions, so
        // we avoid declaring it twice and B) it saves room.
    struct SwapCallbackData {
        bytes path;
        address payer;
        int8 Ropt;
        bool exactInput;
        bool multiPools;
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

    // see IUniswapV3PoolActions
    function swap(
        address recipient,
        bool zeroForOne,
        int256 amountSpecified,
        uint160 sqrtPriceLimitX96,
        bytes calldata data
    ) external override  returns (int256 amount0, int256 amount1) {
        //
            SwapCallbackData memory swap_data = abi.decode(data, (SwapCallbackData));
            revertOption( swap_data.multiPools, swap_data.Ropt, 6, "[swap] 6");
            Slot0 memory slot0Start = slot0;

            // reverts
                if (swap_data.Ropt <= 19 ){
                    require(amountSpecified != 0, 'AS');
                }
                require(slot0Start.unlocked, 'LOK');
                if (zeroForOne==true) {
                    require(sqrtPriceLimitX96 < slot0Start.sqrtPriceX96, "01: P < P0");
                    require(sqrtPriceLimitX96 > TickMath.MIN_SQRT_RATIO, "01: P > MIN");
                }
                if (zeroForOne==false) {
                    require(sqrtPriceLimitX96 > slot0Start.sqrtPriceX96, "10: P ? P0");
                    require(sqrtPriceLimitX96 < TickMath.MAX_SQRT_RATIO, "10: P < MAX");
                }
            //

            // load state/ cache
                // unlock slot0 to allow state changes only if option < 19
                if (swap_data.Ropt <= 19){ slot0.unlocked = false;}
                SwapCache memory cache =
                    SwapCache({
                        liquidityStart: liquidity,
                        blockTimestamp: _blockTimestamp(),
                        feeProtocol: zeroForOne ? (slot0Start.feeProtocol % 16) : (slot0Start.feeProtocol >> 4),
                        secondsPerLiquidityCumulativeX128: 0,
                        tickCumulative: 0,
                        computedLatestObservation: false
                    });

                // bool exactInput = amountSpecified > 0; // put into swapCallbackData
                SwapState memory state =
                    SwapState({
                        amountSpecifiedRemaining: amountSpecified,
                        amountCalculated: 0,
                        sqrtPriceX96: slot0Start.sqrtPriceX96,
                        tick: slot0Start.tick,
                        feeGrowthGlobalX128: zeroForOne ? feeGrowthGlobal0X128 : feeGrowthGlobal1X128,
                        protocolFee: 0,
                        liquidity: cache.liquidityStart
                    });
            //
        // while loop  -------------------------------------------------------------------------
            // continue swapping as long as we haven't used the entire input/output and haven't 
            // reached the price limit 
            while (state.amountSpecifiedRemaining != 0 && state.sqrtPriceX96 != sqrtPriceLimitX96) {
                StepComputations memory step;
                step.sqrtPriceStartX96 = state.sqrtPriceX96;
                (step.tickNext, step.initialized) = tickBitmap.nextInitializedTickWithinOneWord(
                    state.tick,
                    tickSpacing,
                    zeroForOne
                );
                // ensure that we do not overshoot the min/max tick, as the tick bitmap is not aware of these bounds
                if (step.tickNext < TickMath.MIN_TICK) {
                    step.tickNext = TickMath.MIN_TICK;
                } else if (step.tickNext > TickMath.MAX_TICK) {
                    step.tickNext = TickMath.MAX_TICK;
                }
                // get the price for the next tick
                step.sqrtPriceNextX96 = TickMath.getSqrtRatioAtTick(step.tickNext);
                
                // Determine the target square root price based on the trade direction (isDirectionZeroForOne)
                // and compare the next square root price with the limit
                step.sqrtPriceTartgetX96 = (
                    zeroForOne 
                        ? step.sqrtPriceNextX96 < sqrtPriceLimitX96 
                        : step.sqrtPriceNextX96 > sqrtPriceLimitX96
                    ) 
                    ? sqrtPriceLimitX96 
                    : step.sqrtPriceNextX96;
                // compute values to swap to the target tick, price limit, or point where input/output amount is exhausted

                (state.sqrtPriceX96, step.amountIn, step.amountOut, step.feeAmount) = SwapMath.computeSwapStep(
                    state.sqrtPriceX96,
                    (zeroForOne ? step.sqrtPriceNextX96 < sqrtPriceLimitX96 : step.sqrtPriceNextX96 > sqrtPriceLimitX96)
                        ? sqrtPriceLimitX96
                        : step.sqrtPriceNextX96,
                    state.liquidity,
                    state.amountSpecifiedRemaining,
                    fee
                );

                // update state amounts
                if (swap_data.exactInput) {
                    state.amountSpecifiedRemaining -= (step.amountIn + step.feeAmount).toInt256();
                    state.amountCalculated = state.amountCalculated.sub(step.amountOut.toInt256());
                } else {
                    state.amountSpecifiedRemaining += step.amountOut.toInt256();
                    state.amountCalculated = state.amountCalculated.add((step.amountIn + step.feeAmount).toInt256());
                }


                // ------- EMIT STATEMENTS
                // amounts
                if (swap_data.Ropt==21){
                    emit SteppedAmounts(step.tickNext, 
                                state.amountSpecifiedRemaining, 
                                state.amountCalculated);
                }
                // prices
                if (swap_data.Ropt==22 ){
                    emit SteppedPrices(step.tickNext, 
                                state.sqrtPriceX96, 
                                step.sqrtPriceNextX96,
                                step.sqrtPriceTartgetX96);
                }
                // computeSwapStep amounts
                if (swap_data.Ropt==23 ){
                    emit SwapStepAmounts(step.tickNext, 
                                step.amountIn, 
                                step.amountOut, 
                                step.feeAmount);
                }

                // if the protocol fee is on, calculate how much is owed, decrement feeAmount, and increment protocolFee
                if (cache.feeProtocol > 0) {
                    uint256 delta   = step.feeAmount / cache.feeProtocol;
                    step.feeAmount -= delta;
                    state.protocolFee += uint128(delta);
                }
                // update global fee tracker
                if (state.liquidity > 0)
                    state.feeGrowthGlobalX128 += FullMath.mulDiv(step.feeAmount, FixedPoint128.Q128, state.liquidity);
                // shift tick if we reached the next price
                
                if (state.sqrtPriceX96 == step.sqrtPriceNextX96) {
                    // if the tick is initialized, run the tick transition
                    
                    if (step.initialized) {
                        revertOption( swap_data.multiPools, swap_data.Ropt, 7, "[swap] 7");
                        // check for the placeholder value, which we replace with the actual value the first time the swap
                        // crosses an initialized tick
                        if (!cache.computedLatestObservation) {
                            (cache.tickCumulative, cache.secondsPerLiquidityCumulativeX128) = observations.observeSingle(
                                cache.blockTimestamp,
                                0,
                                slot0Start.tick,
                                slot0Start.observationIndex,
                                cache.liquidityStart,
                                slot0Start.observationCardinality
                            );
                            cache.computedLatestObservation = true;
                        }
                        int128 liquidityNet =
                            ticks.cross(
                                step.tickNext,
                                (zeroForOne ? state.feeGrowthGlobalX128 : feeGrowthGlobal0X128),
                                (zeroForOne ? feeGrowthGlobal1X128 : state.feeGrowthGlobalX128),
                                cache.secondsPerLiquidityCumulativeX128,
                                cache.tickCumulative,
                                cache.blockTimestamp
                            );
                        // if we're moving leftward, we interpret liquidityNet as the opposite sign
                        // safe because liquidityNet cannot be type(int128).min
                        if (zeroForOne) liquidityNet = -liquidityNet;

                        state.liquidity = LiquidityMath.addDelta(state.liquidity, liquidityNet);
                    }

                    state.tick = zeroForOne ? step.tickNext - 1 : step.tickNext;
                } else if (state.sqrtPriceX96 != step.sqrtPriceStartX96) {
                    // recompute unless we're on a lower tick boundary 
                    // (i.e. already transitioned ticks), and haven't moved
                    state.tick = TickMath.getTickAtSqrtRatio(state.sqrtPriceX96);
                }

            }
        
        // end while loop---------------------------------------------------------------------------

        (amount0, amount1) = zeroForOne == swap_data.exactInput
            ? (amountSpecified - state.amountSpecifiedRemaining, state.amountCalculated)
            : (state.amountCalculated, amountSpecified - state.amountSpecifiedRemaining);

        // if option = 20 bypass all state changing calls and emits some troubleshooting paramaters.
        // related to the calculation of amounts

        if (swap_data.Ropt==20 ){
                emit SwapAmounts(swap_data.multiPools, msg.sender, recipient, zeroForOne, amount0, amount1);
                IUniswapV3SwapCallback(msg.sender).uniswapV3SwapCallback(amount0, amount1, data);
        }
        
        if (swap_data.Ropt<=19 ){
            //
            // oracle entry [if tick change]
                // update tick and write an oracle entry if the tick change
            if (state.tick != slot0Start.tick) {
                    (uint16 observationIndex, uint16 observationCardinality) =
                        observations.write(
                            slot0Start.observationIndex,
                            cache.blockTimestamp,
                            slot0Start.tick,
                            cache.liquidityStart,
                            slot0Start.observationCardinality,
                            slot0Start.observationCardinalityNext
                        );
                    (slot0.sqrtPriceX96, slot0.tick, slot0.observationIndex, slot0.observationCardinality) = (
                        state.sqrtPriceX96,
                        state.tick,
                        observationIndex,
                        observationCardinality
                    );

                } else {
                    // otherwise just update the price
                    slot0.sqrtPriceX96 = state.sqrtPriceX96;
            }

            // update liquidity/ protocolFees
            // update liquidity if it changed
            if (cache.liquidityStart != state.liquidity) liquidity = state.liquidity;

            // update fee growth global and, if necessary, protocol fees
            // overflow is acceptable, protocol has to withdraw before it hits type(uint128).max fees
            if (zeroForOne) {
                    feeGrowthGlobal0X128 = state.feeGrowthGlobalX128;
                    if (state.protocolFee > 0) protocolFees.token0 += state.protocolFee;
                } else {
                    feeGrowthGlobal1X128 = state.feeGrowthGlobalX128;
                    if (state.protocolFee > 0) protocolFees.token1 += state.protocolFee;
            }

            slot0.unlocked = true;
            revertOption( swap_data.multiPools, swap_data.Ropt, 8, "[swap] 8");
            RouterPaymentCallback( zeroForOne,
                                    amount0,
                                    amount1,
                                    recipient,
                                    data);
            emit Swap(msg.sender, recipient, amount0, amount1, state.sqrtPriceX96, state.liquidity, state.tick);
        }
    }


    function RouterPaymentCallback( 
                        bool zeroForOne,
                        int256 amount0,
                        int256 amount1,
                        address recipient,
                        bytes calldata data
                        ) internal  { 
        //------------
        SwapCallbackData memory swap_data = abi.decode(data, (SwapCallbackData));

        // calculate amounts/ transfer
        revertOption( swap_data.multiPools, swap_data.Ropt, 9, "[swap:: callbacks] 9");
        // do the transfers and collect payment
        if (zeroForOne) {
            if (amount1 < 0) {TransferHelper.safeTransfer(token1, recipient, uint256(-amount1));}
            uint256 balance0Before = balance0();
            IUniswapV3SwapCallback(msg.sender).uniswapV3SwapCallback(amount0, amount1, data);
            require(balance0Before.add(uint256(amount0)) <= balance0(), 'IIA');
        } else {
            if (amount0 < 0) {TransferHelper.safeTransfer(token0, recipient, uint256(-amount0)); }
            uint256 balance1Before = balance1();
            IUniswapV3SwapCallback(msg.sender).uniswapV3SwapCallback(amount0, amount1, data);
            require(balance1Before.add(uint256(amount1)) <= balance1(), 'IIA');
        }
    }

    function setFeeProtocol(uint8 feeProtocol0, uint8 feeProtocol1) external override {
        require(
            (feeProtocol0 == 0 || (feeProtocol0 >= 4 && feeProtocol0 <= 10)) &&
                (feeProtocol1 == 0 || (feeProtocol1 >= 4 && feeProtocol1 <= 10))
        );
        uint8 feeProtocolOld = slot0.feeProtocol;
        slot0.feeProtocol = feeProtocol0 + (feeProtocol1 << 4);
        emit SetFeeProtocol(feeProtocolOld % 16, feeProtocolOld >> 4, feeProtocol0, feeProtocol1);
    }

    function collectProtocol(
        address recipient,
        uint128 amount0Requested,
        uint128 amount1Requested
    ) external override returns (uint128 amount0, uint128 amount1) {
        amount0 = amount0Requested > protocolFees.token0 ? protocolFees.token0 : amount0Requested;
        amount1 = amount1Requested > protocolFees.token1 ? protocolFees.token1 : amount1Requested;

        if (amount0 > 0) {
            if (amount0 == protocolFees.token0) amount0--; // ensure that the slot is not cleared, for gas savings
            protocolFees.token0 -= amount0;
            TransferHelper.safeTransfer(token0, recipient, amount0);
        }
        if (amount1 > 0) {
            if (amount1 == protocolFees.token1) amount1--; // ensure that the slot is not cleared, for gas savings
            protocolFees.token1 -= amount1;
            TransferHelper.safeTransfer(token1, recipient, amount1);
        }

        emit CollectProtocol(msg.sender, recipient, amount0, amount1);
    }
}