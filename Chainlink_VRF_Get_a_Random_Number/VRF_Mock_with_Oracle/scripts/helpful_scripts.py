from brownie import (accounts, network, config, Contract, 
                     mock2, mock3, LinkTokenI, LinkCoordinator, Wrapper, Oracle) 
from web3 import Web3
import numpy as np
import shutil, os, sys

# global variables:
w3 = Web3(Web3.HTTPProvider("https://eth-sepolia.g.alchemy.com/v2/QUhbF0JeaaHCTWmZdPWDQ8TTjX2mv4zE"))

# number of block confirmations to await for transactions.
Confirmations = 2


#=======================================================================================
#------------------------------------------------------------ GET ACCOUNT(S)
def get_account():
    # !! **input(f'network: {config["networks"][network.show_active()]}')
    if network.show_active() == "sepolia":
        account = accounts.add(config["wallets"]["from_key"])
        #print(f'my gas balance: {w3.eth.get_balance(account.address)*1e-18} ETH')
        return account
    if network.show_active() == "development":
        account = accounts[0]
        #print(f'my gas balance: {account.balance()*1e-18} ETH')
        return account
    print('must run on "develpment" or "sepolia" network!')
    sys.exit(0)




#--------------------------------------------------  GET CONTRACT(S)
contract_to_mock = {"mock2_": mock2,
                    "mock3_": mock3,
                    "link_" : LinkTokenI,
                    "wrapper_"  : Wrapper,
                    "oracle_": Oracle,
                    "link_coordinator": LinkCoordinator}

def get_contract(contract_name):
    contract_type = contract_to_mock[contract_name]
    contract_address = config["networks"][network.show_active()][contract_name]
    contract = Contract.from_abi(
        contract_type._name, contract_address, contract_type.abi)
    return contract



#------------------------------------------------ MANAGE SUBSCRIPTION(S)
# *'coordinator' is contract from 'get_contract(contract_name)'
# PRINT = bool (T/F)
account  = get_account() ; my_address  = str(account)
# get subscription info
def getSubInfo(subId, mock2, PRINT):
    subInfo = mock2.getSubscription(subId,{"from": account})
    if PRINT:
        print(f'\nsubscription {subId} info:')
        BAL = subInfo[0] ; print(f'   balance   : {np.round(BAL*1e-18,8)} LINK')
        REQ = subInfo[1] ; print(f'   # requests: {REQ}')
        OWN = subInfo[2] ; print(f'   owner     : {OWN}')
        CON = subInfo[3] ; print(f'   consumers : {CON}')
    return subInfo

def create_and_fund_subscription(mock2):
    # owner of sub will be msg.sender

    # create subscription
    print('\ncreating subscription...')
    tx = mock2.createSubscription({"from": account}) 
    tx.wait(Confirmations)
    subId = mock2.getCurrentSubId({"from": account}) 
      
    # fund subscription  
    fund_subscription(subId, mock2)
    
    # add owner as consumer
    owner = getSubInfo(subId, mock2, False)[2] 
    add_consumer(subId, mock2, owner, 'owner', False)
    return subId

# add consumer to subscription 
def add_consumer(subId, coordinator, consumer_address, str_, PRINT):
    print(f'\nadding {str_} as consumer to subscription {subId}...') 
    tx = coordinator.addConsumer( subId , consumer_address,  {"from": account})
    tx.wait(Confirmations)
    print(f'added {str_} to subscription {subId}')
    if PRINT:
        getSubInfo(subId, coordinator, True)
    
def fund_subscription(subId, mock2):
    dep_val = int(100*1e18) # 10 LINK
    print(f'\nfunding subscription {subId}...')
    tx = mock2.fundSubscription(subId, dep_val, {"from": account})
    tx.wait(1)
    print(f'funded subscription {subId}.\n')   



# remove consumer from subscription
def remove_consumer(subId, consumer_address):
    print('removing consumer...')
    tx = mock2.removeConsumer( subId , consumer_address,  {"from": account})
    tx.wait(1)
    print(f'removed {consumer_address} as a consumer to subscription {subId}')
    getSubInfo(subId)


def fundContractWithLink(link , contractAddress, str_):
    dep_val = int(100*1e18) # 10 LINK
    print(f'\nfunding {str_} contract...')
    fund_direct_tx = link.transfer(contractAddress, dep_val, {"from": account})
    fund_direct_tx.wait(1) 
    print(f'funded  {str_} contract.\n')  


# get relevant balances
def getLINKBalances():
    COORDINATOR  = get_contract("mock2_") # get VRFCoordinator mock contract.
    WRAPPER      = get_contract("wrapper_")
    ORACLE       = get_contract("oracle_")
    LINK         = get_contract("link_")
    LINKCoordinator = get_contract("link_coordinator")
    account      = get_account() ; my_address  = str(account)
    
    _subId      = COORDINATOR.getCurrentSubId({"from": account}) 
    
    my_LINK_bal = COORDINATOR.LINK_balance(my_address,    {"from": account})  
    subBal      = getSubInfo(_subId, COORDINATOR, False)[0]
    totalBal    = COORDINATOR.getTotalBalance({"from": account})
    OracleBal   = COORDINATOR.LINK_balance(ORACLE.address,    {"from": account})  
    print('\nContrac/account LINK balances:')
    print(f'    MY           LINK: {my_LINK_bal}')  
    print(f'    Subscription LINK: {subBal}')
    print(f'    Oracle       LINK: {OracleBal}')  
    print(f'    Coordinator  LINK: {totalBal}')
    
    OracleWithdrawBal = COORDINATOR.withdrawBal(ORACLE.address,{"from": account})
    SenderWithdrawBal = COORDINATOR.withdrawBal(ORACLE.address,{"from": account})
    print(f'withdraw LINK balances:')  
    print(f'    Oracle withdrawable LINK     : {OracleWithdrawBal}')  
    print(f'    Coordinator withdrawable LINK: {SenderWithdrawBal}\n')

# get (aggrevatorv3 or mock3 contract) round data
def getLinkEthFeed(lINK_ETH_FEED):
    latestRndData = lINK_ETH_FEED.latestRoundData({"from": account})
    print(f'latestRndData:')
    print(f'    roundId   : {latestRndData[0]}')
    print(f'    answer    : {latestRndData[1]}')
    print(f'    startedAt : {latestRndData[2]}')
    print(f'    updatedAt : {latestRndData[3]}')
    print(f'    answeredIn: {latestRndData[4]}')

# updated linkEthFeed (aggrevatorv3 or mock3 contract) with wei/eth conversion rate
def updateLinkEthFeed(weiPerUnitLink, lINK_ETH_FEED):
    lINK_ETH_FEED.updateAnswer(weiPerUnitLink, {"from": account})

# set coordinator configuration
def setConfig(COORDINATOR,
              minimumRequestConfirmations, 
              maxGasLimit,
              stalenessSeconds,
              gasAfterPaymentCalculation,
              fallbackWeiPerUnitLink,
              feeConfig,):
    
        print('setting config...')
        COORDINATOR.setConfig(
            minimumRequestConfirmations,
            maxGasLimit,
            stalenessSeconds,
            gasAfterPaymentCalculation,
            fallbackWeiPerUnitLink,
            feeConfig,
            {"from": account}
        )
        print('config set!')

# get explicit (unhashed) request commitment      
def getExplicitRequestCommitment(requestId):
    COORDINATOR    = get_contract("mock2_")
    
    #get hashed commit (what the code actually uses)
    hashed_commit = COORDINATOR.getHashedCommit(requestId)
    print(f'\nHashed commit: {hashed_commit}')
    
    #get readable (explicit) version of commit
    ExplicitCommit = COORDINATOR.getExplicitCommit(requestId)
    print('\nexplicit commit:')
    print(f'---blockNum          : {str(ExplicitCommit[0])[0:8]}...')
    print(f'---subId             : {ExplicitCommit[1]}')
    print(f'---callbackGasLimit : {ExplicitCommit[2]}')
    print(f'---numWords          : {ExplicitCommit[3]}')
    print(f'---sender            : {str(ExplicitCommit[4])[0:8]}...')
        

def UpdateConfigAdresses(
    LINK,
    COORDINATOR,
    AGGREGATOR,
    WRAPPER,
    ORACLE,
    LINK_COORDINATOR):
    NETWORK = network.show_active()
    _dir = os.getcwd() #; print(f'current dir: {_dir}')
    _config = _dir + '\\brownie-config.yaml' ; print(f'\n_config: {_config}\n')
    dummy_file    = _config + '.bak'
    
    with open(_config, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        
        READ_LINES  = read_obj.readlines() # file to be read
        data = []
        i = 0
        while i < len(READ_LINES):  
            
            line = READ_LINES[i]
            data.append(line)
            if NETWORK in line:
                j = i+1
                line = F'    link_    : "{LINK}"\n'
                data.append(line) 
                line = F'    mock2_   : "{COORDINATOR}"\n'
                data.append(line)
                line = F'    mock3_   : "{AGGREGATOR}"\n'
                data.append(line)
                line = F'    wrapper_ : "{WRAPPER}"\n'
                data.append(line)
                line = F'    oracle_  : "{ORACLE}"\n'
                data.append(line)
                line = F'    link_coordinator  : "{LINK_COORDINATOR}"\n'
                data.append(line)
                i = j+5

            i += 1

        #write new file:
        i = 0
        while i < len(data):
            write_obj.write(data[i]) # this is 'a' object
            i += 1

    # replace current file with new debugging file
    os.remove(_config)
    os.rename(dummy_file, _config)