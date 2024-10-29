
from scripts.Load.helpful_scripts import (get_accounts,
                                          get_LMiner_Deposit,
                                          getERC20Min,
                                          getPool,
                                          getTickInfo,
                                          getV3Contracts,
                                          get_NPM_position,
                                          get_pool_position,
                                          gas_controls,
                                          getslot0,
                                          get_Token_bal,
                                          #loadPool,
                                          get_contract_from_abi,
                                          time,
                                          sys,
                                          p_from_x96,
                                          MIN_TICK, MAX_TICK, Q96)
#from scripts.Load.BrownieFuncs import getEvents
from scripts.Load.DICTS import TICK_SPACINGS
import numpy as np
# account: 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce
# accountII: 0x559B0cD29EaBfFC60ee204A78E16852A6D79F50f



# --------- mint
def manage_liquidity(account):

    liquid      = get_contract_from_abi('LiquidityMiner')
    my_math     = get_contract_from_abi('MyMath')
    NPM_Manager = getV3Contracts(1)

    #---------------- GET TOKEN ID's
    tokenIds = np.array(liquid.getTokenIds())
    print(f'tokenIds: {tokenIds} ({type(tokenIds)})')
    num_tokens = len(tokenIds) 

    if num_tokens > 0:
        mytokenIds = liquid.getRetrievedTokenIds(account.address)
        print(f'my tokenIds: {mytokenIds}')

        # select tokenId index
        tokenIndex = 0
        tokenId    = tokenIds[tokenIndex]

        # LiquidityMiner.sol deposit
        # *only thing this has that NPM_position doesn't is owner according to LiquidityMiner.sol
        deposit = get_LMiner_Deposit(tokenId, liquid, False)

        # *[food for thought] should NonfungiblePositionManager parameters (e.g. liquidity) be the same as 
        # pool parameters? should global pool liquidity differ from pool position.liquidity?

        # NPM position
        NPM_position = get_NPM_position(NPM_Manager, tokenId, account, False)
        NPM_pos_L    = NPM_position['liquidity']
        NPM_pos_TL   = int(NPM_position['tickLow'])
        NPM_pos_TH   = int(NPM_position['tickHigh'])


        # load tokens/ pool
        Token0 = getERC20Min(NPM_position['token0']) ; sym0 = Token0.symbol()
        Token1 = getERC20Min(NPM_position['token1']) ; sym1 = Token1.symbol()
        pool   = getPool(Token0.address, Token1.address, NPM_position['fee'], account)
        pool_L = pool.liquidity()
        slot0  = getslot0(pool, False)
        tick0  = slot0['tick']


        # NPM_pos percentage of pool liquidity
        if pool_L != 0:
            L_pos_percent = NPM_pos_L/pool_L
        if pool_L == 0:
            L_pos_percent = 1

        print(f'\nPOOL {sym0}/{sym1} PARAMS:')
        print(f'   pool.L             : {pool_L}')
        print(f'   NPM.position[{tokenId}] L: {NPM_pos_L} [{L_pos_percent}% pool L]')
        print(f'   pool tick0         : {tick0}  ')
        print(f'   NPM.position.tL    : {NPM_pos_TL}  ')
        print(f'   NPM.position.tH    : {NPM_pos_TH}  ')
        
        # pool position
        pool_position = get_pool_position(
            pool,
            NPM_Manager, 
            my_math,
            NPM_pos_TL, 
            NPM_pos_TH, 
            True)


    if num_tokens == 0:
        print(f'\nno liquidity positions minted.')
        sys.exit(0)
    
    #--------------- LOAD POOL/ GET TICK INFO

    OPTIONS = [6]
    if len(OPTIONS) > 0:
        gas_controls(account, set_gas_limit=False, priority_fee=False)
    
    #--------- PREDICT FEE INFO
    if 0 in OPTIONS:
        print(f'\nFEE PREDICTION:')
        # predict the feegrowthOutside accumulated for a tick when minting
        # *see _update(...) function in pool contract. 
        # feeGrowthInside of position [tickHigh/tickLow boundaries] is calculated,
        # then tickLow.feegrowthOutside and tickHigh.feegrowthOutside are updated 
        # with this value if and only if they are below slot0.tick [respectively].

        L_max_per_tick = pool.maxLiquidityPerTick()
        TL_info     = getTickInfo(pool, NPM_pos_TL, False) 
        TH_info     = getTickInfo(pool, NPM_pos_TH, False) 

        predict_fee_0 = True
        if predict_fee_0:
            fGG0        = pool.feeGrowthGlobal0X128()

            TL_fg_out_0 = TL_info['feeGrowthOut0']
            TH_fg_out_0 = TH_info['feeGrowthOut0']

            print(f'\n   TOKEN 0:')
            print(f'      [pool pos.] fg_in_0 : {pool_position["fg_in_last_0"]}')
            print(f'      pool fGG0           : {fGG0}')
            print(f'      TL_feeGrowthOut0    : {TL_fg_out_0}')
            print(f'      TH_feeGrowthOut0    : {TH_fg_out_0}')
            
            (fGIn_0, fGbelow_0, fGabove_0) = my_math.getFeeGrowthInside(
                NPM_pos_TL,
                NPM_pos_TH,
                tick0,
                fGG0,
                TL_fg_out_0,
                TH_fg_out_0,
                L_max_per_tick  
            )
            fGInPredicted_0 = fGG0 - fGIn_0 - fGbelow_0
            print(f'   prediction:')
            print(f'      fGIn_0            : {fGIn_0}')
            print(f'      fGIn_0 [predicted]: {fGInPredicted_0}')
            print(f'      fGbelow_0         : {fGbelow_0}')
            print(f'      fGabove_0         : {fGabove_0}')

        predict_fee_1 = True
        if predict_fee_1:
            fGG1        = pool.feeGrowthGlobal1X128()
            TL_fg_out_1 = TL_info['feeGrowthOut1']
            TH_fg_out_1 = TH_info['feeGrowthOut1']

            print(f'\n   TOKEN 1:')
            print(f'      [pool pos.] fg_in_0 : {pool_position["fg_in_last_1"]}')
            print(f'      pool fGG1           : {fGG1}')
            print(f'      TL_feeGrowthOut0    : {TL_fg_out_1}')
            print(f'      TH_feeGrowthOut0    : {TH_fg_out_1}')
            
            (fGIn_1, fGbelow_1, fGabove_1) = my_math.getFeeGrowthInside(
                NPM_pos_TL,
                NPM_pos_TH,
                tick0,
                fGG1,
                TL_fg_out_1,
                TH_fg_out_1,
                L_max_per_tick  
            )
            fGInPredicted_1 = fGG1 - fGIn_1 - fGbelow_1
            print(f'   prediction:')
            print(f'      fGIn_1            : {fGIn_1}')
            print(f'      fGIn_1 [predicted]: {fGInPredicted_1}')
            print(f'      fGbelow_1         : {fGbelow_1}')
            print(f'      fGabove_1         : {fGabove_1}')

    #--------- PREDICT LIQUIDITY AMOUNTS/ AMOUNTS FOR LIQUIDITY
    if 1 in OPTIONS:
        
        # calculate liquidity for x,y amounts
        PREDICT_LIQUIDITY_FOR_AMOUNTS = True
        if PREDICT_LIQUIDITY_FOR_AMOUNTS:
            x = 1e18
            y = 1e18
            from scripts.Load.helpful_scripts import liquidity_for_amounts
            L_for_xy = liquidity_for_amounts(my_math, tick0, NPM_pos_TL, NPM_pos_TH, x, y)
            if L_for_xy == 0:
                print(f'\nWARNING!! Attempting to mint zero liquidity (must be non-zero)')
                sys.exit(0)

        # calculate amounts x,y for L
        PREDICT_AMOUNTS_FOR_LIQUIDITY = True
        if PREDICT_AMOUNTS_FOR_LIQUIDITY:
            L = 10000000569
            from scripts.Load.helpful_scripts import amounts_for_liquidity
            x,y = amounts_for_liquidity(my_math, tick0, NPM_pos_TL, NPM_pos_TH, L)
            if x == 0 or y == 0:
                print(f'\nWarning!! ??? ')
                sys.exit(0)
 
    #--------- INCREASE L
    if 2 in OPTIONS:
        print(f'\nINCREASE LIQUIDITY:')
        from scripts.Load.helpful_scripts import approve_contract_spender
            
        myBalance0 = get_Token_bal(Token0, account.address, 'my', True)
        myBalance1 = get_Token_bal(Token1, account.address, 'my', True)


        option = 0
        amountAdd0 = 1e18
        amountAdd1 = 1e18
        approve_contract_spender(amountAdd0, Token0, liquid, account, 'Liquid Miner')
        approve_contract_spender(amountAdd1, Token1, liquid, account, 'Liquid Miner')
            
        tx = liquid.increaseL(
            tokenId,
            amountAdd0,
            amountAdd1,
            option,
            {"from":account})
        tx.wait(1)

    #--------- DECREASE L
    if 3 in OPTIONS:
        print(f'\nDECREASE LIQUIDITY:')
        frac   = 1
        option = 0
        print(f'   decreasing liquidity of position {tokenId} 1/{frac}...')
        tx = liquid.decreaseLiquidity(tokenId, frac, option, {"from":account})
        tx.wait(1)

    #--------- COLLECT
    if 4 in OPTIONS:
        print(f'\nCOLLECT:')
        amout0Max = NPM_position['token0Owed']
        amout1Max = NPM_position['token1Owed']
        recipient = account
        print(f'   amout0Max: {amout0Max*1e-18} ')
        print(f'   amout1Max: {amout1Max*1e-18} ')
        option    = 0
        tx = liquid.collectFees(tokenId, amout0Max, amout1Max, option, {"from":account})
        tx.wait(1)

    #--------- BURN
    if 5 in OPTIONS:
        print(f'\nBURN:')
        tx = liquid.burnPosition(tokenId, {"from":account})
        tx.wait(1)

    #--------- RETRIEVE NFT
    if 6 in OPTIONS:
        input(f'\nRETRIEVE NFT:')
        tx = liquid.retrieveNFT(tokenId, {"from":account})
        tx.wait(1)
    
    


 
    
def main():
    account = get_accounts(0) 
    manage_liquidity(account)


