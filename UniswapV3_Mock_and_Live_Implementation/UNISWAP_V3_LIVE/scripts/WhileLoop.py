
from scripts.Load.helpful_scripts import (  time,
                                            get_contract,
                                            loadPool,
                                            get_accounts,
                                            gas_controls,
                                            get_Token_bal,
                                            getTickInfo,
                                            sys,
                                            p_from_x96,
                                            MIN_TICK,
                                            MAX_TICK,
                                            MIN_SQRT_RATIO, MAX_SQRT_RATIO,
                                            Q128)
from scripts.Load.DICTS import *

my_math   = get_contract('MyMath')

           
# account  : 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce
def whileLoop():

    ManagerII  = get_contract('MNonfungiblePositionManagerII')
    PoolPositionOwner = ManagerII.address
    
    
    account = get_accounts(0) 
    gas_controls(account, set_gas_limit=False, priority_fee=False)
    
    
    print('\n============= whileLoop.py ===============\n')
    
    t0 = 'weth' 
    t1 = 'sand' # tokenIn
    t2 = 'link' # tokenOut

    token0 = get_contract(t0)
    token1 = get_contract(t1)
    token2 = get_contract(t2)

    #FTposition       = getNFTPosition(ManagerII, tokenId, account, True)
    #TL = NFTposition['tickLow'] ; TH = NFTposition['tickHigh']
    #PoolPositionOwner = ManagerII.address
    #PoolPosition      = getPoolPosition(pool, PoolPositionOwner, TL, TH, True)
    
    #    ============ SET PARAMETERS ===============

    InputSwap           = False  # True = exactInputSingle, False = exactOutputSingle
    poolNum             = 2     # 1 = token0/token1 pool, 2 = token1/token2 pool
    ZeroForOne          = False 
    sqrtPriceLimitX96   = 0
                        # 79228162514264340000000000000*3 
                        # zeroForOne ? MIN_SQRT_RATIO + 1 : MAX_SQRT_RATIO - 1 
    amountSpecified     = 15743797125439218009
    deadline            = my_math._blockTimestamp() + 20 # additional seconds added to block.timestamp() for deadline [see deadline below]
    fee                 = 3000
    PRINTS              = [6]
                        # 1 prices
                        # 2 amounts
                        # 3 computeSwapStep inputs/ outputs
                        # 4 state changes, e.g. slot0 parameters, liquidity.
    
    #   ============================================

    #----- see router :: exactOutputInternal
    if InputSwap==False:
        amountSpecified = - amountSpecified
        inOutString = '[OUT]'
    if InputSwap:
        inOutString = '[IN]'
    
    # set pool tokens
    if poolNum == 1:
        (tokenIn, tokenOut) = (token0, token1)
    if poolNum == 2:
        (tokenIn, tokenOut) = (token1, token2)

    # If needed, adjust tokenIn/tokenOut to be in line with ZeroForOne condition:
    #     zeroForOne = TokenIn < TokenOut 
    zeroForOne = my_math.getZeroForOne(tokenIn, tokenOut)
    if zeroForOne != ZeroForOne:
        (tokenIn, tokenOut) = (tokenOut, tokenIn) 
        zeroForOne = my_math.getZeroForOne(tokenIn, tokenOut)
        print('\n*swapped zeroForOne')
    
    
    # set sqrtPriceLimitX96 to min/max (see router :: exactOutputInternal)
    if sqrtPriceLimitX96==0:
        if zeroForOne:
            sqrtPriceLimitX96 = MIN_SQRT_RATIO+1
        if zeroForOne==False:
            sqrtPriceLimitX96 = MAX_SQRT_RATIO-1
            
    # Load pool 
    (pool, slot0, liquidity, tick_spacing) = loadPool(tokenIn, tokenOut, fee, account)

            
    # check sqrtPriceLimitX96 is valid
    # * see revert statements at beginning of swap(...) function.
    p0 = slot0["sqrtPriceX96"]
    if ZeroForOne:
        if sqrtPriceLimitX96 > p0:
            print(f'   p0                = {p0}')
            print(f'   sqrtPriceLimitX96 = {sqrtPriceLimitX96}')
            print(f'   ZeroForOne = {zeroForOne} && sqrtPriceLimitX96 > p0\n')
            sys.exit(0)
    if ZeroForOne == False:
        if sqrtPriceLimitX96 < p0:
            print(f'   p0                = {p0}')
            print(f'   sqrtPriceLimitX96 = {sqrtPriceLimitX96}')
            print(f'   ZeroForOne = {zeroForOne} && sqrtPriceLimitX96 < p0\n')
            sys.exit(0)

    
    # print statements
    print(f'\nAMOUNT: {inOutString} : {amountSpecified*1e-18}')
    print(F'\nPARAMS:')
    print(f'   tokenIn   : {tokenIn.symbol()}')
    print(f'   tokenOut  : {tokenOut.symbol()}')
    print(f'   zeroForOne: {zeroForOne} ')
    if 4 in PRINTS:
        print(F'\nPOOL [BEFORE]:')
        print(f'   slot0.tick         = {slot0["tick"]}')
        print(f'   slot0.sqrtPriceX96 = {p0} ')
        print(f'   sqrtPriceLimitX96  = {sqrtPriceLimitX96} ')
        print(f'   pool liquidity     = {liquidity}')

    
    #        ============= WHILE LOOP ==============

    # see swap(..) in pool contract
    exactInput = amountSpecified > 0 # print(F' exactInput: {exactInput}')
    
    slot0Start = slot0
    slot0['unlocked'] = False # see swap(..) in pool contract
    
    _feeGrowthGlobal0X128 = pool.feeGrowthGlobal0X128()
    _feeGrowthGlobal1X128 = pool.feeGrowthGlobal1X128()
    if zeroForOne:
        feeProtocol = slot0Start['feeProtocol'] % 16
        feeGrowthGlobalX128 = _feeGrowthGlobal1X128
    if not zeroForOne:
        feeProtocol = my_math.shift_uint8( slot0Start['feeProtocol']) 
        feeGrowthGlobalX128 = _feeGrowthGlobal0X128
        
        
    cache = {
            'liquidityStart': liquidity,
            'blockTimestamp': my_math._blockTimestamp(),
            'feeProtocol': feeProtocol,
            'secondsPerLiquidityCumulativeX128': 0,
            'tickCumulative': 0,
            'computedLatestObservation': False
    }
    
    state = {
            'amountSpecifiedRemaining': amountSpecified,
            'amountCalculated': 0,
            'sqrtPriceX96': slot0Start['sqrtPriceX96'],
            'tick': slot0Start['tick'],
            'feeGrowthGlobalX128': feeGrowthGlobalX128, 
            'protocolFee': 0,
            'liquidity': cache['liquidityStart']
    }



    #--------------------------------------- WHILE LOOP -----------------------------------------
    i = 1 # loop number
    
    while (abs(state['amountSpecifiedRemaining']) > 10 and state['sqrtPriceX96'] != sqrtPriceLimitX96):
        
        step = {}
        step['sqrtPriceStartX96'] = state['sqrtPriceX96']
  
        # Next Tick
        # *c,m1,m2,m3 are variables used to calculate tickNext value.
        # ...for troubleshooting or for learning how this value is calculated.
        ( c, m1, m2, m3, step['tickNext'], tb, init) = my_math.nextTick(
            state['tick'],
            tick_spacing,
            zeroForOne,
            pool
        )
        TickNextInfo = getTickInfo(pool, step['tickNext'], False) ; 
        step["initialized"] = TickNextInfo['initialized']
        
        print(f'\n---------[{i}] {inOutString}')
        print(f'state.tick: {state["tick"]} tickNext: {step["tickNext"]} [initialized: {step["initialized"]}]')
        print(f'init: {init}]')
        step['sqrtPriceNextX96'] = my_math.sqrtPatTick(step['tickNext'])

        # ensure that we do not overshoot the min/max tick, as the tick bitmap is not aware of these bounds
        if step['tickNext']  < MIN_TICK:
            step['tickNext'] = MIN_TICK
            print(f'   * adjusted tickNext')
        if step['tickNext']  > MAX_TICK:
            step['tickNext'] = MAX_TICK 
            print(f'   * adjusted tickNext')



        # sqrtPX96 Target
        if zeroForOne:
            targetCondition =  (step['sqrtPriceNextX96'] < sqrtPriceLimitX96)
        if zeroForOne == False:
            targetCondition = (step['sqrtPriceNextX96'] > sqrtPriceLimitX96)
                
        if targetCondition:
                sqrtRatioTargetX96 = sqrtPriceLimitX96
                targ_str = 'pLim '
        if targetCondition == False: 
                sqrtRatioTargetX96 = step['sqrtPriceNextX96']  
                targ_str = 'pNext'

        # check our zeroForOne matches computeSwapSteps method
        zeroForOne_ = state['sqrtPriceX96'] >= sqrtRatioTargetX96
        if zeroForOne_ != zeroForOne:
            input(f'   zeroForOne out of alignment with computeSwapStep')
        
        # ComputeSwapStep(sqrtRatioTargetX96, state["sqrtPriceX96"], state["liquidity"], state["amountSpecifiedRemaining"])
          
        # SWAP STEP          
        if 3 in PRINTS:
            print(f'\n   [Swap Step] INPUTS:')
            print(f'      sqrtRatioCurrentX96 = {state["sqrtPriceX96"]}')
            print(f'      sqrtRatioTargetX96  = {sqrtRatioTargetX96}')
            print(f'      liquidity           = {state["liquidity"]}')
            print(f'      amountRemaining     = {state["amountSpecifiedRemaining"]}')
            print(f'      c_step zeroForOne   = {sqrtPriceLimitX96 < slot0["sqrtPriceX96"]}')
        # compute values to swap to the target tick, price limit, or point where input/output amount is exhausted
        (state['sqrtPriceX96'], 
         step['amountIn'], 
         step['amountOut'], 
         step['feeAmount'], 
         amountRemainingLessFee) = my_math.computeSwapStep(
            state['sqrtPriceX96'],
            sqrtRatioTargetX96,
            state['liquidity'],
            state['amountSpecifiedRemaining'],
            fee)

        if 3 in PRINTS:
            print(f'   [Swap Step] OUTPUTS:')
            print(f'      sqrtPriceX96       : {state["sqrtPriceX96"]}')
            print(f'      step.amountIn      : {step["amountIn"]} ')
            print(f'      step.amountOut     : {step["amountOut"]} ')
            print(f'      step.feeAmount     : {step["feeAmount"]} ')
            print(f'      amountRem. LessFee : {amountRemainingLessFee} ')
            time.sleep(2)

        
        #--- calculate amounts
        x0 = state['amountSpecifiedRemaining'] 
        c0 = state['amountCalculated']
        if exactInput:
            state['amountSpecifiedRemaining'] = x0 - (step['amountIn']  + step['feeAmount'])
            state['amountCalculated'] = c0  - step['amountOut']
        else:
            state['amountSpecifiedRemaining'] = x0 + step['amountOut']
            state['amountCalculated'] = c0 + step['amountIn'] + step['feeAmount']

        #------ print prices/ ticks
        if 1 in PRINTS:
            print(f'   state.p       = {state["sqrtPriceX96"]} ')
            print(f'   step.pNext    = {step["sqrtPriceNextX96"] } ')
            print(f'   target        = {sqrtRatioTargetX96}  [{targ_str}]')
            print(f'   pLimit        = {sqrtPriceLimitX96} ')
        if 2 in PRINTS:  
            print(f'   step.amountIn     : {step["amountIn"]} ')
            print(f'   step.amountOut    : {step["amountOut"]} ')
            print(f'   step.feeAmount    : {step["feeAmount"]} ')
            print(f'   amountRemaining   : {state["amountSpecifiedRemaining"]} ')
            print(f'   amountCalculated  : {state["amountCalculated"]*1e-18} ')
        time.sleep(0.5)


        # if the protocol fee is on, calculate how much is owed, decrement feeAmount, and increment protocolFee
        fa0 = step['feeAmount'] 
        pf0 = state['protocolFee']
        if cache['feeProtocol'] > 0:
            delta = fa0 / pf0
            step['feeAmount']    = fa0 - delta
            state['protocolFee'] = pf0 + delta # !! uint128(delta) !!
            input('!! uint128(delta) !!')

        # update global fee tracker
        if state['liquidity'] > 0:
            fgG = state['feeGrowthGlobalX128']
            feeAddAmount = int(step['feeAmount']*Q128 / state['liquidity'])
            feeAddAmountCheck = my_math.MulDiv(step['feeAmount'], Q128, state['liquidity'] )
            state['feeGrowthGlobalX128'] = fgG + feeAddAmount
            TickNextInfo  = getTickInfo(pool, step['tickNext'], False)
            StateTickInfo = getTickInfo(pool, state['tick'], False)

            if 6 in PRINTS:
                print(f'\n      FEE GROWTH FORECAST')
                print(f'         fgG                : {_feeGrowthGlobal0X128}')
                print(f'         state.fgG [before] : {fgG}')
                print(f'         state.fgG [after]  : {state["feeGrowthGlobalX128"]} <----')
                print(f'             *added amount  : {feeAddAmount}')
                #print(f'             *mulDiv check  : {feeAddAmountCheck}')
                print(f'         tickNext.fGOut      : {TickNextInfo["feeGrowthOut0"]}')
                    
        # shift tick if we reached the next price
        if state['sqrtPriceX96'] == step['sqrtPriceNextX96']:
            print(f'      *shift tick {step["tickNext"]} :: {step["initialized"]}:')
            time.sleep(2)
            # if the tick is initialized, run the tick transition
            if step['initialized']: 
                #--- TICK CROSS
                if 6 in PRINTS:
                    print(f'      *tick cross:')
                    
                    # info.feeGrowthOutside0X128 = feeGrowthGlobal0X128 - info.feeGrowthOutside0X128;
                    # info.feeGrowthOutside1X128 = feeGrowthGlobal1X128 - info.feeGrowthOutside1X128;
                    
                    if zeroForOne:
                        print(f'         NewfeeGrowthOut [Next] : {state["feeGrowthGlobalX128"] - TickNextInfo["feeGrowthOut0"]}')
                    if zeroForOne == False:
                        print(f'         NewfeeGrowthOut [Next] : {_feeGrowthGlobal0X128 - TickNextInfo["feeGrowthOut0"]}')
                        
                #--- OBSERVATION
                getObservation = False 
                if getObservation:
                    #--- OBSERVATION
                    # check for the placeholder value, which we replace with the actual value the first time the swap
                    # crosses an initialized tick
                    secondsAgo = [cache['blockTimestamp']]
                    if not cache['computedLatestObservation']:
                        # a python script runs much slower than a solidity function call, so we may catch an error
                        # if our deadline passes
                        try:
                            (cache['tickCumulative'], cache['secondsPerLiquidityCumulativeX128']) = pool.observe(secondsAgo)
                            cache['computedLatestObservation'] = True
                        except Exception as e:
                            if 4 in PRINTS:
                                print(f'      [observe revert:  {e}]')  
                    if 5 in PRINTS:         
                        print(f'     OBSERVATION')
                        print(f'         secondsAgo : {secondsAgo}')
                        print(f'         tickCum    : {cache["tickCumulative"]}')
                        print(f'         sPerLCum   : {cache["secondsPerLiquidityCumulativeX128"]}')

                #--- LIQUIDITY
                        
                liquidityNet = TickNextInfo['liqNet']
                # if we're moving leftward, we interpret liquidityNet as the opposite sign
                # safe because liquidityNet cannot be type(int128).min
                if zeroForOne: 
                    liquidityNet = -liquidityNet
                state['liquidity'] = state['liquidity'] + liquidityNet
                if 4 in PRINTS or 6 in PRINTS:
                    print(f'      added {liquidityNet} liquidity')
                    print(f'      state.liquidity = {state["liquidity"]}')
                #time.sleep(0.5)
            
            
            #--- TICK
            t0 = state['tick']
            if zeroForOne:
                state['tick'] = step['tickNext'] - 1
            if not zeroForOne:
                state['tick'] = step['tickNext']
            stateTick = state["tick"]
            if 4 in PRINTS:
                print(f'      state.tick = {t0} ---> state.tick = {stateTick} [{my_math.sqrtPatTick(stateTick)}]')
                
        #--------   
        if state['sqrtPriceX96'] != step['sqrtPriceNextX96']:
            state['tick'] = my_math.tickAtSqrt(state['sqrtPriceX96'])
        
        if state['amountSpecifiedRemaining'] <= 10:
            terminateString = 'amountRemaining = 0'
        if state['sqrtPriceX96'] == sqrtPriceLimitX96:
            terminateString = 'sqrtPrice = Limit'
        if state['sqrtPriceX96'] == sqrtPriceLimitX96 and state['amountSpecifiedRemaining'] == 0:
            terminateString = 'amountRemaining = 0 sqrtPrice = Limit'
        
        i+=1
                    
    #---------------------------------------
    
    print(F'\n\n======== END WHILE LOOP ({terminateString}) ')
    

    # calculate amount
    amountCondition = ( zeroForOne == exactInput )
    if amountCondition:
        X = amountSpecified - state['amountSpecifiedRemaining']
        Y = state['amountCalculated']
    if not amountCondition:
        Y = amountSpecified - state['amountSpecifiedRemaining']
        X = state['amountCalculated']

    if 4 in PRINTS:
        #------ print prices/ ticks
        print(f'   state.liquidity = {state["liquidity"]}')
        print(f'   state.tick = {state["tick"] }')
        print(f'   state.pX96 = {state["sqrtPriceX96"]} [{p_from_x96(state["sqrtPriceX96"])}]')
        print(f'   pLimit     = {sqrtPriceLimitX96} [{p_from_x96(sqrtPriceLimitX96)}]')

        print(f'\nAMOUNTS:')
        print(F'   amountCondition = {amountCondition}')
        print(F'   amountSpecified = {amountSpecified}')
        print(F'   amountSpecifiedRemaining = {state["amountSpecifiedRemaining"]}')
    
    print(F'   amount0 = {X} [{X*1e-18}]')
    print(F'   amount1 = {Y} [{Y*1e-18}]')


    if X == 0 and Y == 0:
        print(f'\nERROR!! X=Y=0')
        sys.exit(0)




    """    
    troubleShootTicks = False 
    if troubleShootTicks:
        
        # tickBit of tick0
        tick_spacing = int(pool.tickSpacing() )
        tick0 = slot0["tick"]
        compressed0   = tick0 / tick_spacing
        (wordPos0,  bitPos0) = my_math.position(compressed0)
        tickBit0   = pool.tickBitmap(wordPos0)

        
        (wordPos,  bitPos) = my_math.position(compressed)
        print(f'   wordPos  : {wordPos}')
        print(f'   bitPos   : {bitPos}')

        mostSigBit = my_math.mostSignificantBit(masked)
        print(f'   most significant bit: {mostSigBit}')
        leastSigBit = my_math.leastSignificantBit(masked)
        print(f'   least significant bit: {leastSigBit}')
        """
    



def main():
    whileLoop()
    print('\n=============== end whileLoop.py =====================\n')

