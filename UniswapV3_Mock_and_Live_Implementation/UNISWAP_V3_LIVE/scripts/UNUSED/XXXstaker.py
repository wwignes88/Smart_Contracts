
from scripts.Load.helpful_scripts import *
from scripts.Load.DICTS import *
# account: 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce
# accountII: 0x559B0cD29EaBfFC60ee204A78E16852A6D79F50f

def stake_():
    print('\n=============== staker.py =====================\n')

    PRINT_    = 1

    router    = get_contract('MSwapRouter')
    liquid    = get_contract('MliquidityMiner')
    staker    = get_contract('MLiquidityStaker')
    factory   = get_contract('MFactory')
    nonfung   = get_contract('MNonfungiblePositionManager')

    # load accounts/ contracts/ network dictionary
    rateDict = NETWORK_TO_RATE_DICT[network.show_active()]

    #liquid   = get_contract('provide_liquidity')
    
    # --------- set tokens
    # *token0 and token1 will be swap/ mint tokens
    t0 = 'weth' ; token0 = get_contract(t0)
    t1 = 'sand' ; token1 = get_contract(t1)
    t2 = 'link' ; token2 = get_contract(t2)
    native = rateDict["symb"] # native currency symbol
    Itoken   = token0 # reward token
     
    # --------- get balances/ Token Ids
    getBals = False
    if getBals:
        # ERC20 Tokens
        
        Tokens    = [token1, token2, native_token]
        Contracts = [staker]
        
        # balances
        (GasBal,
         MyTokenBals,
         ContractTokenBals) = Token_Bals(account, Tokens, Contracts, True )

        x = MyTokenBals[f'my_{token0.symbol()}']*0.01

    # --------- Load pool
    LoadPool = True
    if LoadPool:
        x96   = X96 = 2**96
        fee   = 3000
        pool  = loadPool(token0, token1, fee, account, PRINT_)
        slot0 = getslot0(pool, False)
        pX96  = slot0['rootP']
        p     = (pX96/X96)**2 # pool price
        if not slot0['unlocked']:
            print(f'\ninitializing pool...')
            p    = p0/p1 # pool price
            pX96 = p_to_x96(p)
            tx   = pool.initialize(pX96, {"from": account})
            tx.wait(1)

        # get tick corresponding to pool price
        #   loaded pool. p = 4043.717301643854 [tick: 41526]
        #   [C CHECK] loaded pool. p = 4043.717301643854 [tick: 83053]
        pool_tick = tick_at_sqrt(pX96) 
        if PRINT_ > 1:
            print(f'\nloaded pool. p = {p} [tick: {pool_tick}]')

        if PRINT_ > 2:
            pool_tick = liquid.tickAtSqrt(pX96)
            print(f'   *[C CHECK]:\n    loaded pool. p = {p} [tick: {pool_tick}]')

    #-------- tokenId's/ deposit/ reward info
    getTokenIds = True 
    if getTokenIds:
        print(f'\n----- TokenIds:')
        mytokenIds      = list(liquid.getTokenIds(account.address))
        LMinersTokenIds = list(liquid.getTokenIds(liquid.address))
        StakersTokenIds = list(liquid.getTokenIds(staker.address))
        tokenId = mytokenIds[-1]
        if PRINT_ > 3:
            print(f'\n   LiquidMiner tokenIds:')
            print(f'       my tokenIds: {mytokenIds} {type(mytokenIds)}')
            #print(f'       StakersTokenIds tokenIds: {StakersTokenIds}')
            #print(f'       LMinersTokenIds tokenIds: {LMinersTokenIds}')
            position = getPosition(nonfung, tokenId, account, 3)

        print(f'\n   Nonfung/ MStaker info:')
        totalIds = nonfung.totalSupply()
        print(f'       total supply: {totalIds}')
        i = totalIds-2
        while i < totalIds:
            try:
                tokenId      = nonfung.tokenByIndex(i)
                print(f'       [{i}] tokenId: {tokenId}')
                
                # nonfungiblePosManager info
                TokenOwner   = nonfung.ownerOf(tokenId)
                position     = nonfung.positions(tokenId)
                operator     = position[1]
                print(f'          Tokenowner : {TokenOwner}')
                print(f'          operator   : {TokenOwner}')
                
            except Exception as e:
                print(f'       [{i}] {e}')
                input(f'       proceed?')
            
            i += 1

        print(f'\n   tokenId: {tokenId}')
        print(f'   liquid: {liquid.address}')
        print(f'   staker: {staker.address}')
        
    if not tokenId:
        print(f'\n need to mint token')
        sys.exit(0)
    
    #-------- get incentive key.
    numIncentives = staker.numIncentives()
    if numIncentives > 0:
        incentiveId   = staker.incentiveId_by_index(numIncentives-1) 
        
        #----- get key
        get_key = True 
        if get_key:
            # 0xdf732b90b4215c9b80b1cdf3bea5e282d08a6dca80bddb59a1cd49a141710460
            # or update after creating incentive (option 0)
            key = staker.getIncentiveKey(incentiveId)
            Itoken   = key[0]
            pool     = key[1]
            t_start  = key[2]
            t_end    = key[3]
            refundee = key[4]
            exists   = key[5]
            incentive_key = (Itoken, pool, t_start, t_end, refundee)

            if PRINT_ > 0:
                print('\n---incentive key:')
                print(F'    current time: {int(time.time())}')
                print(f'    numIncentives: {numIncentives}')
                print(f'    incentiveId  : {str(incentiveId)[:8]}')
                print(F'    KEY:')
                print(f'       Itoken       : {Itoken}')
                print(f'       pool         : {pool}')
                print(f'       t_start      : {t_start}   [*currently: {int(time.time())}]')
                print(f'       t_end        : {t_end}')
                print(f'       refunde      : {refundee}')
                print(f'       exists       : {exists}')

        #----- MStaker deposit info
        deposit_reward_info = True 
        if deposit_reward_info:
            (DepositOwner, 
            EOAaccount,
            numStakes,
            tickL,
            tickU) = staker.deposits(tokenId)
            if PRINT_ > 0:
                print(f'\n---deposit {tokenId}:')
                print(f'       owner     : {DepositOwner}')
                print(f'       EOAaccount: {EOAaccount}')
                print(f'       numStakes : {numStakes}')
                print(f'       tickL     : {tickL}')
                print(f'       tickU     : {tickU}')
        
        #---- stakes
        get_stakes = True 
        if get_stakes:
            s_per_L_in, L = staker.stakes(tokenId, incentiveId)
            if PRINT_ > 0:
                print('\n---stakes:')
                print(F'    s_per_L_in: {s_per_L_in}')
                print(f'    liquidity : {L}')
            

        #---- reward info 
        get_reward_info = True 
        if numStakes > 0 and get_reward_info:
            reward, s_inside = staker.getRewardInfo(
                                    incentive_key,
                                    tokenId,
                                    {'from': account})
            if PRINT_ > 0:
                print(f'\n---reward:')
                print(F'      reward     : {reward}')
                print(F'      s_inside   : {s_inside}')
                

    #==============================================================
    #=====================   EXECUTE FUNCTIONS    =================
    #==============================================================

    options = []

    # --------- create incentive
    if 0 in options:
        print(f'\n\n==========[option 0]: CREATE INCENTIVE:')

        """
        current_date  = datetime.today().date()
        start_time    = datetime(current_date.year, current_date.month, current_date.day, 12, 0)
        t_start       = start_time.timestamp()
        """
        t_start      =  int(time.time())+60
        t_end        =  t_start + (60*60*24)*30 # one month

        refundee = account.address
        
        # create incentive key
        incentive_key = (Itoken, pool, t_start, t_end, refundee)
        reward = 1*1e18

        try:
            # computed incentive Id:
            incentiveId = staker.compute_incentiveId(incentive_key)
            print(F'\nincentiveId: {incentiveId}')
            
            staker_allowance = approve_contract_spender(2*reward, Itoken, staker, account, 'MStaker')

            print(f'\n creating incentive....')
            tx = staker.createIncentive(incentive_key, reward, {'from': account})
            tx.wait(1)
            
            events      = tx.events
            _events     =  events['IncentiveCreated'][0]  # Assuming there is only one DecreaseLiquidity event
            if PRINT_ > 0:
                for index, (event, value) in enumerate(_events.items(), start=1):
                    print(f'    [{index}] {event}: {value} ')

        except Exception as e:
            print(f'    createIncentive failed {e}')
            
    # --------- stake Token
    if 1 in options:
        print(f'\n\n==========[option 4]: STAKE TOKEN:')
        if TokenOwner != staker.address:
            print(f'\ndepositing ERC721 token to staker.sol ...')
            tx = liquid.transferToStaker(
                    liquid.address,   # from: assuming liquid miner the token holder
                    staker.address,   
                    tokenId,
                    account.address,
                    {'from': account}
                )
            tx.wait(1)
            # !! missing implementation: StakerTransferEvents  = tx.events

        #--------
        print(f'\n   staking...')
        # stake token
        tx = staker.stakeToken(
                                incentive_key,
                                tokenId,
                                {'from': account})
        tx.wait(1)
        # Retrieve amount0 and amount1 from tx
        events  = tx.events
        _events = events['TokenStaked'][0]  # Assuming there is only one DecreaseLiquidity event
   
        if PRINT_ > 0:
            for index, (event, value) in enumerate(_events.items(), start=1):
                print(f'    [{index}] {event}: {value} ')

    # --------- transfer deposit
    if 2 in options:
        print(f'\n\n==========[option 2]: TRANSFER DEPOSIT:')

        tokenId = 1
        to = account.address
        tx = staker.transferDeposit(
                                tokenId,
                                to,
                                {'from': account})
        tx.wait(1)
        events  = tx.events
        _events    =  events['DepositTransferred'][0]  # Assuming there is only one DecreaseLiquidity event

        if PRINT_ > 1:
            for index, (event, value) in enumerate(_events.items(), start=1):
                print(f'    [{index}] {event}: {value} ')

    # --------- unstake Token
    if 3 in options:
        print(f'\n\n==========[option 5]: UNSTAKE TOKEN:')
        tx = staker.unstakeToken(
                                incentive_key,
                                tokenId,
                                {'from': account})
        tx.wait(1)
        events  =  tx.events
        _events =  events['TokenUnstaked'][0]  # Assuming there is only one DecreaseLiquidity event
        
        if PRINT_ > 1:
            for index, (event, value) in enumerate(_events.items(), start=1):
                print(f'    [{index}] {event}: {value} ')

    # --------- claim reward
    if 4 in options:
        print(f'\n\n==========[option 6]: CLAIM REWARD:')

        Itoken   = token0
        to       = account.address
        amountRequested = 2

        tx = staker.claimReward(
                                Itoken,
                                to,
                                amountRequested,
                                {'from': account})
        tx.wait(1)
        
        events  = tx.events
        #print(f'\nevents: {events}')
        _events   = events['RewardClaimed'][0]  # Assuming there is only one DecreaseLiquidity event
        to        = _events['to']
        reward    = _events['reward']
        
        if PRINT_ > 1:
            for index, (event, value) in enumerate(_events.items(), start=1):
                print(f'    [{index}] {event}: {value} ')

    # --------- withdraw token
    if 5 in options:
        print(f'\n\n==========[option 3]: WITHDRAW TOKEN:')

        tokenId = 1
        to = account.address
        data = ''
        tx = staker.withdrawToken(
                                tokenId, 
                                to,
                                data,
                                {'from': account})
        tx.wait(1)
        events  = tx.events
        _events     = events['DepositTransferred'][0]  # Assuming there is only one DecreaseLiquidity event


        if PRINT_ > 1:
            for index, (event, value) in enumerate(_events.items(), start=1):
                print(f'    [{index}] {event}: {value} ')
    
    # --------- end incentive
    if 6 in options:
        print(f'\n\n==========[option 0]: END INCENTIVE:')

        tx = staker.endIncentive(
                                incentive_key,
                                {'from': account})
        tx.wait(1)
        # Retrieve amount0 and amount1 from tx
        events  = tx.events
        #print(f'\nevents: {events}')
        _events     =  events['IncentiveEnded'][0]  # Assuming there is only one DecreaseLiquidity event

        if PRINT_ > 1:
            for index, (event, value) in enumerate(_events.items(), start=1):
                print(f'    [{index}] {event}: {value} ')


def main():
    stake_()
    print('\n=============== end staker.py =====================\n')

