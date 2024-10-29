from brownie import (accounts, interface, network, config, Contract,
                    MyMath,
                    LiquidityMiner
                    )
import sys, os
import time, datetime
import math
import pandas as pd
import numpy as np
from scripts.Load.DICTS import NETWORK_TO_RATE_DICT, NETWORK_SYMS

#------------------------- ACCOUNT/ CONTRACTS
if True:
    
    def getConfigAddress(symbol):
        return config["networks"][network.show_active()][symbol]
    
    # load account
    def get_accounts(option):
        if option == 0:
            return accounts.add(config["wallets"]["EXPLOR_key"])
        if option == 1:
            return accounts.add(config["wallets"]["GOOG_key"])

    def getERC20Min(tokenAddress): 
        try:
            IContract = interface.IERC20Min(tokenAddress)
            return IContract
        except Exception as e:
            print(f' \n!!error!!: {e}')
            print(f' token contract does not conform to ERC20')
            sys.exit(0)



    MY_CONTRACTS = {
                        'LiquidityMiner'    : LiquidityMiner,
                        #'LiquidityStaker'   : LiquidityStaker,
                        #'Swapper'           : Swapper,
                        'MyMath'   : MyMath}
                

    def get_contract_from_abi(contract_name):
        # get contract on active network
        contract_type    = MY_CONTRACTS[contract_name]
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi)
        return contract
    
    def getV3Contracts(option): 
        # 1 :: NPM Manager
        # 2 :: Router
        # 3 :: Factory
        if option == 1:
            return interface.IV3NPMManager(config["networks"][network.show_active()]['NonfungiblePositionManager'])
        if option == 2:
            return interface.IV3Router(config["networks"][network.show_active()]['SwapRouter'])
        if option == 3:
            return interface.IV3Factory(config["networks"][network.show_active()]['Factory'])
        

#------------------------- ERC20 TOKEN BALANCE/ APPROVE/ FUND
if True:
    
    # get token balnce of address.
    def get_Token_bal(Token, address_, _str, PRINT):
        Token_balance = Token.balanceOf(address_)
        if PRINT:
            print(f'    {_str}... {Token.symbol()} bal: {Token_balance*1e-18} wei')
        return Token_balance

    # mint tokens
    def Token_Mint(token_contract, mint_amount_wei, ToAddress, account):
        print(f'   minting {mint_amount_wei} wei {token_contract.symbol()} to acct. {ToAddress[:6]}...')
        print(f'      to acct.   : {ToAddress}...')
        print(f'      from acct. : {account.address}...')
        tx = token_contract.mint(mint_amount_wei*1e18, ToAddress, {"from": account})
        tx.wait(1)

    # check balance of an entire list of tokens...mint if needed
    def getBals(tokenDict, address, STRING, PRINT, MINT, account):
        bals = []
        for token_contract in tokenList:
            bals.append(get_Token_bal(token_contract, address,  PRINT))
        return bals
    
    # approve a contract to spent amount of token
    def approve_contract_spender(amount, token, contract, account, contract_name):
        _allowed = token.allowance(account.address, contract.address)

        # if _allowed amount is less than desired amount, approve
        if _allowed < amount:
            print(f'\napproving {contract_name} for {amount*1e-18} {token.symbol()}...')
            time.sleep(2)
            # approve(address spender, uint256 amount) 
            tx = token.approve(contract.address,
                                    amount,
                                    {"from": account})
            tx.wait(1)
            _allowed = token.allowance(account.address, contract.address)
        print(f'    {contract_name} allowance over my {token.symbol()} tokens: {_allowed*1e-18}')
        return _allowed

# ------------------------ LiquidityMiner 

def get_LMiner_Deposit(tokenId, liquidity_contract, PRINT):
    deposit = liquidity_contract.getDeposit(tokenId)
    deposit_dict = {
        'owner': deposit[0],
        'liquidity': deposit[1],
        'token0_sym': deposit[2],
        'token1_sym': deposit[3]
    }
    if PRINT:
        print(f'\nLiquidityMiner deposit [tokenId = {tokenId}]:')
        print(f'   owner     : {deposit[0]}')
        print(f'   liquidity : {deposit[1]}')
        Token0    =    getERC20Min(deposit[2])
        Token1    =    getERC20Min(deposit[3])
        print(f'   token0    : {Token0.symbol()}')
        print(f'   token1    : {Token1.symbol()}')

    return deposit_dict
                
# ------------------------- UNISWAP 
if True:

    # get tick info
    def getTickInfo(V3Pool_contract, tick_, PRINT):
        vals          = V3Pool_contract.ticks(tick_)
        params        = {}
        liqGross      = vals[0]; params['liquidityGross'] = liqGross
        liqNet        = vals[1]; params['liquidityNet'] = liqNet
        feeGrowthOut0 = vals[2]; params['feeGrowthOut0'] = feeGrowthOut0
        feeGrowthOut1 = vals[3]; params['feeGrowthOut1'] = feeGrowthOut1
        tickCumOut    = vals[4]; params['tickCumulativeOut'] = tickCumOut
        secsPerLiq    = vals[5]; params['secsPerLiquidity'] = secsPerLiq
        secsOut       = vals[6]; params['secsOut'] = secsOut
        initialized   = vals[7]; params['initialized'] = initialized

        if PRINT:
            for key, value in params.items():
                print(f'   {key}: {value}')
        return params

    # get next tick. See tickBitmap.sol in v3-core
    def getNextTick(pool, tickCurrent, tick_spacing, zeroForOne, i):
        my_math   = get_contract_from_abi('MyMath')
        # *c, m1, m2, m3, tb are troubleshooting parameters for the interested coder
        # who wishes to see deeper into the logic of calculating the next tick.
        # ignore init [initialized] because this pulls from my_math contract not the pool,
        # we will get the value of 'initialized' directly from pool 
        ( c, m1, m2, m3, tickNext, tb, init ) = my_math.nextTick(
                                                tickCurrent,
                                                tick_spacing,
                                                zeroForOne,
                                                pool
                                            )
        tickNextInfoDict = getTickInfo(pool, tickNext, False, i)     
        
        if tickNext < MIN_TICK:
            tickNext = MIN_TICK
            print(f'     tickNext < MIN TICK')
            sys.exit(0)
            
        return tickNext, tickNextInfoDict
  
  
    # get position from ERC721 manager (nonfungiblePositionManger) of a given [minted] tokenId
    def get_NPM_position(NonFungibleManager, tokenId, account, PRINT):
        vals          = NonFungibleManager.positions(tokenId,  {"from": account})
        params        = {}
        nonce         = vals[0]; params['nonce']        = nonce
        operator      = vals[1]; params['operator']     = operator
        token0        = vals[2]; params['token0']       = token0 #getERC20Min(token0)
        token1        = vals[3]; params['token1']       = token1 #getERC20Min(token1)
        fee           = vals[4]; params['fee']          = fee
        tickLow       = vals[5]; params['tickLow']      = tickLow
        tickHigh      = vals[6]; params['tickHigh']     = tickHigh
        liquidity     = vals[7]; params['liquidity']    = liquidity
        feeGrowthIn   = vals[8]; params['feeGrowthIn']  = feeGrowthIn
        feeGrowthOut  = vals[9]; params['feeGrowthOut'] = feeGrowthOut
        token0Owed    = vals[10]; params['token0Owed']  = token0Owed
        token1Owed    = vals[11]; params['token1Owed']  = token1Owed

        if PRINT:
            TOKENS = ["token0", "token1"]
            print(f'\nNFT POSITION:')
            for key, value in params.items():
                if key in TOKENS:
                    
                    print(f'   {key}: {value.symbol()}')
                if key not in TOKENS:
                    print(f'   {key}: {value}')
        
        return params

    # get position from ERC721 manager (nonfungiblePositionManger) of a given [minted] tokenId
    def get_pool_position(
            pool,
            NPM_Manager, 
            my_math_contract, 
            NPM_pos_TL, 
            NPM_pos_TH, 
            PRINT):
        pool_position_key = my_math_contract.compute(
            NPM_Manager.address, 
            NPM_pos_TL, 
            NPM_pos_TH)
        pool_pos = pool.positions(pool_position_key)
        pool_pos_dict = {'liquidity': pool_pos[0],
                            'fg_in_last_0': pool_pos[1],
                            'fg_in_last_1': pool_pos[2],
                            'tokensOwed0': pool_pos[3],
                            'tokensOwed1': pool_pos[4]}

        if PRINT:
            print(f'\nPOOL POSITION:')
            for key, value in pool_pos_dict.items():
                print(f'   {key}: {value}')
               
         
        return pool_pos_dict
    
    # get slot0 of pool
    def getslot0(V3Pool_contract, PRINT):
        params = {}
        slot0_ = V3Pool_contract.slot0()
        sqrtPriceX96 = slot0_[0]
        params['sqrtPriceX96'] = sqrtPriceX96
        tick = slot0_[1]; 
        params['tick'] =  tick
        observationIndex = slot0_[2]; 
        params['observationIndex'] =  observationIndex
        obsCard = slot0_[3]; 
        params['obsCard'] =  obsCard
        obsCardNext = slot0_[4]; 
        params['obsCardNext'] =  obsCardNext
        feeProtocol = slot0_[5]; 
        params['feeProtocol'] =  feeProtocol
        unlocked = slot0_[6]; 
        params['unlocked'] =  unlocked
        
        
        if PRINT:
            print(f'\n   slot0:')
            print(f'      Tick0    : {tick}')
            print(f'      p_X96    : {sqrtPriceX96}')
            print(f'      obs.Ind.     : {observationIndex}')
            print(f'      obs.Card.    : {obsCard}')
            print(f'      obs.Card.Next: {obsCardNext}')
            print(f'      feeProt.     : {feeProtocol}')
            #print(f'    unlocked     : {unlocked}')
            
        return params

    # load uniswapV3Pool. will create and initialize pool if needed.
    # 
    def deployPool(tokenA, tokenB, fee, account, price):

        if fee not in [500,3000,10000]:
            print('\ninvalid fee.')
            sys.exit(0)
        factory = interface.IV3Factory(config["networks"][network.show_active()]['Factory'])
        
        tx = factory.createPool(tokenA, tokenB, fee, {'from':account})
        tx.wait(1)
        pool_addr  = factory.getPool(tokenA, tokenB, fee, {'from':account})
        
        # get pool contract
        pool = interface.IV3Pool(pool_addr)
        
        # pool parameters
        liquidity    = pool.liquidity()
        slot0        = getslot0(pool, False)
        tick_spacing = int(pool.tickSpacing() )
        
            
        # initialize pool 
        if not price :
            p = 1
            p0_X96  = p_to_x96(p)
            print(f'\n   initializing w/ price p = {p0_X96} ')  
            tx     = pool.initialize(p0_X96, {"from": account})
            tx.wait(1)
            slot0 = getslot0(pool, False)
                
        return (pool, slot0, liquidity, tick_spacing, p0_X96)

    def getPoolFromAddress(pool_addr, account):

        factory = interface.IV3Factory(config["networks"][network.show_active()]['Factory'])
        
        # get pool contract
        pool = interface.IV3Pool(pool_addr)
        
        # pool parameters
        liquidity    = pool.liquidity()
        slot0        = getslot0(pool, False) 
        fee          = pool.fee()
        tick_spacing = int(pool.tickSpacing() )
        token0Addr, token1Addr = pool.token0(), pool.token1()
        Token0 = getERC20Min(token0Addr)
        Token1 = getERC20Min(token1Addr)

        # initialize pool if needed
        if not slot0['unlocked'] :
            input(f'slot0 locked. initialize w/ p=1?')
            p = 1
            p0_X96  = p_to_x96(p)

            print(f'\n   initializing w/ price p = {p0_X96} ')  
            tx     = pool.initialize(p0_X96, {"from": account})
            tx.wait(1)
            slot0 = getslot0(pool, False)
                
        return (pool, slot0, liquidity, tick_spacing, fee, Token0, Token1)

    # get pool from tokens
    def getPool(tokenA, tokenB, fee, account):
        factory    = getV3Contracts(3)
        pool_addr  = factory.getPool(tokenA, tokenB, fee, {'from':account})
        pool       = interface.IV3Pool(pool_addr)
        return pool

# ------------------ UNISWAP : Math
if True:
    from decimal import Decimal
    MIN_TICK = -887272
    MAX_TICK = -MIN_TICK
    MIN_SQRT_RATIO = 4295128739
    MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342
    Q96  = 2**24 # = 79228162514264337593543950336 # see LiquidityAmounts.sol in v3-periphery
    Q128 = 2**32

    # convert p to sqrtPX96
    def p_to_x96(p):
        pX96 = math.sqrt(p)*(2**96)
        return pX96

    # get sqrtPX96 value at tick
    def sqrtPatTick(tick):
        p = 1.0001**tick
        return p_to_x96(p)
    
    # convert pX96 to p
    def p_from_x96(pX96):
        rootP = pX96/(2**96)
        p = rootP**2
        return p
    
    # check sqrtpX96 values don't pass max/min values
    def SQRT_RATIO_CHECK(root_pX96):
        if root_pX96 <  MIN_SQRT_RATIO:
            raise Exception("root_pX96 <  MIN_SQRT_RATIO")
        if root_pX96 >  MAX_SQRT_RATIO:
            raise Exception("root_pX96 >  MAX_SQRT_RATIO")
    
    # check ticks to surposs max/min values
    def TICK_CHECK(tick):
        if abs(tick) <  MIN_TICK:
            raise Exception(f"abs(tick) = {tick} <  MIN_TICK")

    # get corresponding tick at sqprtX96 value
    def tick_at_sqrt(root_pX96):
        SQRT_RATIO_CHECK(root_pX96)
        p = ( root_pX96/(2**96) )**2
        i = int(math.log(p)/math.log(1.0001))
        TICK_CHECK(root_pX96)
        return i

    def liquidity_for_amounts(my_math_contract, tick0, tickLow, tickHigh, x, y):
        # x, y - amount 0/1 in wei
        print(f'\nLIQUIDITY FOR AMOUNTS:')
        print(f'   x = {x*1e-18} wei')
        print(f'   y = {y*1e-18} wei')

        p0 = my_math_contract.sqrtPatTick(tick0) 
        pA = my_math_contract.sqrtPatTick(tickLow) 
        pB = my_math_contract.sqrtPatTick(tickHigh)    
        print(f'   p0X96 : {p0} [{p_from_x96(p0)}]')
        print(f'   pAX96 : {pA} [{p_from_x96(pA)}]')
        print(f'   pBX96 : {pB} [{p_from_x96(pB)}]')
        
        LForAmounts = my_math_contract.LForAmounts(p0,pA,pB,x,y)
        print(f'   LForAmounts: {LForAmounts} Wei\n')
        
        return LForAmounts

    def amounts_for_liquidity(my_math_contract, tick0, tickLow, tickHigh, L):
        # x, y - amount 0/1 in wei
        print(f'\nAMOUNTS FOR LIQUIDITY:')
        print(f'   L = {L*1e-18} wei')

        p0 = my_math_contract.sqrtPatTick(tick0) 
        pA = my_math_contract.sqrtPatTick(tickLow) 
        pB = my_math_contract.sqrtPatTick(tickHigh)    
        print(f'   p0X96 : {p0} [{p_from_x96(p0)}]')
        print(f'   pAX96 : {pA} [{p_from_x96(pA)}]')
        print(f'   pBX96 : {pB} [{p_from_x96(pB)}]')
        
        (x,y) = my_math_contract.getAmountsForLiquidity(p0,pA,pB,L)
        print(f'   x: {x*1e-18} Wei')
        print(f'   y: {y*1e-18} Wei')
        
        return x,y

#
#--------------------- CHAINLINK/ CURRENCY CONVERSION
if True:

    # use chainlinks price-feed service to get the current price of an asset
    def getRoundData(rate_sym, roundID): # https://docs.chain.link/data-feeds/historical-data/
        
        price_feed_dict = NETWORK_TO_RATE_DICT[network.show_active()]
        price_feed_address = price_feed_dict[rate_sym]
        price_feed = interface.AggregatorV3Interface(price_feed_address)

        if not roundID:
            roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.latestRoundData()
        if roundID:
            roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.getRoundData(roundID)
        # latest rate
        #answer = float(Web3.fromWei(answer, "ether"))*1e10
        answer = answer*1e-8
        return answer

    def CurrencyConvert(
        currencyA_amount, 
        currencyAsym, 
        currencyBsym, 
        descriptor_str,
        network_csv_file
        ):
            # load_option :
                # 0 :: current network rate
                # 1 :: 
        
            rate_sym = currencyAsym + '_' + currencyBsym
            # pull rate from DataTables//CurrentRates//{network_csv_file}.csv
            if network_csv_file:
                data_file_path = f'DataTables//CurrentRates//{network_csv_file}.csv'
                df   = pd.read_csv(data_file_path)
                syms = df['symbols'].values

                #find row index of rate
                target_rate_indices = np.where(syms == rate_sym)[0]
                if len(target_rate_indices) > 1:
                    print(f'   multiple {rate_sym} rates in dict.')
                    sys.exit(0)
                
                rate_index   = target_rate_indices[0]
                rate_row     = df.iloc[rate_index]

                time         = rate_row.iloc[1]
                convert_rate = rate_row.iloc[2]
                #print(f'   time {time} ')
                #print(f'   rate {convert_rate} ')

            # Live price feed
            if network_csv_file==None:
                # rate_sym: e.g. ETH_USD [make sure its in DICTS.py price feed dictionary]
                # convert_rate*currencyA_amount = currencyB_amount
                convert_rate  = getRoundData(rate_sym, None)
            
            # calculate converted amount
            print(f'\nConversion [{rate_sym} = {convert_rate}]:')
            currencyB_amount = currencyA_amount*convert_rate
            print(f'   {descriptor_str}: {currencyA_amount*1e-18} {currencyAsym} ({currencyB_amount*1e-18} {currencyBsym}) ')
            return currencyB_amount


    def seconds_to_date(seconds_since_epoch):
        # input: seconds since last epoch. returns date and time format
        return datetime.datetime.fromtimestamp(seconds_since_epoch)

    def date_to_seconds(dateTime):
        # input: datetime.datetime(2023, 9, 1, 12, 30, 0)
        # returns: seconds since last epoch
        return  dateTime.timestamp()
    
    def get_latest_rates(networkFolder, updateRates, PRINT):
        # networkFolder does not need to be same as current network when updateRates == False.
        # when True, the folder should correspond the the current network.
        data_file_path = f'DataTables//CurrencyRates//{networkFolder}.csv'

        # if file exists, convert to dataframe
        if updateRates==False:
            if os.path.exists(data_file_path):
                df = pd.read_csv(data_file_path)
                df = df.set_index('symbols')
                if PRINT:
                    print(f'\nretrieved df: \n{df}')
            else:
                raise ValueError('no rates available. Run on live network and make sure network dictionary is updated.')
                

        # if file available 
        if updateRates:

            # find price feed dictionary that corresponds to network Folder selected.
            corresponding_network = networkFolder +'-main'
            rate_dict = NETWORK_TO_RATE_DICT[corresponding_network]

            data = np.array(['symbols','time', 'rates_usd'])
            for rateSym, addr in rate_dict.items():

                rndID, t_updated, rate = getRoundData(addr, None)
                T = seconds_to_date(t_updated)
                row_data = np.array([rateSym,T, rate])
                data     = np.vstack([data,row_data])
                if PRINT:
                    print(f'    {rateSym} : ${rate}')

                df = pd.DataFrame(data[1:] , columns=data[0]) 
                if PRINT:
                    print(f'\nsaving df: \n{df}')

                # save df to .csv
                df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
                df = df.set_index('symbols')

            syms         = df['symbols'].values
            syms         = row_data.iloc[0]
            time         = row_data.iloc[1]
            convert_rate = row_data.iloc[2]
        

        times = df['time'].values
        rates = df['rates_usd'].values
        syms  = df.index.to_numpy()
        
        return df,times, rates, syms


#--------------------- GAS CONTROLS


# set gas controls 
# * even if set_gas_limit==False, user will be warned with an input statement in the case that 
# gas price exceeds 30 gwei
gas_controls = True 
def gas_controls(account, set_gas_limit, priority_fee):
    print(f'\n--- GAS CONTROL CHECK:')
    GasBal = account.balance()
    print(f'   GasBal      : {GasBal*1e-18}')
    
    ALCHEMY_MAINNET = 'https://eth-mainnet.g.alchemy.com/v2/OeVRTKqUBtFwUKVXZnZC8z7Wjwvftb71'
    ALCHEMY_AMOYI   = 'https://polygon-amoy.g.alchemy.com/v2/AvwdU6g-OMNug__6SxF2Dl0St5MClFvB'
    ALCHEMY_AMOYII  = 'https://polygon-amoy.g.alchemy.com/v2/rzmbwZEeKcPzwcS_pk3ik__W99TLSWdm'
    INFURA_AMOY     = "https://polygon-amoy.infura.io/v3/ff7afa1fca9640caa5ce186fc906ba58"
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(ALCHEMY_MAINNET))

    gas_price    = w3.eth.gas_price  # current gas price [wei]
    print(f'   gas_price   : {int(gas_price*1e-9) } gwei')
    priority_fee = network.priority_fee("16 gwei")
    total_fee    = gas_price + priority_fee

    # set gas limit
    if set_gas_limit:
        max_cost  = 0.2*1e18    # enter desired max cost [wei]
        gas_limit = int(max_cost/total_fee) # [wei]
        network.gas_limit(gas_limit)
        print(f'   gas_limit   : {gas_limit}')
    # network.max_fee(gas_limit)

    if priority_fee:
        print(f'   priority fee: {network.priority_fee()*1e-9} gwei')

    if gas_price*1e-9 > 40:
        input('   gas fee is high. proceed?')


    # calculations:
    #  gas cost  = gas_used  * gas_price
    #  max cost  = gas_limit * gas_price

    # *example:
        # Gas price: 30.000000015 gwei   Gas limit: 5677256   Nonce: 7
        # ... Block: 45169776   Gas used: 5161142 (90.91%)
    print(' ')

    return GasBal