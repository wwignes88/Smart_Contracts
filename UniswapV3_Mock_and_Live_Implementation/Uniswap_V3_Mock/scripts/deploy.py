import time
from scripts.Load.helpful_scripts import get_accounts, gas_controls, get_contract, sys
from scripts.Load.BrownieFuncs import UpdateConfigAdresses
from brownie import (accounts, interface, network, config, Contract,
                    # V3-CORE/ PERIPERY MOCK CONTRACTS
                    MUniswapFactory, 
                    MUniswapFactoryII, 
                    MNonfungiblePositionManager,
                    MNonfungiblePositionManagerII,
                    MSwapRouter,
                    # UNISWAP LIBRARIES:
                    MCallbackValidation,
                    PoolHashGenerator, 
                    PoolIIHashGenerator,
                    MPoolAddress,
                    MTransferHelper,
                    # ZEPPELIN MOCKS
                    MERC20,
                    # MY CONTRACTS
                    MSwapper,
                    MliquidityMiner,
                    # MLiquidityStaker,
                    # TESTING
                    MyMath
                    )

# account  : 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce # Goog
# accountII: 0x6dFa1b0235f1150008B23B2D918F87D4775fBba9 # explorer

def deploy():
    print('\n=============== deploy =====================\n')

    # load account
    account = get_accounts(0) 
    gas_controls(account, set_gas_limit=False, priority_fee=False)

    # 0 ERC20 TOKENS
    # 1 V3 PERIPHERY LIBRARIES
    # 2 V3 CORE CONTRACTS
    # 3 Swapper contract
    # 4 Liquidity Miner contract
    deployments = [5]

    # ERC20s
    if 0 in deployments:
        print('\ndeploying ERC20...')
        
        token_list = ['weth', 'link','sand']
        for token_name in token_list:
            symbol    = token_name.upper()
            print(f'\n   deploying {symbol} ...')
            mockERC20 =  MERC20.deploy(token_name,
                                        symbol,
                                        {"from": account})
            
            UpdateConfigAdresses(mockERC20, token_name)

        #print('\ndeploying test...')
        #a_test = A.deploy({"from": account})    
        #UpdateConfigAdresses(a_test, 'a_test')
        sys.exit(0)

    # UNISWAP libraries
    if 1 in deployments:

        #---------- deploy TransferHelper library
        deploy_MTransferHelper = False
        if deploy_MTransferHelper:
            transfer_helper = MTransferHelper.deploy({"from": account})
            UpdateConfigAdresses(transfer_helper, 'MTransferHelper')
            
        #---------- deploy hashPoolCreationCode
        deploy_PoolHashGenerators = False
        if deploy_PoolHashGenerators:
            
            deployFirstPoolGenerator   = True 
            deploySecondPooltGenerator = True 
        
            if deployFirstPoolGenerator:
                hash_generator = PoolHashGenerator.deploy({"from": account})
                UpdateConfigAdresses(hash_generator, 'PoolHashGenerator')
                POOL_INIT_CODE_HASH = hash_generator.hashPoolCode()
                print(f'\nPOOL_INIT_CODE_HASH: \n    {POOL_INIT_CODE_HASH}')


            if deploySecondPooltGenerator:
                hash_generatorII = PoolIIHashGenerator.deploy({"from": account})
                UpdateConfigAdresses(hash_generatorII, 'PoolIIHashGenerator')
                POOL_INIT_CODE_HASHII = hash_generatorII.hashPoolCodeII()
                print(f'\nPOOL_INIT_CODE_HASHII: \n    {POOL_INIT_CODE_HASHII}')
                
            print('\n***update MPoolAddress.sol library with these values, save it, \
                ... THEN continue with deployment of ComputeAddressPool library.***\n\n')
            sys.exit(0)
            
        #---------- deploy ComputePoolAddress library
        deploy_MPoolAddress = True
        if deploy_MPoolAddress:
            pool_address_computer = MPoolAddress.deploy({"from": account})
            UpdateConfigAdresses(pool_address_computer, 'MPoolAddress')
   
        deploy_callbackValidation = True # uses MPoolAddress 
        if deploy_callbackValidation:
            callbackVal = MCallbackValidation.deploy({"from": account})
            UpdateConfigAdresses(callbackVal, 'MCallbackValidation')

        print(f'\n   V3 LIBRARIES DEPLOYED.\n')
        sys.exit(0)
        #----------------------------------------------------------
        
    # core/ periphery uniswap mock contracts
    if 2 in deployments:

        #---------- deploy mock factory

        deploy_MFactory = True
        if deploy_MFactory:
            print('\ndeploying factory MOCK...')
            factory =  MUniswapFactory.deploy({"from": account})
            UpdateConfigAdresses(factory, 'MFactory')
            time.sleep(3)
            factoryAddress = factory.address
        if not deploy_MFactory:
            factoryAddress = config["networks"][network.show_active()]['MFactory']

        deploy_MFactoryII = True
        if deploy_MFactoryII:
            print('\ndeploying factoryII MOCK...')
            factoryII =  MUniswapFactoryII.deploy({"from": account})
            UpdateConfigAdresses(factoryII, 'MFactoryII')
            time.sleep(3)
            factoryAddressII = factoryII.address
        if not deploy_MFactoryII:
            factoryAddressII = config["networks"][network.show_active()]['MFactoryII']
            
        #---------- deploy mock non-fungible position manager 
        deploy_MNonfungible = True
        if deploy_MNonfungible:
            print('\ndeploying  nonFungible MOCKS...')
            weth9 = config["networks"][network.show_active()]['weth']
            # not utilized unless interested in URI...I'm not, so enter any address
            tokenDescriptor = account.address # ???
            
            deployFungII = True 
            if deployFungII:
                ERC721managerII = MNonfungiblePositionManagerII.deploy(
                                        factoryAddress,
                                        factoryAddressII,
                                        weth9,
                                        {'from': account})
                UpdateConfigAdresses(ERC721managerII, 'MNonfungiblePositionManagerII')
                time.sleep(2)
            
            deployFung = True 
            if deployFung:
                if deployFungII:
                    ERC721managerIIAddress = ERC721managerII.address
                if not deployFungII:
                    ERC721managerIIAddress = config["networks"][network.show_active()]['MNonfungiblePositionManagerII']
                
                ERC721manager   = MNonfungiblePositionManager.deploy(
                                        ERC721managerIIAddress,
                                        tokenDescriptor,
                                        {'from': account})
                UpdateConfigAdresses(ERC721manager, 'MNonfungiblePositionManager')
        
        #---------- deploy mock SwapRouter
        deploy_MSwapRouter = True
        if deploy_MSwapRouter:

            print('\ndeploying  swap router MOCK...')
            weth9   = config["networks"][network.show_active()]['weth']
            
            # not utilized unless interested in URI...I'm not, so enter any address
            tokenDescriptor = account.address 
            swap_router     = MSwapRouter.deploy(
                                    factoryAddress,
                                    weth9,
                                    {'from': account})
            UpdateConfigAdresses(swap_router, 'MSwapRouter')
            routerAddress = swap_router.address

        print(f'\n   V3-CORE DEPLOYED.\n')
        sys.exit(0)
        #----------------------------------------------------------
    
    # Swapper
    if 3 in deployments:
        router  = get_contract('MSwapRouter')
        fee     = 3000
        print('\ndeploying swapper...')
        swapper = MSwapper.deploy(fee,
                                router, 
                                {"from": account})
        
        UpdateConfigAdresses(swapper, 'MSwapper')

    # Liquidity Miner
    if 4 in deployments:
        ERC721manager = config["networks"][network.show_active()]['MNonfungiblePositionManager']
        ERC721managerII = config["networks"][network.show_active()]['MNonfungiblePositionManagerII']
        print('\ndeploying Liquidity Miner...')
        liquidMOCK = MliquidityMiner.deploy(ERC721manager,
                                            ERC721managerII,
                                            {"from": account})
        UpdateConfigAdresses(liquidMOCK, 'MliquidityMiner')

    # MyMath
    if 5 in deployments:
        print('\ndeploying MyMath...')
        my_math = MyMath.deploy( {"from": account} )
        UpdateConfigAdresses(my_math, 'MyMath')

    """ XXX
    # Liquidity Staker
    if 6 in deployments:
        print('\ndeploying Liquidity Staker...')
        factory = config["networks"][network.show_active()]['MFactory']
        ERC721manager = config["networks"][network.show_active()]['MNonfungiblePositionManager']
        
        # the max amount of seconds into the future the incentive startTime can be set
        _maxIncentiveStartLeadTime  =  60*60 # one hour 
        # the max duration of an incentive in seconds
        _maxIncentiveDuration       =  (60*60*24)*30*12 # one year 
        
        staker  = MLiquidityStaker.deploy(factory,
                                          ERC721manager,
                                          _maxIncentiveStartLeadTime,
                                          _maxIncentiveDuration,
                                          {"from": account})
        UpdateConfigAdresses(staker, 'MLiquidityStaker')
        XXX
        """

def main():
    deploy()

