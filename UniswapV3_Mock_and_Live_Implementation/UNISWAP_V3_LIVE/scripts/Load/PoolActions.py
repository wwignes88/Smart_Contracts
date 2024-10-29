
from scripts.Load.helpful_scripts import (approve_contract_spender,
                                          get_contract_from_abi,
                                          time,
                                          getslot0,
                                          p_from_x96,
                                          MIN_TICK, MAX_TICK, Q96)
from scripts.Load.DICTS import TICK_SPACINGS
#from scripts.Load.BrownieFuncs import listenForEvent, getEvents

# account: 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce
# accountII: 0x559B0cD29EaBfFC60ee204A78E16852A6D79F50f


def mint_to_pool(pool, x, y, token0, token1, fee, tickLow, tickHigh, account):
    print(f'\n   ======mint :: PoolAxtions.py')
    import sys
    
    #--------------  
    tick_spacing     = TICK_SPACINGS[fee]
    liquid           = get_contract_from_abi('LiquidityMiner')
    my_math          = get_contract_from_abi('MyMath')

    #------------- APPROVAL
    print(F'\nAPPROVALS:')
    # approve liquid.sol to transfer my tokens to itself (see mintNewPosition function).
    L_x_allowed = approve_contract_spender(x, token0, liquid, account, 'Liquid Miner')
    L_y_allowed = approve_contract_spender(y, token1, liquid, account, 'Liquid Miner')

    #------------- EVENT LISTENER
    Option = 0 # default value -- presumes troubleShoot=False and listenToEvents=False
    """ 
    LISTEN_TO_EVENTS = False
    if LISTEN_TO_EVENTS:
        Option = 50 # int8 variables used to bypass state changing events (set to zero if you want the real transaction)
        eventToken = token1
        
        listenForEvent([#[pool, "modifyAmounts"],
                        [ERC721Manager,"MintPayAmounts"],
                         #[eventToken, "Approval"],
                         #[eventToken, "Transfer"],
                         [eventToken, "transferFromParams"]])
    """
        
    #------------ MINT PARAMS
    mintParams = (token0,
                token1,
                x,
                y,
                0, # Amount0Min
                0, # Amount1Min
                tickLow,
                tickHigh,
                fee
            )

    #------------- TROUBLESHOOT
    TROUBLESHOOT= False
    # see LIquidityAmounts.sol in v3-periphery contracts. this will help troubleshoot by emulating v3 liquidity calculations.
    if TROUBLESHOOT:
        print(f'\n\nTROUBLSHOOT:')

        SLOT0 = getslot0(pool, True) 
        tick0 = SLOT0['tick']

        pA = my_math.sqrtPatTick(tickLow) 
        pB = my_math.sqrtPatTick(tickHigh) 
        p0 = my_math.sqrtPatTick(tick0)    
        print(f'\n      pLow : {pA} [{p_from_x96(pA)}]')
        print(f'      pHigh: {pB} [{p_from_x96(pB)}]')
        print(f'      p0   : {p0} [{p_from_x96(p0)}]')
        
        #----------- LIQUIDITY AMOUNT CHECKS
        # see LiquidityAmounts.sol in v3-periphery
        print(f'\n   L AMOUNTS:')
        if p0<pA:
            intermediate, L, L_for_0 = my_math.LForZero(pA, pB, x)
            if L_for_0 == 0:
                print(F'      L_for_0 = 0 !!!')
                print(f'         intermediate =  {intermediate}')
                print(f'         L            =  {L}')
            print(f'      L_for_0  : {L_for_0*1e-18} Wei ')
        if pA<p0 and p0<pB:
            intermediate, L, L_for_0 = my_math.LForZero(pA,pB,x)
            L_for_1  = my_math.LForOne(pA,pB,y)
            print(f'      L_for_0  : {L_for_0}  int.: {intermediate} ')
            print(f'      L_for_1  : {L_for_1}  ')
        if pB<p0:  
            L_for_1  = my_math.LForOne(pA,pB,y)
            print(f'      L_for_1  : {L_for_1}   ')
        
        LForAmounts = my_math.LForAmounts(p0,pA,pB,x,y)
        print(f'   LForAmounts: {LForAmounts} Wei\n')
        
        if LForAmounts == 0:
            print(f'\attempting to mint zero liquidity (must be non-zero)')
            sys.exit(0)

        # check ticks are within valid range
        if abs(tickLow) > abs(MIN_TICK) or abs(tickHigh) > abs(MIN_TICK) :
            print(f'\n   *ticks out of range!! |TICK| > {abs(MIN_TICK)} \n')
            print(f'      tickLow  : {tickLow} ')
            print(f'      tickHigh : {tickHigh} ')
            sys.exit(0)
        
        # check tick is divisible by tick_spacing 
        if abs(tickLow) % tick_spacing != 0 or abs(tickHigh) % tick_spacing != 0 :
            print('/n   !! need to adjust tick high/low !!')
            print(f'      tickLow  % {tick_spacing} : {tickLow % tick_spacing} ')
            print(f'      tickHigh % {tick_spacing} : {tickHigh % tick_spacing} ')
            sys.exit(0)


        # !! only good for mock!!!
        # intentionally trigger revert (to see how far into call a given transaction goes)
        REVERT_CALL = False
        if REVERT_CALL:
            # transaction will revert at a specified point for each option in a while loop
            # which utilizes the try/except method.
            
            # CONTRACT :: FUNCTION :: OPTIONS
            # LMiner :: mintNewPosition 1-2
            #       MNonfung   :: 
            #         MNonfungII   :: 3-4 
            #           MLmanager :: addLiquidity 5
            #               poolII :: mintII
            #                   pool :: _modify   21-22
            #                   pool :: _update   31-34
            #               poolII :: mintII  7                     
            #                   MLmanager :: uniswapV3MintCallback 8-9
            #       >> ERC721 mint
            #       MNonfung   :: mint 10
            #           MNonfungII :: mappoolkey 11-12
            # LMiner :: mintNewPosition 13-15
            i = 7  ;  iMax = 10
            while i <= iMax:
                print(f'\n----------- minting {token0.symbol()}/ {token1.symbol()} pool...')
                try: 
                    option = i
                    mint_params = liquid.mintNewPosition(mintParams,
                                                        option,
                                                        {'from': account})
                    i = iMax
                except Exception as e:
                    print(f'    mint{i} failed {e}')
                i += 1
                time.sleep(2)
            import sys
            sys.exit(0)

        if not REVERT_CALL:
            print(f'\n----------- minting {token0.symbol()}/ {token1.symbol()} pool...')
            tx = liquid.mintNewPosition(
                                    mintParams,
                                    Option,
                                    {'from': account}
                                )
            tx.wait(1)

        if Option < 50:
            mytokenIds = liquid.getTokenIds(account.address)
            tokenId    = mytokenIds[0]
            print(f'my tokensIds: {mytokenIds}')

    # ----------- MINT TX
    if not TROUBLESHOOT:
        print(f'\n----------- minting liquidity position...')
        tx = liquid.mintNewPosition(
                                mintParams,
                                Option,
                                {'from': account}
                            )
        tx.wait(1)





        




