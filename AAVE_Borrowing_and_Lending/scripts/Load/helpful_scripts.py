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
def get_ALT_account():
    EXPLORaccount = accounts.add(config["wallets"]["EXPLOR_key"])
    return  EXPLORaccount

def get_account():
    GOOGaccount   = accounts.add(config["wallets"]["GOOG_key"])
    return GOOGaccount

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

def depositTokens(account,
                  TokenContract, 
                  DepositAmount, 
                  GasLimit, 
                  priorityFee, 
                  maxFee, 
                  eth_usd,
                  eth_native,
                  eth_asset,
                  native_usd,
                  native_asset,
                  network_sym):

    print('\n[get tokens]:')
    print(f'\ndepositing \n\
        = {DepositAmount*1e-18} {network_sym} <-------\n\
            = {DepositAmount*native_asset*1e-18} {TokenContract.symbol()}\n\
                = {DepositAmount*native_usd*1e-18} USD\n\
                    ....')

    priority_fee(priorityFee)  
    max_fee(maxFee)

    try:
        tx_hash = TokenContract.deposit({"value": DepositAmount, "from": account})
        tx_hash.wait(1)
        gas_used     = tx_hash.gas_used
        block_number = tx_hash.block_number
        gas_price    = tx_hash.gas_price
        gas_cost     = gas_price*gas_used
        print(f'     Gas cost: {gas_cost*1e-9} ETH ( % {gas_cost/DepositAmount} )')

        return gas_used, gas_price, gas_cost
    
    except Exception as e:
        print(f'\n    !!! failed to deposit {TokenContract.symbol()} !!!')
        print(f"        An error occurred: {str(e)}\n")
        print('     * check if this contract has a deposit function (DAI, for example, does not)\n')
        return 0, 0, 0
    
def withdrawTokens(account, TokenContract, WithdrawAmount):
    # deposit AVAX into an ERC-20 compatable token 
    print(f'\nwithdrawing {TokenContract.symbol()}...')
    tx_hash = TokenContract.withdraw(WithdrawAmount, {"from": account})
    tx_hash.wait(1)
    print(f'withdrew {WithdrawAmount*1e-18} {TokenContract.symbol()}!')
    
def tok_bal(token_contract, address, PRINT):
    token_bal = token_contract.balanceOf(address)
    if PRINT:
        print(f'    {token_contract.symbol()} bal: {token_bal*1e-18}')
    return token_bal

def approve_erc20(account, amount, spender, erc20):
    print("---\nApproving ERC20 token...")
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    spender_allowance = erc20.allowance(account.address, spender) 
    print(f"Spender approved for {spender_allowance*1e-18} {erc20.symbol()}")
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
    liquid_thresh         = float(current_liquidation_threshold)*1e-4
    ltv = float(ltv)*1e-4
    
    if PRINT:
        print('\nborrowable data:')
        print(f"    collateral : {total_collateral_eth*1e-18} ETH ")
        print(f"    debt       : {total_debt_eth*1e-18} ETH ")
        print(f"    borrow     : {available_borrow_eth*1e-18} ETH ")
        print(f"    liq. thr.  : {liquid_thresh} ETH ")
        print(f"    ltv        : {ltv}  ")
        print(f"    health     : {health_factor}  ")
    return (total_collateral_eth, total_debt_eth, available_borrow_eth,
            liquid_thresh, ltv,health_factor)

    #------------ get lending info.

def eth_print(c,b,d, asset, eth_usd, eth_asset):
    # print collateral, borrowable, and debt values in GWEI, USD, and in selected currency.
    _gwei = 1e-9
    _wei  = 1e-18

    print('\nlending info:')
    print(f'    collateral: {np.round(c*_gwei,4)} GWETH \
 = ${np.round(c*_wei*eth_usd, 6)} \
 = {np.round(c*eth_asset*_wei, 9)} {asset.symbol()}')
    
    print(f'    borrowable: {np.round(b*_gwei,4)} GWETH \
 = ${np.round(b*_wei*eth_usd, 6)} \
 = {np.round(b*eth_asset*_wei, 9)} {asset.symbol()}')
    
    print(f'    debt      : {np.round(d*_gwei,4)} GWETH \
 = ${np.round(d*_wei*eth_usd, 6)} \
 = {np.round(d*eth_asset*_wei, 9)} {asset.symbol()}')
    
def deposit_to_Pool(account, 
                    dep_amount,
                    lending_pool,
                    erc20,
                    priorityFee,
                    maxFee,
                    GasLimit):

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
    tx.wait(1);  print(f'\ndeposited!!')

def check_gas_ratio(transaction_amount, GasLim):
    # check percentile of transaction amount to gasLimit
    # transaction_amount should be entered in ETH WEI
    tx_amount_gwei = transaction_amount*1e-9
    percentage = GasLim/tx_amount_gwei
    if percentage > 0.95:
        input(f'\n Warning! Gas limit is more than %5 of this transaction amount (it is {percentage}). Press any key to proceed.')
    return percentage

def bitmask_reserve_config(bitmask, PRINT):
    # see getConfiguration in documentation. This function will decode the bitmask.
    # getConfiguration returns list, but here input only one entry of that list, i.e. 
    # getConfiguration returns (bitmask,) so input first entry of return value.
    
    b_ = format(bitmask, '079b')  # Format as a binary string with leading zeros

    #print(f'b_ = {b_}')

    LTV        = int(b_[0:16], 2)*1e-4       
    Liq_thresh = int(b_[16:32], 2)*1e-4  
    Liq_bonus  = int(b_[32:48], 2)*1e-4  
    Decimals   = int(b_[48:56], 2)       
    res_active = int(b_[56], 2)          
    res_froze  = int(b_[57], 2)        
    Borrow     = int(b_[58], 2)          
    sBorrow    = int(b_[59], 2)          
    Reserved   = int(b_[60:64], 2)      
    Reserved_f = int(b_[64:80], 2)*1e-4  

    if PRINT:
        print(f'    LTV        : {LTV} ')
        print(f'    Liq_thresh : %{Liq_thresh}') # liquidation threshhold
        print(f'    Liq_bonus  : %{Liq_bonus}') # 
        print(f'    Decimals   : {Decimals}') # 
        print(f'    res_active : {res_active}') # 
        print(f'    res_froze  : {res_froze}') # 
        print(f'    Borrow     : {Borrow}') # 
        print(f'    sBorrow    : {sBorrow}') # 
        print(f'    LiqReserved: {Reserved}') # 
        print(f'    Reserved_f : %{Reserved_f}') # 
        
    dict_ = {"LTV": LTV, "Liq_thresh": Liq_thresh, "Liq_bonus": Liq_bonus, 
             "Decimals": Decimals, "res_active": res_active, 
            "reserve_froze": res_froze, "Borrow": Borrow, 
            "sBorrow": sBorrow, "Reserved": Reserved, "Reserved_f": Reserved_f}
    list_ = [LTV, Liq_thresh, Liq_bonus, Decimals, res_active, 
            res_froze, Borrow, sBorrow, Reserved, Reserved_f]
    return list_, dict_

def get_asset_configuration(lending_pool, Token, PRINT):
    # get LTV, liquidation threshhold, see if reserve is active or frozen, etc.
    
    asset_config  = lending_pool.getConfiguration(Token.address)
    if PRINT:
        print('\n asset configuration:')
        print(f'\n{Token.symbol()} :')
        print(f'    bitmask(s) : {asset_config}')
    bitmask = asset_config[0]
    config_list, config_dict = bitmask_reserve_config(bitmask, PRINT)
    return config_list, config_dict 
    
def bitmask_user_config(bitmask, reserve_list):
    # for each asset in the above list, will return bits representing 
    # if it is used as collateral and if it is borrowed, respectively.
    bitmask = bitmask[2:]
    print(f'   bitmask: {bitmask}')
    
    count = 0
    c_list = []
    b_list = []
    
    i = len(bitmask) - 2
    while i >= 0:
        bit = bitmask[i:i+2]
        i -= 2
        
        str_ = ''
        # used as collateral 
        if bit[0] == '1':
            str_ += ' C '
            c_list.append(reserve_list[count])
        # borrowed
        if bit[1] == '1':
            str_ += ' B '
            b_list.append(reserve_list[count])
        
        print(f'        {count}: {reserve_list[count]} = {bit}  {str_}')
        count += 1
        
    # catch last bit when length of bitmask is odd
    if  len(bitmask) % 2 == 1:
        bit = '0'+bitmask[0]
        
        str_ = ''
        # used as collateral 
        if bit[0] == '1':
            str_ += ' C '
            c_list.append(reserve_list[count])
        # borrowed
        if bit[1] == '1':
            str_ += ' B '
            b_list.append(reserve_list[count])
        
        print(f'        {count}: {reserve_list[count]} = {bit}  {str_}')
    
    return c_list, b_list

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


