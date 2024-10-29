from brownie import (accounts, interface, network, config, Contract, 
                     MyV2FlashLoan, testings) 
from scripts.Load.DICTS import *
from web3 import Web3
import numpy as np
import shutil, os, sys
import datetime
from pathlib import Path
import pandas as pd
from brownie.network import priority_fee, max_fee
# global variables:
w3 = Web3(Web3.HTTPProvider("https://eth-sepolia.g.alchemy.com/v2/QUhbF0JeaaHCTWmZdPWDQ8TTjX2mv4zE"))

#------------------------------------------ MISC GENERAL ACCOUNT/ CONTRACT FUNCTIONS
def get_account():
    account = accounts.add(config["wallets"]["from_key"])
    return account

account = get_account()

contract_to_mock = {"FlashLoan_": MyV2FlashLoan,
                    "testing_"  : testings}

def get_contract(contract_name):
    contract_type = contract_to_mock[contract_name]
    contract_address = config["networks"][network.show_active()][contract_name]
    contract = Contract.from_abi(
        contract_type._name, contract_address, contract_type.abi)
    return contract

def get_abi(contract_):
    # get a contracts ABI
    try: 
        print(f'\n {contract_.symbol(): }')
    except:
        pass
    input(f'\nabi: \n{contract_.abi}')

#---------------------  DATA FILE RETRIEVAL/ MANIPULATION

def get_data_df(data_file_path):
    # retrieve data table. Presumes df had only 'time' and 'rate' columns 
    # and was saved with index set to false (no numbers)
    
    data_file_path = f'DataTables//Tables//{ParentFolderName}//{period}//{sym}.csv'
    df = pd.read_csv(data_file_path)
    # df = df.set_index('time')
    # time = df.index.to_numpy()
    times = df['time'].values
    rates = df[sym].values
    
    return times,rates
    
def UpdateConfigAdresses(FlashLoanContract):
    # DEPLOYMENT; UPDATE CONFIG  ADDRESSES

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
                j = i+1; kill = False
                while kill == False:
                    line = READ_LINES[j]
                    if 'FlashLoan_' in line:
                        line = F'    FlashLoan_    : "{FlashLoanContract.address}"\n'
                        kill = True
                    data.append(line)
                
                    j += 1
                i=j-1
            i += 1
            

        #write new file:
        i = 0
        while i < len(data):
            write_obj.write(data[i]) # this is 'a' object
            i += 1

    # replace current file with new debugging file
    os.remove(_config)
    os.rename(dummy_file, _config)
    print('config file updated w/ deployment addresses\n\n')

    #----------------------------

#--------------------- check for/ update directory

def check_dir(dir_path):
    # Check if the directory already exists, create if not.
    path = Path(dir_path)
    
    if not path.is_dir():
        # Create the directory
        path.mkdir(parents=True, exist_ok=True)
        print(f"\nDirectory '{dir_path}' created successfully")
    else:
        pass

#---------------------------------------------------- TOKENS

def TokenContract(_token_):
    # get token contract
    return interface.IERC20(config["networks"][network.show_active()][_token_])

def depositTokens(TokenContract, DepositAmount, GasLimit, priorityFee, maxFee, native_to_usd):
    print('\n-------------DEPOSIT:')
    print(f'\ndepositing {DepositAmount*1e-18} {TokenContract.symbol()}  = ${DepositAmount*native_to_usd*1e-18}....')
    print(f'Gas Limit: {GasLimit} gwei  = ${GasLimit*native_to_usd*1e-9} \n ')

    priority_fee(priorityFee)  
    max_fee(maxFee)
    tx_hash = TokenContract.deposit({"value": DepositAmount, "gas_limit": GasLimit, "from": account})
    tx_hash.wait(1)
    gas_used     = tx_hash.gas_used
    block_number = tx_hash.block_number
    gas_price    = tx_hash.gas_price
    gas_cost     = gas_price*gas_used
    print(f'     Gas cost: {gas_cost*1e-9} ( % {gas_cost/DepositAmount} )')
    print('\n      ***   ')
    return gas_used, gas_price, gas_cost
    
def withdrawTokens(TokenContract, WithdrawAmount):
    # deposit AVAX into an ERC-20 compatable token 
    print(f'\nwithdrawing {TokenContract.symbol()}...')
    tx_hash = TokenContract.withdraw(WithdrawAmount, {"from": account})
    tx_hash.wait(1)
    print(f'withdrew {WithdrawAmount*1e-18} {TokenContract.symbol()}!')
    
def token_balance(token_contract, address):
    token_bal =  token_contract.balanceOf(address)
    return token_bal

def approve_erc20(amount, spender, erc20):
    print("---\nApproving ERC20 token...")
    erc20 = interface.IERC20(erc20.address)
    tx    = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!!")
    print('  ** ')
    return tx

#----------------------------------- CHAINLINK FUNCTIONS

def getRoundData(price_feed_address, roundID): # https://docs.chain.link/data-feeds/historical-data/
    price_feed = interface.AggregatorV3Interface(price_feed_address)
    
    if not roundID:
        printString = 'LATEST ROUND DATA:'
        roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.latestRoundData()
    if roundID:
        printString = 'HISTORICAL ROUND DATA:'
        roundId,answer,startedAt,updatedAt,answeredInRound = price_feed.getRoundData(roundID)

    # latest rate
    answer = float(Web3.fromWei(answer, "ether"))*1e10
    
    currently = current_seconds()
    Δt = currently-updatedAt # time since last update

    # times since last updated:
    months, weeks, days, hours, mins = days_hours_min(Δt, False)
    
    return roundId,float(updatedAt),days,hours,mins, answer

def get_latest_rates(dict_, PRINT):

    # get latest or most updated rate data for a network dictionary.
    dict_network = dict_["network"]
    if PRINT:
        print(f'\n{dict_network} rates:')
    data_file_path = f'DataTables//Tables//Current_Network_Rates//{dict_network}.csv'

    # --------------- update latest rates table
    if network.show_active()  in LIVE_ENVS:
        data = np.array(['symbols','time', 'rates_usd'])
        for symb, addr in dict_.items():
            if symb not in ['symb', 'network']:
                crypto_str, usd = symb.split('_')
                addr = dict_[symb]
                rndID,t_updated,d,h,m,rate = getRoundData(addr, None)
                T = seconds_t0_date(t_updated)
                symb_data = np.array([symb,T, rate])
                data      = np.vstack([data,symb_data])
                if PRINT:
                    print(f'    {crypto_str} : ${rate}')

        df = pd.DataFrame(data[1:] , columns=data[0]) 
        if PRINT:
            print(f'\nsaving df: \n{df}')
        # save df to .csv
        df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
        df = df.set_index('symbols')
        
    # ----------- pull most updated rate
    if network.show_active() not in LIVE_ENVS:
        if os.path.exists(data_file_path):
            df = pd.read_csv(data_file_path)
            df = df.set_index('symbols')
            if PRINT:
                print(f'\nretrieved df: \n{df}')

            
        else:
            raise ValueError('no rates available. Run on live network and make sure network dictionary is updated.')
            
        
    times = df['time'].values
    rates = df['rates_usd'].values
    syms  = df.index.to_numpy()
    
    return df,times, rates, syms

#----------------------------------- LENDING POOL FUNCTIONS

def get_lending_pool():
    lending_pool_addresses_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_addresses_provider"])
    lending_pool_address = lending_pool_addresses_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)
    return lending_pool

def get_borrowable_data(lending_pool, account, PRINT):
    (
        total_collateral_eth,
        total_debt_eth,
        available_borrow_eth,
        current_liquidation_threshold,
        ltv,
        health_factor,
    ) = lending_pool.getUserAccountData(account.address)

    total_collateral_eth  = float(total_collateral_eth)
    total_debt_eth        = float(total_debt_eth)
    available_borrow_eth  = float(available_borrow_eth)
    liquid_thresh         = float(current_liquidation_threshold)
    ltv = float(ltv)
    
    if PRINT:
        print('\nborrowable data:')
        print(f"    collateral : {total_collateral_eth*1e-18} ETH ")
        print(f"    debt       : {total_debt_eth*1e-18} ETH ")
        print(f"    borrow     : {available_borrow_eth*1e-18} ETH ")
        print(f"    liq. thr.  : {liquid_thresh} ETH ")
        print(f"    ltv        : {ltv}  ")
        print(f"    health     : {health_factor}  ")
    return (total_collateral_eth, available_borrow_eth, total_debt_eth)

def deposit_to_Pool(dep_amount,
                    lending_pool,
                    erc20,
                    priorityFee,
                    maxFee,
                    GasLimit):
    
    print('\n-------------DEPOSIT TO LENDING POOL:')
    # approve transaction
    approve_tx = approve_erc20(dep_amount,
                                lending_pool.address,
                                erc20)

    print(f'\ndepositing {erc20.symbol()} into lending pool...')
    tx = lending_pool.deposit(erc20.address, 
                                dep_amount, 
                                account.address, 
                                0, 
                                {"from": account})
    tx.wait(1);  print(f'\ndeposited {dep_amount*1e-18}!!')
    print('\n          *****      ')

#----------------------------------- TIME FUNCS

def seconds_t0_date(seconds_since_epoch):
    # input: seconds since last epoch. returns date and time format
    return datetime.datetime.fromtimestamp(seconds_since_epoch)

def date_to_seconds(dateTime):
    # input: datetime.datetime(2023, 9, 1, 12, 30, 0)
    # returns: seconds since last epoch
    return  dateTime.timestamp()

def current_dateTime():
    # current time in date-time format
    return datetime.datetime.now()

def current_seconds():
    # get current time since one year ago, in seconds.
    return current_dateTime().timestamp()

def days_hours_min(t, PRINT):
    # convert t (seconds) into days, hours, min, etc.
    # t = time in seconds
    
    mins  = t/60.0
    hours = mins/60.0
    days  = hours/24.0
    weeks = days/7
    months = weeks/4
    if PRINT:
        print(f'\n      days  : {days} ')
        print(f'      hours : {hours} ')
        print(f'      mins  : {mins} ')
    return months, weeks, days, hours, mins

def split_str(input_string):
    parts = input_string.split('_')
    return parts[0], parts[1]


