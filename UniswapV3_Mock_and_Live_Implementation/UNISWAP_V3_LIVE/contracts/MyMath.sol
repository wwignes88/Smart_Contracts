// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;
pragma abicoder v2;

import '@uniswap/v3-core/contracts/libraries/TickBitmap.sol';
import '@uniswap/v3-periphery/contracts/libraries/Path.sol';
import '@uniswap/v3-periphery/contracts/libraries/BytesLib.sol';
import '@uniswap/v3-core/contracts/libraries/TickMath.sol';
import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol';
import '@uniswap/v3-periphery/contracts/libraries/LiquidityAmounts.sol';
import '@uniswap/v3-core/contracts/libraries/FullMath.sol';
import '@uniswap/v3-core/contracts/libraries/SqrtPriceMath.sol';
contract MyMath {

    using TickBitmap for mapping(int16 => uint256);
    using Path for bytes;
    using BytesLib for bytes;

// =============================================================
// =================== NPM functions ==========================
// ============================================================
    // see PositionKey.sol library in v3-periphery.
    function compute(
        address owner,
        int24 tickLower,
        int24 tickUpper
    ) external pure returns (bytes32) {
        return keccak256(abi.encodePacked(owner, tickLower, tickUpper));
    }

// =============================================================
// =================== Swap functions ==========================
// =============================================================


    // MISC
        /*
        function _blockTimestamp32() public view virtual returns (uint32) {
            return uint32(block.timestamp); // truncation is desired
        }
        */
        function _blockTimestamp() public view virtual returns (uint256) {
            return block.timestamp; // truncation is desired
        }

        function shift_uint8(uint8 value) public view returns (uint8){
            return value >> 4;
        }

        // see exactInputInternal and exactOutputInternal of router contract [and others].
        // we use this in certain cases to give us insight to what our zeroForOne parameter is
        // when functions like exactInputInternal construct it instead of accepting it as an input.
        function getZeroForOne(address tokenA, address tokenB) public view returns(bool zeroForOne){
            zeroForOne = tokenA < tokenB;
        }

    //
    // NEXT TICK 
        //TickBitmap.sol :: mock nextInitializedTickWithinOneWord function
        function mostSignificantBit(uint256 x) public pure returns(uint8 r){
            r = BitMath.mostSignificantBit(x);
        }
        function leastSignificantBit(uint256 x) public pure returns(uint8 r){
            r = BitMath.leastSignificantBit(x);
        }
        function position(int24 tick) public pure returns (int16 wordPos, uint8 bitPos) {
            wordPos = int16(tick >> 8);
            bitPos  = uint8(tick % 256);
        }

        // calculate next tick based on input from pool tickBitmap[wordPos]
        function nextTick(
            int24 tick,
            int24 tickSpacing,
            bool lte,
            IUniswapV3Pool pool
         ) public view returns ( int24 compressed,
                                uint256 maskA,
                                uint256 mask,
                                uint256 masked,
                                int24 next,
                                uint256 tickBit,
                                bool initialized) 
         {
            compressed = tick / tickSpacing;
            if (tick < 0 && tick % tickSpacing != 0) compressed--; // round towards negative infinity

            
            if (lte) {
                (int16 wordPos, uint8 bitPos) = position(compressed);
                // all the 1s at or to the right of the current bitPos
                maskA   = (1 << bitPos) ;
                mask    = (1 << bitPos) - 1 + (1 << bitPos);
                tickBit = pool.tickBitmap(wordPos);
                masked  = tickBit & mask;
                initialized  = masked != 0;
                next = initialized
                    ? (compressed - int24(bitPos - BitMath.mostSignificantBit(masked))) * tickSpacing
                    : (compressed - int24(bitPos)) * tickSpacing;
                
            } else {
                // start from the word of the next tick, since the current tick state doesn't matter
                (int16 wordPos, uint8 bitPos) = position(compressed + 1);
                // all the 1s at or to the left of the bitPos
                maskA   = (1 << bitPos);
                mask    = ~((1 << bitPos) - 1);
                tickBit = pool.tickBitmap(wordPos);
                masked  = tickBit & mask;
                initialized = masked != 0;
                next = initialized
                    ? (compressed + 1 + int24(BitMath.leastSignificantBit(masked) - bitPos)) * tickSpacing
                    : (compressed + 1 + int24(type(uint8).max - bitPos)) * tickSpacing;

            }

        }
    //




// ===================================================
// =================== math ==========================
// ===================================================

    function sqrtPatTick(int24 tick_) external pure returns (uint160 sqrtPriceX96_){
        sqrtPriceX96_ = TickMath.getSqrtRatioAtTick( tick_);
    }
    function tickAtSqrt(uint160 sqrtPriceX96_) external pure returns (int24 tick_){
        tick_ = TickMath.getTickAtSqrtRatio( sqrtPriceX96_);
    }


    // LIQUIDITY RELATED FUNCTIONS
        function toUint128(uint256 x) private pure returns (uint128 y) {
            require((y = uint128(x)) == x);
        }

        uint256 internal constant Q96 = 0x1000000000000000000000000;

        function getQ96() public pure returns (uint256 q96){
            q96 = Q96;
        }

        // see LForZero [below]
        function MulDiv(
            uint256 a,
            uint256 b,
            uint256 denominator
         ) public pure returns (uint256 result) {
            // 512-bit multiply [prod1 prod0] = a * b
            // Compute the product mod 2**256 and mod 2**256 - 1
            // then use the Chinese Remainder Theorem to reconstruct
            // the 512 bit result. The result is stored in two 256
            // variables such that product = prod1 * 2**256 + prod0
            uint256 prod0; // Least significant 256 bits of the product
            uint256 prod1; // Most significant 256 bits of the product
            assembly {
                let mm := mulmod(a, b, not(0))
                prod0 := mul(a, b)
                prod1 := sub(sub(mm, prod0), lt(mm, prod0))
            }

            // Handle non-overflow cases, 256 by 256 division
            if (prod1 == 0) {
                require(denominator > 0);
                assembly {
                    result := div(prod0, denominator)
                }
                return result;
            }

            // Make sure the result is less than 2**256.
            // Also prevents denominator == 0
            require(denominator > prod1);

            ///////////////////////////////////////////////
            // 512 by 256 division.
            ///////////////////////////////////////////////

            // Make division exact by subtracting the remainder from [prod1 prod0]
            // Compute remainder using mulmod
            uint256 remainder;
            assembly {
                remainder := mulmod(a, b, denominator)
            }
            // Subtract 256 bit number from 512 bit number
            assembly {
                prod1 := sub(prod1, gt(remainder, prod0))
                prod0 := sub(prod0, remainder)
            }

            // Factor powers of two out of denominator
            // Compute largest power of two divisor of denominator.
            // Always >= 1.
            uint256 twos = -denominator & denominator;
            // Divide denominator by power of two
            assembly {
                denominator := div(denominator, twos)
            }

            // Divide [prod1 prod0] by the factors of two
            assembly {
                prod0 := div(prod0, twos)
            }
            // Shift in bits from prod1 into prod0. For this we need
            // to flip `twos` such that it is 2**256 / twos.
            // If twos is zero, then it becomes one
            assembly {
                twos := add(div(sub(0, twos), twos), 1)
            }
            prod0 |= prod1 * twos;

            // Invert denominator mod 2**256
            // Now that denominator is an odd number, it has an inverse
            // modulo 2**256 such that denominator * inv = 1 mod 2**256.
            // Compute the inverse by starting with a seed that is correct
            // correct for four bits. That is, denominator * inv = 1 mod 2**4
            uint256 inv = (3 * denominator) ^ 2;
            // Now use Newton-Raphson iteration to improve the precision.
            // Thanks to Hensel's lifting lemma, this also works in modular
            // arithmetic, doubling the correct bits in each step.
            inv *= 2 - denominator * inv; // inverse mod 2**8
            inv *= 2 - denominator * inv; // inverse mod 2**16
            inv *= 2 - denominator * inv; // inverse mod 2**32
            inv *= 2 - denominator * inv; // inverse mod 2**64
            inv *= 2 - denominator * inv; // inverse mod 2**128
            inv *= 2 - denominator * inv; // inverse mod 2**256

            // Because the division is now exact we can divide by multiplying
            // with the modular inverse of denominator. This will give us the
            // correct result modulo 2**256. Since the precoditions guarantee
            // that the outcome is less than 2**256, this is the final result.
            // We don't need to compute the high bits of the result and prod1
            // is no longer required.
            result = prod0 * inv;
            return result;
        }

        // LIQUIDITY FOR AMOUNTS
            // see LiquidityAmounts.sol and LiquidityManager :: addLiquidity in v3-periphery 
            // Calculates amount0 * (sqrt(upper) * sqrt(lower)) / (sqrt(upper) - sqrt(lower))
            function LForZero(
                uint160 sqrtRatioAX96,
                uint160 sqrtRatioBX96,
                uint256 amount0
            ) public pure returns (uint256 intermediate, uint256 lIQUIDITY, uint128 liquidity) {
                if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
                intermediate = MulDiv(sqrtRatioAX96, sqrtRatioBX96, Q96);
                lIQUIDITY = MulDiv(amount0, intermediate, sqrtRatioBX96 - sqrtRatioAX96);
                liquidity = toUint128(lIQUIDITY);
            }
            // Calculates amount1 / (sqrt(upper) - sqrt(lower)).
            function LForOne(
                uint160 sqrtRatioAX96,
                uint160 sqrtRatioBX96,
                uint256 amount1
            ) public pure  returns (uint128 liquidity) {
                if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
                return toUint128(MulDiv(amount1, Q96, sqrtRatioBX96 - sqrtRatioAX96));
            }


            function LForAmounts(
                uint160 sqrtRatioX96,
                uint160 sqrtRatioAX96,
                uint160 sqrtRatioBX96,
                uint256 amount0,
                uint256 amount1
            ) external view returns ( uint128 liquidity ) {
                if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);
                if (sqrtRatioX96 <= sqrtRatioAX96) {
                    ( , , liquidity) = LForZero(sqrtRatioAX96, sqrtRatioBX96, amount0);
                } else if (sqrtRatioX96 < sqrtRatioBX96) {
                    uint128 liquidity0;
                    uint128 liquidity1;
                    ( , , liquidity0) = LForZero(sqrtRatioX96, sqrtRatioBX96, amount0);
                    liquidity1 = LForOne(sqrtRatioAX96, sqrtRatioX96, amount1);
                    liquidity  = liquidity0 < liquidity1 ? liquidity0 : liquidity1;
                } else {
                    liquidity = LForOne(sqrtRatioAX96, sqrtRatioBX96, amount1);
                }
            }

        //  
        // AMOUNTS FOR LIQUIDITY
            ///  Gets the amount0 delta between two prices
            // Calculates liquidity / sqrt(lower) - liquidity / sqrt(upper),
            // i.e. liquidity * (sqrt(upper) - sqrt(lower)) / (sqrt(upper) * sqrt(lower))
            function getAmount0ForLiquidity(
                uint160 sqrtRatioAX96,
                uint160 sqrtRatioBX96,
                uint128 liquidity
            ) public pure returns (uint256 amount0) {
                if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);

                return
                    FullMath.mulDiv(
                        uint256(liquidity) << FixedPoint96.RESOLUTION,
                        sqrtRatioBX96 - sqrtRatioAX96,
                        sqrtRatioBX96
                    ) / sqrtRatioAX96;
            }

            /// @notice Gets the amount1 delta between two prices
            /// @dev Calculates liquidity * (sqrt(upper) - sqrt(lower))
            function getAmount1ForLiquidity(
                uint160 sqrtRatioAX96,
                uint160 sqrtRatioBX96,
                uint128 liquidity
            ) public pure returns (uint256 amount1) {
                if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);

                return FullMath.mulDiv(liquidity, sqrtRatioBX96 - sqrtRatioAX96, FixedPoint96.Q96);
            }

            function getAmountsForLiquidity(
                uint160 sqrtRatioX96,
                uint160 sqrtRatioAX96,
                uint160 sqrtRatioBX96,
                uint128 liquidity
            ) public pure returns (uint256 amount0, uint256 amount1) {
                if (sqrtRatioAX96 > sqrtRatioBX96) (sqrtRatioAX96, sqrtRatioBX96) = (sqrtRatioBX96, sqrtRatioAX96);

                if (sqrtRatioX96 <= sqrtRatioAX96) {
                    amount0 = getAmount0ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
                } else if (sqrtRatioX96 < sqrtRatioBX96) {
                    amount0 = getAmount0ForLiquidity(sqrtRatioX96, sqrtRatioBX96, liquidity);
                    amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioX96, liquidity);
                } else {
                    amount1 = getAmount1ForLiquidity(sqrtRatioAX96, sqrtRatioBX96, liquidity);
                }
            }
        //
    //

    function getFeeGrowthInside(
        int24 tickLower,
        int24 tickUpper,
        int24 tickCurrent,
        uint256 feeGrowthGlobalX128,
        uint256 LOWfeeGrowthOutsideX128,
        uint256 HIGHfeeGrowthOutsideX128,
        uint128 liquidityGrossBefore
    ) public view returns (
        uint256 feeGrowthInsideX128,
        uint256 feeGrowthBelowX128,
        uint256 feeGrowthAboveX128) {
        
        //----- Tick.sol :: update
        // see pool :: _update function
        if (liquidityGrossBefore == 0) {
            // by convention, we assume that all growth before a tick was initialized happened _below_ the tick
            if (tickLower <= tickCurrent) {
                LOWfeeGrowthOutsideX128 = feeGrowthGlobalX128;
            }
            if (tickUpper <= tickCurrent) {
                HIGHfeeGrowthOutsideX128 = feeGrowthGlobalX128;
            }
        }

        //----- Tick.sol :: getFeeGrowthInside 
        if (tickCurrent >= tickLower) {
            feeGrowthBelowX128 = LOWfeeGrowthOutsideX128;
        } else {
            feeGrowthBelowX128 = feeGrowthGlobalX128 - LOWfeeGrowthOutsideX128;
        }
        if (tickCurrent < tickUpper) {
            feeGrowthAboveX128 = HIGHfeeGrowthOutsideX128;
        } else {
            feeGrowthAboveX128 = feeGrowthGlobalX128 - HIGHfeeGrowthOutsideX128;
        }
        feeGrowthInsideX128 = feeGrowthGlobalX128 - feeGrowthBelowX128 - feeGrowthAboveX128;
    }



}