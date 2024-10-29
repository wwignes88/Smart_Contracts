
from scripts.Load.helpful_scripts import (approve_contract_spender,
                                          get_contract,
                                          time,
                                          getPosition,
                                          p_from_x96,
                                          MIN_TICK, MAX_TICK, Q96)
from scripts.Load.BrownieFuncs import getEvents
from scripts.Load.DICTS import TICK_SPACINGS
from scripts.Load.BrownieFuncs import getEvents, listenForEvent

# account: 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce
# accountII: 0x559B0cD29EaBfFC60ee204A78E16852A6D79F50f


def mint(pool, tick0, x, y, token0, token1, fee, tickLow, tickHigh, account):
    import sys
    
    #--------------  
    tick_spacing     = TICK_SPACINGS[fee]
    liquid           = get_contract('MliquidityMiner')
    ERC721ManagerII  = get_contract('MNonfungiblePositionManagerII')
    my_math          = get_contract('MyMath')

    mlApprove = False 
    if mlApprove:
        tx = liquid.MLApproval(token1,liquid.address, 2*y, {"from": account} )
        tx.wait(1)
  
    #------------- MINT 

    troubleShoot   = False # trigger revert options at specified points in contracts [see below to set option range]
    listenToEvents = False # will set option=50 which bypasses all state changing lines, but emits 
                           # events which give parameter values of interest.
    troubleshootLiquidity  = False  # check various parameters are within allowed range. 
                           # set to true for state changing mint transaction.
    # troubleShoot = listenToEvents = False will default to Option=0 which does the mint transaction
    # with state changes executed (so the real transaction -- no intentional reverts or bypasses)
    
#------------- LIQUIDITY MATH
    pA = my_math.sqrtPatTick(tickLow) 
    pB = my_math.sqrtPatTick(tickHigh) 
    p0 = my_math.sqrtPatTick(tick0)    
    
    if troubleshootLiquidity:
        
        print(f'\n      pLow : {pA} [{p_from_x96(pA)}]')
        print(f'      pHigh: {pB} [{p_from_x96(pB)}]')
        print(f'      p0   : {p0} [{p_from_x96(p0)}]')
        
        #----------- LIQUIDITY AMOUNT CHECKS
        # see LiquidityAmounts.sol in v3-periphery
        print(f'\n   L AMOUNTS:')
        if p0<pA:
            intermediate, L, L_for_0  = my_math.LForZero(pA, pB, x)
            if L_for_0 == 0:
                print(F'      L_for_0 = 0 !!!')
                print(f'         intermediate =  {intermediate}')
                print(f'         L            =  {L}')
            print(f'      L_for_0  : {L_for_0*1e-18} Wei ')
        if pA<p0 and p0<pB:
            intermediate, L, L_for_0   = my_math.LForZero(pA,pB,x)
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

    # ----------- VARIOUS CHECKS ON TICKS:
    
    # see LiquidityAmounts.sol library. if tick0<tickLow we use getLiquidityForAmount0
    # ... but this will calculate 'intermediate' value of 0 if pA*pB/Q96 < 0.01 which leads to L=0
    if tick0 < tickLow:
        mark = 0.01
        if pA*pB/Q96 <= 0.5:
            print(f'\npA*pB/Q96 < {mark} !!\n')
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

    #------------- APPROVAL
    # approve liquid.sol to transfer my tokens to itself (see mintNewPosition function).
    L_x_allowed = approve_contract_spender(2*x, token0, liquid, account, 'Liquid Miner')
    L_y_allowed = approve_contract_spender(2*y, token1, liquid, account, 'Liquid Miner')

    #------------- EVENT LISTENER
    Option = 0 # default value -- presumes troubleShoot=False and listenToEvents=False
    if listenToEvents:
        Option = 50 # int8 variables used to bypass state changing events (set to zero if you want the real transaction)
        eventToken = token1
        
        listenForEvent([#[pool, "modifyAmounts"],
                        [ERC721ManagerII,"MintPayAmounts"],
                         #[eventToken, "Approval"],
                         #[eventToken, "Transfer"],
                         [eventToken, "transferFromParams"]])
        
    #------------ MINT
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

    if troubleShoot:
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

    if not troubleShoot:
        print(f'\n----------- minting {token0.symbol()}/ {token1.symbol()} pool...')
        tx = liquid.mintNewPosition(
                                mintParams,
                                Option,
                                {'from': account}
                            )
        tx.wait(1)
        
        #getEvents(tx)
        if Option < 50:
            mytokenIds = liquid.getTokenIds(account.address)
            tokenId    = mytokenIds[0]
            print(f'my tokensIds: {mytokenIds}')


        




