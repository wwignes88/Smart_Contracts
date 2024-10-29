
from scripts.Load.helpful_scripts import (  sys,
                                            time,
                                            get_contract,
                                            approve_contract_spender,
                                            get_accounts,
                                            get_Token_bal,
                                            getERC20,
                                            loadPool,
                                            getslot0,
                                            p_from_x96,
                                            gas_controls, 
                                            MAX_SQRT_RATIO,
                                            MIN_SQRT_RATIO,
                                            MIN_SQRT_RATIO, MAX_SQRT_RATIO)
from scripts.Load.DICTS import *
from scripts.Load.BrownieFuncs import getEvents, listenForEvent


def swap_():
    account = get_accounts(0) 
    gas_controls(account, set_gas_limit=False, priority_fee=False)
    
    print('\n=============== swap.py =====================\n')
    
    my_math   = get_contract('MyMath')
    swapper   = get_contract('MSwapper')
    router    = get_contract('MSwapRouter')
    

    # --------- set tokens

    t0 = 'weth' 
    t1 = 'sand' 
    t2 = 'link'

    token0 = get_contract(t0)
    token1 = get_contract(t1)
    token2 = get_contract(t2)
    fee = 3000
    
    # swap amount
    amountIn = 3*1e18

    # 1 = multihop, 2 = exact single swaps
    SWAP_OPTION  = [1] 
    troubleshoot = False ; TroubleshootFirstPool = True

    # -------------  MULTI-HOP SWAPS
    if 1 in SWAP_OPTION:
        
        #    ============ SET PARAMETERS ===============
        
        InputSwap      =   False  # True = exactInput, False = exactOutput
        amount         =   0.1e18
        amountInMax    =   2206835969487227177*2 # for output swaps
        amountOutMin   =   0
        
        # Payment
        payAmount      =   2206835969487227177 
        transferToken  =   token0
        approvalAmount =   payAmount*2
        
        # event listening/ troubleshooting
        option         =   0
        listenForSpecificEvents = True # if False will instead print tx.events (in a readable format)
                # ROUTER:
                #    20: exactIn/OutInternal
                # POOL:
                #    0 : Swap
                #    20: SwapAmounts
                #    21: SteppedAmounts
                #    22: SteppedPrices
                #    23: SwapStepAmounts
        poolToListenTo = 3

        #     ==========================================
        
        if InputSwap:
            swapString    = print(f'\n========= MULTI-HOP INPUT [amount = {amount*1e-18}]:')

        if InputSwap == False:
            swapString    = print(f'\n========= MULTI-HOP OUTPUT  [amount = {amount*1e-18}]:')
        print(f'   amount   : {amount*1e-18} {token2.symbol()}')
        print(f'   payAmount: {payAmount*1e-18} {transferToken.symbol()}')
        
        # event listener
        if listenForSpecificEvents:
            if poolToListenTo == 1:
                (pool, slot0, liquidity, tick_spacing) = loadPool(token0, token1, fee, account)
                
            if poolToListenTo == 2:
                (pool, slot0, liquidity, tick_spacing) = loadPool(token1, token2, fee, account)
            if poolToListenTo in [1,2]:
                poolToken0 = getERC20(pool.token0())
                poolToken1 = getERC20(pool.token1())
                print(f'   *listening to pool {poolToListenTo}: {pool.address}')
                print(f'   token0 = {poolToken0.symbol()}: {poolToken0}')  
                print(f'   token1 = {poolToken1.symbol()}: {poolToken1}')  
                
                eventOptions = {0:  [],
                                20: [[pool, "SwapAmounts"]],
                                21: [[pool,"SteppedAmounts"]],
                                22: [[pool,"SteppedPrices"]],
                                23: [[pool,"SwapStepAmounts"]]
                                }
                eventList = eventOptions[option]
                
            if poolToListenTo == 3:
                print(f'   *listening to pool router: {router.address}')
                if InputSwap:
                    inOutEvent = "exactInInternal"
                if InputSwap==False:
                    inOutEvent = "exactOutInternal"  
                eventList  =   [#[router, inOutEvent],
                                [router,"SwapCallback"],
                                [router,"paidInexact"],
                                [router,"paidExact"]]
            
            listenForEvent( eventList)
        
        # approve MSwapper.sol to take my money  
        if option < 20:
            balIn0  = get_Token_bal(transferToken, account.address, 'my [transferToken] ', True, True, account)
            approve_contract_spender(approvalAmount, transferToken, swapper, account, 'swapper')

        if troubleshoot:

            # for troubleshooting; set option parameter value(s) to trigger a revert statement
            # at a specified location in the call. This lets you know [about] where
            # the call is reverting.

            # [CONTRACT] :: [FUNCTION] [OPTION VALUE(S)]
            # Swapper :: swapExact 1-2
                # Router :: exactInput
                        # Router :: exactInput/OutputInternal 4 , -4
                            # pool :: swap          5-8     
                                # pool :: _modify   21-22   
                                # pool :: _update   31-34   
                            # pool :: callbacks     9        
                                # Router :: cllbck  10-11                                 
            
            
            i = 10 ;  iMax = 11; inc = 1
            while i <= abs(iMax):
                
                try: 
                    option = i
                    if InputSwap:
                        print(F'\n-----------INPUT SWAP({i})')
                        tx = swapper.MultiHop_Input(
                                amount, 
                                amountOutMin,
                                token0,
                                token1,
                                token2,
                                option,
                                        {"from": account})

                    if InputSwap==False:
                        print(F'\n-----------OUTPUT SWAP({i})')
                        tx = swapper.MultiHop_Output(
                                        amount, 
                                        amountInMax,
                                        payAmount,
                                        token0,
                                        token1,
                                        token2,
                                        transferToken,
                                        option,
                                        {"from": account})
                    tx.wait(1)
                    i = iMax
                except Exception as e:
                    print(f'    swap{i} failed {e}')
                i += inc
                time.sleep(2)
            sys.exit(0)
            #----------------------------------------
            
        if troubleshoot == False:  
            if InputSwap:
                tx = swapper.MultiHop_Input(
                                amount, 
                                amountOutMin,
                                token0,
                                token1,
                                token2,
                                option,
                                {"from": account})

            if InputSwap==False:
                tx = swapper.MultiHop_Output(
                                amount, 
                                amountInMax,
                                payAmount,
                                token0,
                                token1,
                                token2,
                                transferToken,
                                option,
                                {"from": account})
            tx.wait(1)

            if listenForSpecificEvents == False:
                print(f'\nGET EVENTS:')
                getEvents(tx)


    # -------------- SINGLE SWAPS
    if 2 in SWAP_OPTION:

        #    ============ SET PARAMETERS ===============

        InputSwap           = False  # True = exactInputSingle, False = exactOutputSingle
        poolNum             = 1     # 1 = token0/token1 pool, 2 = token1/token2 pool
        ZeroForOne          = True # True: swap token0 for token1. False: opposite.
        sqrtPriceLimitX96   = 0
                # [see below] sqrtPriceLimitX96 == 0
                #    ? (zeroForOne ? TickMath.MIN_SQRT_RATIO + 1 : TickMath.MAX_SQRT_RATIO - 1)
                #    : sqrtPriceLimitX96,


        approvalAmount      = 50*1e18 # approve Router to spend approvalFactor*amountSpecified
        𐤃deadline           = 20 # additional seconds added to block.timestamp() for deadline [see deadline below]
        recipient           = account.address
        fee                 = 3000
        option              = 20
        listenForSpecificEvents = True # if False will instead print tx.events (in a readable format)
                            # ROUTER:
                            #    20: exactIn/OutInternal
                            # POOL:
                            #    0 : Swap
                            #    20: SwapAmounts
                            #    21: SteppedAmounts
                            #    22: SteppedPrices
                            #    23: SwapStepAmounts
        printPoolParams     = False
        
        # amounts
        amount        = 15743797125439218009
        amountMinMax  = 0
        
        #            ============================================
        
        # set pool tokens
        if poolNum == 1:
            (tokenIn, tokenOut) = (token0, token1)
        if poolNum == 2:
            (tokenIn, tokenOut) = (token1, token2)

        # Load pool 
        (pool, slot0, liquidity, tick_spacing) = loadPool(tokenIn, tokenOut, fee, account)

        # event listener
        if listenForSpecificEvents:
            eventOptions = {0:  [[pool,"Swap"],
                                 [router, "exactInInternal"],
                                 [router, "exactOutInternal"]],
                            20: [#[router, "exactOutInternal"],
                                 [pool,"SwapAmounts"]],
                                 #[router, "exactInInternal"]],
                            21: [[pool,"SteppedAmounts"]],
                            22: [[pool,"SteppedPrices"]],
                            23: [[pool,"SwapStepAmounts"]]
                             }
            eventList = eventOptions[option]
            listenForEvent( eventList)
            
        
        # adjust tokenIn/tokenOut to be in line with ZeroForOne, if needed
        # (see router :: exactIn/OutputInternal -- this mocks the bahavior of this function)
        zeroForOne = my_math.getZeroForOne(tokenIn, tokenOut)
        if zeroForOne != ZeroForOne:
            print(f'   *re-ordered tokens')
            (tokenIn, tokenOut) = (tokenOut, tokenIn) 
            zeroForOne = my_math.getZeroForOne(tokenIn, tokenOut)

        # set sqrtPriceLimitX96 to min/max (see router :: exactOutputInternal)
        if sqrtPriceLimitX96==0:
            if zeroForOne:
                sqrtPriceLimitX96 = MIN_SQRT_RATIO+1
            if zeroForOne==False:
                sqrtPriceLimitX96 = MAX_SQRT_RATIO-1
                
        # tick of sqrtPriceLimitX96
        tickLimit = my_math.tickAtSqrt(sqrtPriceLimitX96)
        

        # *Check priceLimit is valid.
        p0 = slot0["sqrtPriceX96"]
        tick0 = slot0["tick"]
        if ZeroForOne:
            if sqrtPriceLimitX96 >= p0 or  sqrtPriceLimitX96 <= MIN_SQRT_RATIO:
                print(f'   REQUIRED: pLimit < p0 & pLimit > pMin')
                print(f'      sqrtPriceLimitX96 = {sqrtPriceLimitX96} ')
                print(f'      p0                = {p0}')
                print(f'      tickLimit         = {tickLimit}')
                print(f'      tick0             = {tick0}')
                sys.exit(0)
        if ZeroForOne == False:
            if sqrtPriceLimitX96 <= p0 or  sqrtPriceLimitX96 >= MAX_SQRT_RATIO:
                print(f'   REQUIRED: pLimit > p0 & pLimit < pMax')
                print(f'      sqrtPriceLimitX96 = {sqrtPriceLimitX96} ')
                print(f'      p0                = {p0}')
                print(f'      tickLimit         = {tickLimit}')
                print(f'      tick0             = {tick0}')
                sys.exit(0)



        print(F'\nPARAMS:')
        print(f'   tokenIn   : {tokenIn.symbol()}')
        print(f'   tokenOut  : {tokenOut.symbol()}')
        print(f'   zeroForOne: {zeroForOne} ')
        #print(f'   𐤃deadline : {𐤃deadline}')

        if printPoolParams:
            print(F'\nPOOL STATE [BEFORE]:')
            print(f'   slot0.tick         = {slot0["tick"]}')
            print(f'   slot0.sqrtPriceX96 = {slot0["sqrtPriceX96"]} ')
            print(f'   sqrtPriceLimitX96  = {sqrtPriceLimitX96} ')
            print(f'   pool liquidity     = {liquidity}')
        
        # Get Inital Balances
        balIn0  = get_Token_bal(tokenIn, account.address, 'my [In] ', False, True, account)
        balOut0 = get_Token_bal(tokenOut, account.address, 'my [Out]', False, True, account)
        
        # set parameters for Exact Input/ Output swaps
        deadline          = my_math._blockTimestamp() + 𐤃deadline
        ExactSingleParams = (
            tokenIn,       # tokenIn
            tokenOut,      # tokenOut
            fee,   
            recipient,     # recipient
            deadline,      # deadline
            amount,        # amount In/Out
            amountMinMax,  # amount Out/In Minimum
            sqrtPriceLimitX96, # sqrtPriceLimitX96
        )
        

        
        # troubleshooting
        if troubleshoot:
            #Payment : approve Router to make payment [to pool]
            approve_contract_spender(approvalAmount, tokenIn, router, account, 'router')
            
            #-----------------------------------------------
            # for troubleshooting; set option parameter value(s) to trigger a revert statement
            # at a specified location in the call. This lets you know [about] where
            # the call is reverting.

            # [CONTRACT] :: [FUNCTION] [OPTION VALUE(S)]
            # Swapper :: swapExact 1-2 [ not relevant to single swaps]
                # Router :: exactInputInternal 4 
                    # pool :: swap          5-8    
                        # pool :: _modify   21-22   
                        # pool :: _update   31-34   
                    # pool :: callbacks     10         
                        # Router :: cllbck  11-13                                      
            
            
            i = 11 ;  iMax = 14; inc = 1
            while i <= abs(iMax):
                try: 
                    revert_option = i
                    if InputSwap:
                        print(F'\n-----------EXACT SINGLE SWAP ({i})')
                        tx = router.exactInputSingle(
                                        ExactSingleParams,
                                        revert_option, 
                                        {"from": account})

                    if InputSwap==False:
                        print(F'\n-----------EXACT OUT SWAP ({i})')
                        tx = router.exactOutputSingle(
                                        ExactSingleParams,
                                        revert_option, 
                                        {"from": account})
                    tx.wait(1)
                    i = iMax
                except Exception as e:
                    print(f'    swap{i} failed {e}')
                i += inc
                time.sleep(2)
            sys.exit(0)
            #-----------------------------------------------
         
        if troubleshoot == False:   

            # Payment : approve Router to make payment [to pool]
            if option < 20:
                approve_contract_spender(approvalAmount, tokenIn, router, account, 'router')
                
            # Execute exact single swap
            if InputSwap:
                print(f'\nSWAPPING [SINGLE INPUT, amount = {amount*1e-18}]...')
                tx = router.exactInputSingle(
                                ExactSingleParams,
                                option, 
                                {"from": account})

            if InputSwap==False:
                print(f'\nSWAPPING [SINGLE OUTPUT, amount = {amount*1e-18}]...')
                tx = router.exactOutputSingle(
                                ExactSingleParams,
                                option, 
                                {"from": account})
            
            tx.wait(1)

            if listenForSpecificEvents == False:
                #print(F'\nPOOL [AFTER]:')
                #slot0 = getslot0(pool, False)
                #print(f'   slot0.tick         = {slot0["tick"]}')
                #print(f'   slot0.sqrtPriceX96 = {slot0["sqrtPriceX96"]} [{p_from_x96(slot0["sqrtPriceX96"])}]')
                #print(f'   sqrtPriceLimitX96  = {sqrtPriceLimitX96} [{p_from_x96(sqrtPriceLimitX96)}]')
                #print(f'   pool liquidity     = {pool.liquidity()}')
                
                getEvents(tx)
                        
        get𐤃s = False 
        if get𐤃s:
            print('\n')
            balIn1   = get_Token_bal(tokenIn, account.address, '[In]  my', True, True, account)
            balOut1  = get_Token_bal(tokenOut, account.address, '[Out] my', True, True, account)
            𐤃In  = balIn0  - balIn1
            𐤃Out = balOut0 - balOut1
            print(f'    𐤃In  = {𐤃In*1e-18} Wei')
            print(f'    𐤃Out = {𐤃Out*1e-18} Wei')
    
                

def main():
    swap_()
    print('\n=============== end swap.py =====================\n')

