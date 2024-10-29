
from scripts.Load.helpful_scripts import (get_contract,
                                          get_accounts,
                                          getPoolPosition,
                                          getTickInfo,
                                          getNFTPosition,
                                          gas_controls,
                                          loadPool,
                                          time,
                                          sys,
                                          p_from_x96,
                                          MIN_TICK, MAX_TICK, Q96)
from scripts.Load.BrownieFuncs import getEvents
from scripts.Load.DICTS import TICK_SPACINGS



# --------- mint
def manageLiquidity(account):
    
    t0 = 'weth' 
    t1 = 'sand' 
    t2 = 'link' 
    fee    = 3000

    liquid     = get_contract('MliquidityMiner')
    ManagerII  = get_contract('MNonfungiblePositionManagerII')
    my_math    = get_contract('MyMath')

    #---------------- GET TOKEN ID's
    mytokenIdCount = liquid.getTokenCount(account.address)
    print(f'mytokenIdCount: {mytokenIdCount}')
    if mytokenIdCount > 0:
        mytokenIds = liquid.getTokenIds(account.address)
        tokenId    = mytokenIds[1]
        print(f'my tokenIds: {mytokenIds}')
    if mytokenIdCount == 0:
        print(f'\nno liquidity positions minted.')
        sys.exit(0)
    
    #--------------- LOAD POOL/ GET TICK INFO

    # get NFT Manager position
    NFTposition = getNFTPosition(ManagerII, tokenId, account, True)
    TL     = NFTposition['tickLow'] ; TH = NFTposition['tickHigh']
    token0 = NFTposition['token0']  ; token1 = NFTposition['token1'] 
    
    # load pool params
    (pool, slot0, liquidity, tick_spacing) = loadPool(token0, token1, fee, account)
    tick0  = slot0['tick']

    print(f'\nPOOL PARAMS:')
    print(f'   liquidity: {liquidity}')
    print(f'   tick0    : {tick0}  ')
    print(f'   tickL    : {TL}  ')
    print(f'   tickH    : {TH}  ')
    
    # pool position
    PoolPositionOwner = ManagerII.address
    PoolPosition      = getPoolPosition(pool, PoolPositionOwner, TL, TH, True)

    OPTIONS = []
    if len(OPTIONS) > 0:
        gas_controls(account, set_gas_limit=False, priority_fee=False)
    
    #--------- PREDICT FEE INFO
    if 0 in OPTIONS:
        # predict the feegrowthOutside accumulated for a tick when minting
        # see _update(...) function in pool contract. 
        # feeGrowthInside of position [tickHigh/tickLow boundaries] is calculated,
        # then tickLow.feegrowthOutside and tickHigh.feegrowthOutside are updated 
        # with this value if and only if they are below slot0.tick [respectively].
        print(f'\n[MINT] FEE GROWTH PREDICTION')
        LMaxPerTick = pool.maxLiquidityPerTick()
        fGG0 = pool.feeGrowthGlobal0X128()
        TL_info =  getTickInfo(pool, TL, False) ; LOWfeeGrowthOutsideX128  = TL_info['feeGrowthOut0']
        TH_info =  getTickInfo(pool, TH, False) ; HIGHfeeGrowthOutsideX128 = TH_info['feeGrowthOut0']

        print(f'   CURRENT PARAMS:')
        print(f'      pool Position fGIn : {PoolPosition["feeGrowthIn0"]}')
        print(f'      pool fGG0          : {fGG0}')
        print(f'      TL_feeGrowthOut0   : {LOWfeeGrowthOutsideX128}')
        print(f'      TH_feeGrowthOut0   : {HIGHfeeGrowthOutsideX128}')
        
        (fGIn, fGbelow, fGabove) = my_math.getFeeGrowthInside(
             TL,
             TH,
             tick0,
             fGG0,
             LOWfeeGrowthOutsideX128,
             HIGHfeeGrowthOutsideX128,
             LMaxPerTick  
        )
        fGInPredicted = fGG0 - fGIn - fGbelow
        print(f'   PREDICTED PARAMS:')
        print(f'      fGIn    : {fGIn}')
        print(f'      fGIn [p]: {fGInPredicted}')
        print(f'      fGbelow : {fGbelow}')
        print(f'      fGabove : {fGabove}')

    #--------- INCREASE L
    if 1 in OPTIONS:
        option = 0
        amountAdd0 = 1e18
        amountAdd1 = 1e18
        tx = liquid.increaseL(
            tokenId,
            amountAdd0,
            amountAdd1,
            option,
            {"from":account})
        tx.wait(1)

    #--------- DECREASE L
    if 2 in OPTIONS:
        frac   = 1
        option = 0
        tx = liquid.decreaseLiquidity(tokenId, frac, option, {"from":account})
        tx.wait(1)

    #--------- COLLECT
    if 3 in OPTIONS:
        amout0Max = NFTposition['token0Owed']
        amout1Max = NFTposition['token1Owed']
        recipient = account
        option    = 0
        tx = liquid.collectFees(tokenId, amout0Max, amout1Max, option, {"from":account})
        tx.wait(1)

    #--------- BURN
    if 4 in OPTIONS:
        tx = liquid.burnPosition(tokenId, {"from":account})
        tx.wait(1)

    #--------- RETRIEVE NFT
    if 5 in OPTIONS:
        tx = liquid.retrieveNFT(tokenId, {"from":account})
        tx.wait(1)
    
    
    if len(OPTIONS) > 0:
        mytokenIds = liquid.getTokenIds(account.address)
        tokenId    = mytokenIds[0]
        print(f'my tokensIds: {mytokenIds}')
        #PoolPosition = getPoolPosition(pool, PoolPositionOwner, TL, TH, True)

def main():
    account = get_accounts(0) 
    manageLiquidity(account)


