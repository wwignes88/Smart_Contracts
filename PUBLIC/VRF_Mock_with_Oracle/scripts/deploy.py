from brownie import (accounts, network, config, Contract,
                    mock2, mock3, LinkTokenI, LinkCoordinator, Wrapper)
from scripts.helpful_scripts import *
from web3 import Web3


def deploy_CHAINS(): 
    # *Note; web3 is only used here to check ETH balance for gas of transactions.
    w3 = Web3(Web3.HTTPProvider("https://eth-sepolia.g.alchemy.com/v2/QUhbF0JeaaHCTWmZdPWDQ8TTjX2mv4zE"))
    account  = get_account() ; my_address  = str(account)
    print(f'my gas balance: {w3.eth.get_balance(my_address)*1e-18}')
    
    
    #------------------------------------ DEPLOY MOCKS AND LINK CONTRACTS
    deployMocksAndLink = True
    if deployMocksAndLink:
         
        # deploy LINK
        print('\ndeploying Link...')
        link_  = LinkTokenI.deploy({"from": account})            ; _LINK = link_.address 

        # deploy MockV3Aggregator.sol (mock3_)
        print('deploying mockv3 aggregator ("mock3")...')
        _DECIMALS      = 18 
        _INITIALANSWER = (1/307.54)*1e18# 1 ETH = 307.54 LINK (*10**18 for Wei conversion)
        mock3_  = mock3.deploy(
            _DECIMALS, 
            _INITIALANSWER, 
            {"from": account}) ; 
        # update answer
        getLinkEthFeed(mock3_) #!!!!!!!! tx.wait?...why do I need to update answer? it should load

        print('updating LinkEth conversion rate...')
        _LINKETHFEED = mock3_.address 
        weiPerUnitLink = (1/307.54)*1e18
        updateLinkEthFeed(weiPerUnitLink, mock3_)
        getLinkEthFeed(mock3_)
        
        # deploy VRFCoordinatorV2Mock.sol (mock2_ or COORDINATOR)
        print('\ndeploying VRFV2 Coordinator ("mock2")...')
        BASE_FEE       = 100000000000000000  #                         ???
        GAS_PRICE_LINK = 1000000000 # 0.000000001 LINK per gas         ???
        mock2_ = mock2.deploy(
            BASE_FEE, 
            GAS_PRICE_LINK, 
            _LINK,
            _LINKETHFEED,
            {"from": account}) ; _COORDINATOR = mock2_.address 
        
        # deploy LINKCoordinator contract
        print('\ndeploying LinkCoordinator...')
        link_coordinator  = LinkCoordinator.deploy(_COORDINATOR, {"from": account}) ; _LINK_COORDINATOR = link_coordinator.address 
        # set LINKCoordinator address in COORDINATOR (mock2) contract. This will be used to verify that only
        # the LINKCoordinator calls the function 'onTokenTransfer'  which is used to track all deposits/ withdraws
        # of LINK token from the COORDINATOR contract.
        print('\nupdating LinkCoordinator address in coordinator contract...')
        mock2_.setLinkCoordinatorAddress(_LINK_COORDINATOR,{"from": account})
        
        # set configuration:
        print('\nsetting config of COORDINATOR (mock2)...')
        minimumRequestConfirmations  = 1
        maxGasLimit                  = 2500000   # (gwei) ~ 0.77 LINK
        # default stalenessSeconds val is 2,700;
        # a high value will cause us to rely on V3Aggregator for 
        # 'fallbackWeiPerUnitLink' value. seegetFeedData() 
        stalenessSeconds             = 60000 
        gasAfterPaymentCalculation   = 33285     # (gwei) ~ 0.01 LINK
        fallbackWeiPerUnitLink       = 3.25*1e15 # 3.25*1E15 Wei = 0.00325 ETH = 1 LINK
        feeConfig                    = (100000, 100000, 100000, 100000, 100000, 0, 0, 0, 0) # 0.1 LINK = 400,0000 gwei
        feeConfig                    = (100000, 100000, 100000, 100000, 100000, 0, 0, 0, 0) 
        setConfig(mock2_,
              minimumRequestConfirmations, 
              maxGasLimit,
              stalenessSeconds,
              gasAfterPaymentCalculation,
              fallbackWeiPerUnitLink,
              feeConfig,)
        


    


    #------------------------- DEPLOY WRAPPER + ORACLE
    deployWrapper_Oracle = True
    if deployWrapper_Oracle:
        if deployMocksAndLink ==  False:
            link_   = get_contract("link_") ;  _LINK         = link_.address
            mock3_  = get_contract("mock3_");  _LINKETHFEED  = mock3_.address
            mock2_  = get_contract("mock2_");  _COORDINATOR  = mock2_.address
            
        print('\ndeploying wrapper...')
        wrapper_  = Wrapper.deploy(
            _LINK, 
            _LINKETHFEED,
            _COORDINATOR,
            {"from": account}) ; _WRAPPER = wrapper_.address 

        print('\ndeploying oracle...')
        oracle_  = Oracle.deploy(
            _LINK, 
            _LINKETHFEED,
            _COORDINATOR,
            {"from": account}) ; _ORACLE = oracle_.address 
        
        # set Oracle as blockHashStore
        print('\nsetting Oracle as blochHashstore...')
        tx = mock2_.launchBlockHash(_ORACLE,{"from":account})
        tx.wait(2)
        
    #-------------------------- FUND CONTRACTS/ CREATE SUBSCRIPTION

    fundContracts_createSub = True
    if fundContracts_createSub:
        if deployMocksAndLink == False:
            link_   = get_contract("link_") ;  _LINK         = link_.address
            mock3_  = get_contract("mock3_");  _LINKETHFEED  = mock3_.address
            mock2_  = get_contract("mock2_");  _COORDINATOR  = mock2_.address
        if deployWrapper_Oracle == False:
            wrapper_  = get_contract("wrapper_");  _WRAPPER  = wrapper_.address
            oracle_   = get_contract("oracle_") ;  _ORACLE   = oracle_.address
            
        #fund mock2 coordinator and wrapper with LINK
        fundContractWithLink(link_ , _COORDINATOR, "Coordinator") 
        fundContractWithLink(link_ , _WRAPPER, "Wrapper") 
        
        #create and fund subscription
        subId = create_and_fund_subscription(mock2_)    
        
        #add wrapper as consumer
        add_consumer(subId, mock2_, _WRAPPER, 'Wrapper', True)  
    


    # deployed addresses:
    print('\ncontracts deployed @:')
    print(f'    _LINK        : {_LINK}')
    print(f'    _COORDINATOR : {_COORDINATOR }')
    print(f'    _LINKETHFEED : {_LINKETHFEED }')
    print(f'    _WRAPPER     : {_WRAPPER}')
    print(f'    _ORACLE      : {_ORACLE}')
    print(f'    _LINK_COORD. : {_LINK_COORDINATOR}')
    UpdateConfigAdresses(
        _LINK,
        _COORDINATOR,
        _LINKETHFEED,
        _WRAPPER,
        _ORACLE,
        _LINK_COORDINATOR)
    print(f'\naddresses have been updated in config file.')


def main():
    deploy_CHAINS()