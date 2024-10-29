from scripts.Load.helpful_scripts import (loadPool, 
                                          get_contract, 
                                          get_Token_bal, 
                                          get_accounts,
                                          getNextTick,
                                          getTickInfo,
                                          time,
                                          gas_controls,
                                          getERC20,
                                          p_from_x96,
                                          MIN_TICK, MAX_TICK, Q96)
from scripts.Load.PoolActions import mint
import sys



def mint_(poolnum):
    print(f'\n\n\n======= MINTING TO POOL {poolnum}:')
    
    account = get_accounts(0) 
    gas_controls(account, set_gas_limit=False, priority_fee=False)
    my_math = get_contract('MyMath')
    
    t0 = 'weth' 
    t1 = 'sand' 
    t2 = 'link' 

    token0 = get_contract(t0)
    token1 = get_contract(t1)
    token2 = get_contract(t2)
            
    # Load pool 
    fee = 3000
    if poolnum == 1:
        (pool, slot0, liquidity, tick_spacing) = loadPool(token0, token1, fee, account)
    if poolnum == 2:
        (pool, slot0, liquidity, tick_spacing) = loadPool(token1, token2, fee, account)
    
    Lpool0 = pool.liquidity()
    tick0  = slot0['tick']
    
    # *Note: if (TokenA , TokenB) = (token1, token0) [tokens are out of order compared to 
    # [pool.token0(), pool.token1()] mint will 'M1' error.
    # This comes from MUniswapV3PoolII.sol :: mintII function. See also MPeripheryPayments.sol :: pay.
    # why this happens I am unsure, but I believe it to be related to the tok0, tok1 declarations in 
    # the PoolII contract which in the case of unordered tokens would not align with the passed parameters.
    # Still though, both tokens get paid. If amount0=amount1 then I fail to see why it would matter if one gets
    # paid before the other.
    TokenA = getERC20(pool.token0())
    TokenB = getERC20(pool.token1())
    print(f'      {TokenA.symbol()}/  {TokenB.symbol()} pool')
    #sys.exit(0)
    
    #            ==============  SET MINT AMOUNTS ==========
    x = 25*1e18
    y = 25*1e18

    # view next numTicksToView ticks then exit (do not mint)
    # zeroForOne will set the direction of nextTick. 
    # xxx  viewNextTicks  = False ; numTicksToView = 5
    zeroForOne     = False
    printTicks     = False

    # set tick range to mint liquidity to
    # ticks should be within range (abs(tick) < MAX_TICK = 887272 and divisible by tick spacing.

    # get token balances. will mint if needed.
    getTokenBals = True 
    if getTokenBals:
        #print(f'\n--------- Balances Before:')
        # check my balance/ mint if needed
                                                                #  PRINT=False, MINT=True
        myBalance0 =  get_Token_bal(token0, account.address, 'my', False, True, account)
        myBalance1 =  get_Token_bal(token1, account.address, 'my', False, True, account)
        myBalance2 =  get_Token_bal(token2, account.address, 'my', False, True, account)

    # set tickLow/ tickHigh values
    if  poolnum == 1:
        tickLow  = -92160  
        tickHigh = -15360
    if  poolnum == 2:
        tickLow  = 15300   
        tickHigh = 92100
    
    # view next ticks, or get next tick.
    """
    if viewNextTicks:

      tick0: 0
         [1] tickNext: 15300 [170254363637599206452736906702 = 4.617823568835026]
         [2] tickNext: 30660 [366960854187076154106862038914 = 21.452618450736843]
         [3] tickNext: 46020 [790935783545285935724471811934 = 99.66055037243372]
         [4] tickNext: 61380 [1704757895983847518230427316680 = 462.98428899691044]
         [5] tickNext: 76740 [3674381086783737467105769802518 = 2150.845555808464]
         [6] tickNext: 92100 [7919644427352728073180036292043 = 9991.99479309306]
        Tick0 = tick0
        print(f'\n      tick0: {Tick0}')
        i = 1
        while i < 8:
            tickNext, NextInitialized = getNextTick(pool, Tick0, tick_spacing, zeroForOne)
            pNext = my_math.sqrtPatTick(tickNext)
            PNext = p_from_x96(pNext)
            print(f'         [{i}] tickNext: {tickNext} [{pNext} = {PNext}]')
            Tick0 = tickNext
            i += 1
        sys.exit(0)
        
        tickNext, NextInitialized = getNextTick(pool, tick0, tick_spacing, zeroForOne)
        """
    if printTicks:
        # print statements
        print(f'   POOL PARAMS:')
        print(f'      liquidity: {liquidity}')
        print(f'      tick0    : {tick0}  ')
        
        print(F'\nTick info BEFORE:')
        LowParams0  = getTickInfo(pool, tickLow, False)
        HighParams0 = getTickInfo(pool, tickHigh, False)
        LGross0 = LowParams0['liqGross']; LNet0 = LowParams0['liqNet']
        HGross0 = HighParams0['liqGross']; HNet0 = HighParams0['liqNet']
        time.sleep(2)

    #-------MINT
    mint(pool, tick0, x, y, TokenA, TokenB, fee, tickLow, tickHigh, account)
    
    if printTicks:
        print(F'\nTick info AFTER:')

        LowParams1  = getTickInfo(pool, tickLow, True)
        HighParams1 = getTickInfo(pool, tickHigh, True)
        HGross1 = HighParams1['liqGross']; HNet1 = HighParams1['liqNet']
        LGross1 = LowParams1['liqGross']; LNet1 = LowParams1['liqNet']
        
        # calculate added liquidity amounts
        print(f"\nΔL's:")
        print(f'   tickLow = {tickLow}:')
        ΔLGross = LGross1 - LGross0 ; print(f'      ΔLGross: {ΔLGross}' )
        ΔLNet   = LNet1 - LNet0     ; print(f'      ΔLNet  : {ΔLNet}' )
        print(f'   tickHigh = {tickHigh}:')
        ΔHGross = HGross1 - HGross0 ; print(f'      ΔHGross: {ΔHGross}' )
        ΔHNet   = HNet1 - HNet0     ; print(f'      ΔHNet  : {ΔHNet}' )
        
        Lpool1 = pool.liquidity()
        ΔLpool = Lpool1 - Lpool0
        print(f'   Lpool1 : {Lpool1}')
        print(f'      ΔLpool : {ΔLpool}')


def main():
    # see multihopswap in router contract; we need to mint liquidity to 
    # two different pools
    poolnums = [1,2]
    for poolnum in poolnums:
        mint_(poolnum)
    print('\n=============== end mint.py =====================\n')
