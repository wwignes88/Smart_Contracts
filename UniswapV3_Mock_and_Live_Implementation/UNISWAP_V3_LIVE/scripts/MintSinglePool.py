from scripts.Load.helpful_scripts import (getPoolFromAddress, 
                                          get_Token_bal, 
                                          get_accounts,
                                          getTickInfo,
                                          liquidity_for_amounts,
                                          gas_controls,
                                          get_contract_from_abi,
                                          getslot0,
                                          p_to_x96,
                                          CurrencyConvert)


from scripts.Load.PoolActions import mint_to_pool
#from scripts.Load.PoolActions import mint
from brownie import network, interface, config
from scripts.Load.DICTS import NETWORK_TO_RATE_DICT
import sys, time

# account  : 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce # Goog
# accountII: 0x6dFa1b0235f1150008B23B2D918F87D4775fBba9 # Explor


def mint_(pool_address, account):
    print(f'\n\n\n======= MINTING TO POOL {pool_address[:10]}...:')
    
    my_math = get_contract_from_abi('MyMath')
            
    # Load pool 
    (pool, slot0, liquidity, tick_spacing, fee, token0, token1) = getPoolFromAddress(pool_address, account)
    tick0 = slot0['tick']
    sym0  = token0.symbol() 
    sym1  = token1.symbol() 

    print(f'\n loaded pool.')
    print(f'   token0       : {sym0}')
    print(f'   token1       : {sym1}')
    print(f'   liquidity    : {liquidity*1e-18}')
    print(f'   tick0        : {slot0['tick']}')
    print(f'   tick_spacing : {tick_spacing}')
    print(f'   fee          : {fee}')


    #            ==============  get bals/ convert ==========
    print(f'\nBals:')

    # native bals/ conversion
    myNative_bal   = account.balance()
    NativeSym      = NETWORK_SYMS[network.show_active()]
    myUSD          = CurrencyConvert(myNative_bal, NativeSym, 'USD')
    

    myBalance0 = get_Token_bal(token0, account.address, 'my', True)
    myBalance1 = get_Token_bal(token1, account.address, 'my', True)

    # -------------- MINT TOKENS
    # mint tokens then exit without minting to pool
    MINT_TOKENS = False
    if MINT_TOKENS:
        mint_amount   = 1e18
        mint_receiver = account.address
        tx            = token0.mint(mint_amount, mint_receiver) 
        tx.wait(1)
        
        myBalance0 = get_Token_bal(token0, account.address, 'my', True)
        myBalance1 = get_Token_bal(token1, account.address, 'my', True)

    # -------------- MINT AMOUNTS 
    # set amounts to mint in liquidity position
    x = 3*1e18
    y = 4*1e18
    tickLow  = 0
    tickHigh = 15300

    # -------------- VIEW TICKS 
    # view next n ticks then exit 
    VIEW_TICKS = True
    if VIEW_TICKS:
        print(f'\nNEXT TICKS:')
        # zeroForOne will set the direction of nextTick. 
        n = 5  # number of ticks to view
        zeroForOne = True
        printTicks = False

        i = 0
        while i < n:
            (c, mA, mB, mC, t_next, tickbit, initialized) = my_math.nextTick(
                tick0, 
                tick_spacing, 
                zeroForOne, 
                pool
            )
            #print(f'      next tick: {t_next}')
            print(f'\n------- tick {t_next}')
            getTickInfo(pool, t_next, True)

            i += 1
        sys.exit(0)
    
    # vget mint position tick info.
    MINT_TICKS_INFO = False
    if MINT_TICKS_INFO:

        print(F'\nTick info BEFORE:')
        LowParams0  = getTickInfo(pool, tickLow, False)
        HighParams0 = getTickInfo(pool, tickHigh, False)
        LGross0     = LowParams0['liqGross']  ; LNet0 = LowParams0['liqNet']
        HGross0     = HighParams0['liqGross'] ; HNet0 = HighParams0['liqNet']
        time.sleep(2)


    # -------------- L FOR AMOUNTS
    # calculate liquidity for x,y amounts then exit
    LIQUIDITY_AMOUNTS = True
    if LIQUIDITY_AMOUNTS:
        L_for_xy = liquidity_for_amounts(my_math, tick0, tickLow, tickHigh, x, y)
        if L_for_xy == 0:
            print(f'\attempting to mint zero liquidity (must be non-zero)')
            sys.exit(0)


    #  --------------------------------------   MINT

    # MintSinglePool.py :
        # MintTokens (optional)
        # View Ticks (optionl)
        # print mint ticks (optionl)

    # PoolActions.py :
        # troubleshoot (optional)
            # more detailed liquidity calculations
            # revert mint calls
        # approval
        # event listener (optionl)
        
    mint_to_pool(pool, x, y, token0, token1, fee, tickLow, tickHigh, account)
    


    
def deployPool_(tokenA_sym, tokenB_sym, fee, account, price):

    tokenA_address = config["networks"][network.show_active()][tokenA_sym]
    tokenB_address = config["networks"][network.show_active()][tokenB_sym]

    if fee not in [500,3000,10000]:
        print('\ninvalid fee.')
        sys.exit(0)
    factory = interface.IV3Factory(config["networks"][network.show_active()]['Factory'])

    pool_addr  = factory.getPool(tokenA_address, tokenB_address, fee)
    zero_address = '0x0000000000000000000000000000000000000000'

    # create pool if needed.
    if pool_addr == zero_address:
        input(f'\nno pool deployed. creating pool...')
        tx = factory.createPool(tokenA_address, tokenB_address, fee, {'from':account})
        tx.wait(1)
        pool_addr  = factory.getPool(tokenA_address, tokenB_address, fee)
        print(f'\ndeployed pool {pool_addr}')

    # get pool contract
    pool = interface.IV3Pool(pool_addr)

    # pool parameters
    liquidity    = pool.liquidity()
    slot0        = getslot0(pool, False)
    tick_spacing = int(pool.tickSpacing() )
    
    if not slot0['unlocked'] :
        # initialize pool 
        p0_X96  = p_to_x96(price)
        print(f'\n   initializing w/ price p = {price} [{p0_X96}] ')  
        tx = pool.initialize(p0_X96, {"from": account})
        tx.wait(1)
        slot0 = getslot0(pool, False)
    
    print(f'   liquidity    : {liquidity}')
    print(f'   tick spacing : {tick_spacing}')
    slot0 = getslot0(pool, True)
        
    return (pool, slot0, liquidity, tick_spacing, p0_X96)




#                 ==============================
#                 ==============================
#                 ==============================

def main():

    account = get_accounts(0)
    gas_controls(account, set_gas_limit=False, priority_fee=False)

    tokenA_sym = 'link'
    tokenB_sym = 'weth'
    fee = 3000
    
    OPTION = 1 #  1: MINT, 2 deploy pool
    if OPTION == 1:

        # load pool address from token pair
        factory = interface.IV3Factory(config["networks"][network.show_active()]['Factory'])
        tokenA_address = config["networks"][network.show_active()][tokenA_sym]
        tokenB_address = config["networks"][network.show_active()][tokenB_sym]
        pool_address   = factory.getPool(tokenA_address, tokenB_address, fee)

        # load pool address directly
        #pool_address = '0x0001fcbba8eb491c3ccfeddc5a5caba1a98c4c28' # BCZ_WETH,303015134493562686441

        print(f'\nminting to pool {pool_address[:7]}...')
        mint_(pool_address, account)

    if OPTION == 2:
        print(f'\ndeploying pool...')
        price      = 1
        deployPool_(tokenA_sym, tokenB_sym, fee, account, price)

    print('\n=============== end mint.py =====================\n')
