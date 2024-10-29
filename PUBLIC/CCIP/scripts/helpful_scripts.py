from brownie import (accounts, interface, network, config, Contract,
                     Enumerate, Lendable)
from web3 import Web3
from brownie.network import priority_fee, max_fee
import shutil, os, sys

# global variables:
w3 = Web3(Web3.HTTPProvider("https://eth-sepolia.g.alchemy.com/v2/QUhbF0JeaaHCTWmZdPWDQ8TTjX2mv4zE"))

#------------------------------------------ MISC GENERAL ACCOUNT/ CONTRACT FUNCTIONS
def get_ALT_account():
    EXPLORaccount = accounts.add(config["wallets"]["EXPLOR_key"])
    return  EXPLORaccount

def get_account():
    GOOGaccount   = accounts.add(config["wallets"]["GOOG_key"])
    return GOOGaccount

#---------------------------------------------------- TOKENS
def get_Token_bal(Token, address_, str_, PRINT):
    Token_balance = Token.balanceOf(address_)
    if PRINT:
        print(f'    {str_} {Token.symbol()} bal: {Token_balance*1e-18}')
    return Token_balance

def update_CCIP_Bals(account, BnM, LnM, LINK, contract, PRINT ):
    GasBal = account.balance()
    contract_native = contract.balance()
    if PRINT:
        print('\n----Native Bals:')
        print(f'    GasBal     : {GasBal*1e-18}')
        print(f'    contract   : {contract_native*1e-18}')
        print('----Token Bals:')
    my_BnM   =  get_Token_bal(BnM,account.address, "my", PRINT)
    my_LINK  =  get_Token_bal(LINK,account.address, "my", PRINT)
    contract_LINK = get_Token_bal(LINK,contract.address, "contract", PRINT)
    contract_BnM  = get_Token_bal(BnM,contract.address, "contract", PRINT) ; 

    return GasBal, my_BnM, my_LINK, contract_BnM, contract_LINK, contract_native
    
def get_BnM_contract(_token_):
    # get token contract
    return interface.CCIPBnM_Interface(config["networks"][network.show_active()][_token_])

def TokenContract(_token_):
    # get token contract
    return interface.IERC20(config["networks"][network.show_active()][_token_])

contract_to_mock = {"enumerate"  : Enumerate,
                    "lendable"   : Lendable}

def get_contract(contract_name):
    # get contract on active network
    contract_type = contract_to_mock[contract_name]
    contract_address = config["networks"][network.show_active()][contract_name]
    contract = Contract.from_abi(
        contract_type._name, contract_address, contract_type.abi)
    return contract

def approve_erc20(account, amount, spender, erc20):
    print("---\nApproving ERC20 token...")
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    spender_allowance = erc20.allowance(account.address, spender) 
    print(f"Spender approved for {spender_allowance*1e-18} {erc20.symbol()}")
    return tx

def fundERC20(erc20 , recipient, dep_val, account):
    print(f'\nfunding {erc20.symbol()} contract...')
    tx = erc20.transfer(recipient , dep_val, {"from": account})
    tx.wait(1) 

#------------------ CCIP

def get_router_addr():
    return config["networks"][network.show_active()]['router']

#---------------------  DEPLOYMENT; UPDATE CONFIG  ADDRESSES
def UpdateConfigAdresses(Contract, str_):

    NETWORK = network.show_active()
    _dir = os.getcwd() ; #(f'current dir: {_dir}')
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
                    if str_ in line:
                        line = F'    {str_} : "{Contract.address}"\n'
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
    try:
        os.remove(_config)
        os.rename(dummy_file, _config)
        # shutil.move(dummy_file, _config)
        print('config file updated w/ deployment addresses\n\n')
    except:
        print('\n !! could not delete config file. delete brownie-config.yaml and \
            rename the .bak file.')


    #----------------------------
