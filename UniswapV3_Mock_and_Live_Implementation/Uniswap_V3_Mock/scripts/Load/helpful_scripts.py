from brownie import (accounts, interface, network, config, Contract,
                    # V3-CORE/ PERIPERY MOCKS
                    MUniswapFactory, 
                    MUniswapFactoryII,
                    MNonfungiblePositionManager,
                    MNonfungiblePositionManagerII,
                    MSwapRouter,
                    # UNISWAP LIBRARIES:
                    MCallbackValidation,
                    MPoolAddress,
                    # ZEPPELIN MOCKS
                    MERC20,
                    # MY CONTRACTS
                    MSwapper,
                    MliquidityMiner,
                    # MLiquidityStaker,
                    # TESTING
                    MyMath
                    )
import sys
import time, datetime
import math
from scripts.Load.DICTS import NETWORK_TO_RATE_DICT




#------------------------------------------ACCOUNT/ CONTRACTS
if True:
    # load account
    def get_accounts(option):
        if option == 0:
            return accounts.add(config["wallets"]["EXPLOR_key"])
        if option == 1:
            return accounts.add(config["wallets"]["GOOG_key"])

    def getERC20(contractAddress): 
        return interface.myERC20(contractAddress)

    CONTRACT_TO_MOCK = {# zeppelin mocks
                        'weth'     : MERC20,
                        'link'     : MERC20,
                        'sand'     : MERC20,
                        # uniswap v3 libraries
                        'MPoolAddress'       : MPoolAddress,
                        'MCallbackValidation': MCallbackValidation,
                        # uniswap v3-core/ periphery mocks
                        'MFactory'           : MUniswapFactory,
                        'MFactoryII'         : MUniswapFactoryII,
                        'MNonfungiblePositionManager'  : MNonfungiblePositionManager,
                        'MNonfungiblePositionManagerII': MNonfungiblePositionManagerII,
                        'MSwapRouter'        : MSwapRouter,
                        # my mocks
                        'MliquidityMiner'    : MliquidityMiner,
                        #'MLiquidityStaker'   : MLiquidityStaker,
                        'MSwapper'           : MSwapper,
                        # misc testing
                        'MyMath'   : MyMath}

    def get_contract(contract_name):
        # get contract on active network
        contract_type = CONTRACT_TO_MOCK[contract_name]
        contract_address = config["networks"][network.show_active()][contract_name]
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi)
        return contract
    

#------------------------- ERC20 TOKEN BALANCE/ APPROVE/ FUND
if True:
    
    # get token balnce of address_. print this balance if PRINT==True.
    # mint 150 ETH if MINT==True and if token balance < 30 ETH. 
    def get_Token_bal(Token, address_, str_, PRINT, MINT, account):
        Token_balance = Token.balanceOf(address_)
        if PRINT:
            print(f'    {str_} {Token.symbol()} bal: {Token_balance*1e-18}')
        if MINT: 
            if Token_balance*1e-18 < 30:
                print(f'    minting 100 {Token.symbol()} to {str_}...')
                tx = Token.mint(150*1e18, address_, {"from": account})
                tx.wait(1)
        return Token_balance

    # check balance of an entire list of tokens...mint if needed
    def getBals(tokenDict, address, STRING, PRINT, MINT, account):
        bals = []
        for token in tokenList:
            bals.append(get_Token_bal(token, address, STRING, PRINT, MINT))
        return bals
    
    # approve a contract to spent amount of token
    def approve_contract_spender(amount, token, contract, account, contract_name):
        _allowed = token.allowance(account.address, contract.address)

        # if _allowed amount is less than desired amount, approve
        if _allowed < 0.9*amount :
            print(f'\napproving {contract_name} for {amount*1e-18} {token.symbol()}...')
            time.sleep(2)
            # approve(address spender, uint256 amount) 
            tx = token.approve(contract.address,
                                    amount,
                                    {"from": account})
            tx.wait(1)
            _allowed = token.allowance(account.address, contract.address)
        print(f'    {contract_name} allowance over my {token.symbol()} tkns: {_allowed*1e-18}')
        return _allowed

    def printABI(_contract):
        # OPTION = 1 :: contract functions
        # OPTION = 1 :: contract events
        argumentsList = ["inputs", "outputs"]
        ABI = _contract.abi
        for listItem in ABI:
            print(f'\n--------')
            print(f'{listItem["name"]}')
            for key, value in listItem.items():
                if key in argumentsList: 
                    print(f'   {key}: ')
                    for variableDicts in value:
                        print(f'      {variableDicts["name"]}')
                if key not in argumentsList and key != "name": 
                    print(f'   {key}: {value}')
                
# ------------------ UNISWAP 
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
    def getNextTick(pool, tickCurrent, tick_spacing, zeroForOne):
        my_math   = get_contract('MyMath')
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
        tickNextInfoDict = getTickInfo(pool, tickNext, False)     
        
        if tickNext < MIN_TICK:
            tickNext = MIN_TICK
            print(f'     tickNext < MIN TICK')
            sys.exit(0)
            
        return tickNext, tickNextInfoDict
  
  
    # get position from ERC721 manager (nonfungiblePositionManger) of a given [minted] tokenId
    def getNFTPosition(NonFungibleManagerII, tokenId, account, PRINT):
        vals          = NonFungibleManagerII.positions(tokenId,  {"from": account})
        params        = {}
        nonce         = vals[0]; params['nonce']        = nonce
        operator      = vals[1]; params['operator']     = operator
        token0        = vals[2]; params['token0']       = getERC20(token0)
        token1        = vals[3]; params['token1']       = getERC20(token1)
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
    def getPoolPosition(pool, owner, tickLower, tickUpper, PRINT):
        # position updated in pool._update
        # liquidity updated analgous to Tick.sol :: liquidityGross (so always added)
        vals          = pool.getPoolPosition(owner, tickLower, tickUpper)
        params        = {}
        liquidity     = vals[0]; params['liquidity']     = liquidity
        feeGrowthIn0  = vals[1]; params['feeGrowthIn0']  = feeGrowthIn0
        feeGrowthIn1  = vals[2]; params['feeGrowthIn1']  = feeGrowthIn1
        tokensOwed0   = vals[3]; params['tokensOwed0']   = tokensOwed0
        tokensOwed1   = vals[4]; params['tokensOwed1']   = tokensOwed1

        if PRINT:
            print(f'\nPOOL POSITION:')
            for key, value in params.items():
                print(f'   {key}: {value}')
               
         
        return params
    
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
            print(f'\nslot0:')
            print(f'    Tick0    : {tick}')
            print(f'    sqrtP    : {sqrtPriceX96}')
  
            
            #print(f'    obs.Ind.     : {observationIndex}')
            #print(f'    obs.Card.    : {obsCard}')
            #print(f'    obs.Card.Next: {obsCardNext}')
            #print(f'    feeProt.     : {feeProtocol}')
            print(f'    unlocked     : {unlocked}')
            
        return params

    # load uniswapV3Pool. will create and initialize pool if needed.
    # 
    def loadPool(tokenA, tokenB, fee, account):

        if fee not in [500,3000,10000]:
            print('\ninvalid fee.')
            sys.exit(0)
        factory   = get_contract('MFactory')
        factoryII = get_contract('MFactoryII')
        zero_address = '0x0000000000000000000000000000000000000000'
        pool_addr    = factory.getPool(tokenA, tokenB, fee)
        pool_addrII  = factoryII.getPoolII(tokenA, tokenB, fee, {'from':account})  
        
        # create pool if needed.
        if pool_addrII == zero_address:
            print(f'\nno poolII deployed. creating pool {tokenA.symbol()}/{tokenB.symbol()}...')
            txII = factoryII.createPoolII(tokenA, tokenB, fee, {'from':account})
            txII.wait(1)
            pool_addrII  = factoryII.getPoolII(tokenA, tokenB, fee, {'from':account})
        
        if pool_addr == zero_address:
            print(f'\nno pool deployed. creating pool {tokenA.symbol()}/{tokenB.symbol()}...')
            tx = factory.createPool(tokenA, tokenB, fee, {'from':account})
            tx.wait(1)
            pool_addr  = factory.getPool(tokenA, tokenB, fee, {'from':account})
        
        # check that MPoolAddress.sol library is accurately calculating the pool address
        # this is vital to a number of processes/ function in the uniswap V3 protocol, 
        # so it is worth checking, although it need not be checked EVERY time a pool 
        # gets loaded, so can be set to False after a couple checks that its working.
        checkAddressComputed = True
        if checkAddressComputed:
            pool_address_computer = get_contract('MPoolAddress')
            poolAddress = pool_address_computer.computePoolAddress(
                            factory.address, 
                            tokenA.address,
                            tokenB.address,
                            fee)
            
            poolIIAddress = pool_address_computer.computePoolAddressII(
                            factoryII.address, 
                            tokenA.address,
                            tokenB.address,
                            fee)
            
            if pool_addr != poolAddress or poolIIAddress != pool_addrII:
                print(f'\n    [LoadPool] :: !!! pool address calculation error !!! ')
                print(f'      pool_addr  : {pool_addr}')
                print(f'         *computed pool   : {poolAddress}')
                print(f'      pool_addrII: {pool_addrII}')
                print(f'         *computed poolII : {poolIIAddress}')
                print(f'\n*      factory    : {factory.address}')
                print(f'*      factoryII  : {factoryII.address}')           
            
                sys.exit(0)
        
        # get pool contract
        pool = interface.IV3Pool(pool_addr)
        
        # pool parameters
        liquidity    = pool.liquidity()
        slot0        = getslot0(pool, False)
        tick_spacing = int(pool.tickSpacing() )
        
        #xxxprint(f'\npool address 2: {pool.address}')
        #xxxprint(f'slot0["unlocked"] : {slot0["unlocked"] }')
        #xxxprint(f'liquidity: {liquidity}')
        #xxxsys.exit(0)
            
        # initialize pool if needed
        if not slot0['unlocked'] :
            print(f'\ninitializing pool {tokenA.symbol()}/ {tokenB.symbol()} pool...')
            rateDict = NETWORK_TO_RATE_DICT[network.show_active()]
            
            # pool price initialized to p=1
            p = 1
            p0_X96  = p_to_x96(p)
            
            # not implemented: set pool price by ratio of token0, token1 prices.
            """
            priceAddressA = rateDict[tokenA.symbol() + '_usd']
            priceAddressB = rateDict[tokenB.symbol() + '_usd']
            p0 = getRoundData(priceAddressA, None) 
            p1 = getRoundData(priceAddressB, None)
            
            print(f'\n   p0 = {p0})
            print(f'   p1 = {p1})
            
            p  = p1/p0 # pool price
            p0_X96  = p_to_x96(p)
            tick0   = tick_at_sqrt(p0_X96)   
            if abs(tick0) < MAX_TICK:
                print(f'\n   !! invalid pool price !!')
                sys.exit(0)
            """
            
            print(f'\n   initializing w/ price p = {p0_X96} ')  
            tx     = pool.initialize(p0_X96, {"from": account})
            tx.wait(1)
            slot0 = getslot0(pool, False)
                
        return (pool, slot0, liquidity, tick_spacing)



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


#
#--------------------- CHAINLINK
if True:

    # use chainlinks price-feed service to get the current price of an asset
    def getRoundData(price_feed_address, roundID): # https://docs.chain.link/data-feeds/historical-data/
        price_feed = interface.AggregatorV3Interface(price_feed_address)

        if not roundID:
            roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.latestRoundData()
        if roundID:
            roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.getRoundData(roundID)
        # latest rate
        #answer = float(Web3.fromWei(answer, "ether"))*1e10
        anser = answer*1e-8
        return answer


#--------------------- GAS CONTROLS


# set gas controls 
# * even if set_gas_limit==False, user will be warned with an input statement in the case that 
# gas price exceeds 30 gwei
gas_controls = True 
def gas_controls(account, set_gas_limit, priority_fee):
    print(f'\n--- GAS CONTROL CHECK:')
    GasBal = account.balance()
    print(f'   GasBal      : {GasBal*1e-18}')
    
    ALCHEMY_NODEI  = 'https://polygon-amoy.g.alchemy.com/v2/AvwdU6g-OMNug__6SxF2Dl0St5MClFvB'
    ALCHEMY_NODEII = 'https://polygon-amoy.g.alchemy.com/v2/rzmbwZEeKcPzwcS_pk3ik__W99TLSWdm'
    INFURA_NODE   = "https://polygon-amoy.infura.io/v3/ff7afa1fca9640caa5ce186fc906ba58"
    CardonaAlchemy = "https://polygonzkevm-cardona.g.alchemy.com/v2/rf-_5NKGQkbQuR5rPiTHjeFEzKqxOoUU"
    from web3 import Web3
    w3 = Web3(Web3.HTTPProvider(INFURA_NODE))


    gas_price    = w3.eth.gasPrice;  # current gas price [wei]
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