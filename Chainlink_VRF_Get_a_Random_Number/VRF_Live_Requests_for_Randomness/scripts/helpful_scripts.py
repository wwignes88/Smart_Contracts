from brownie import (accounts, network, config, Contract, interface, Request)
from web3 import Web3
import os
import sys

def get_breed(breed_number):
    return BREED_MAPPING[breed_number]


def get_account():
    return accounts.add(config["wallets"]["from_key"])

contract_to_mock = {"request_": Request}

def get_contract(contract_name):
    contract_type = contract_to_mock[contract_name]
    contract_address = config["networks"][network.show_active()][contract_name]
    contract = Contract.from_abi(
        contract_type._name, contract_address, contract_type.abi
    )
    return contract


def fund_with_link( contract_address, amount, name):
    print(f'\nfunding {name} w/ LINK...')
    account = get_account()
    link_token = interface.Ilink(config["networks"][network.show_active()]["link_token"])
    tx = link_token.transfer(contract_address, amount, {"from": account})
    tx.wait(1)
    
    print(f'funded {name} w/ LINK.')
    return tx

#---------------------  DEPLOYMENT; UPDATE CONFIG  ADDRESSES
def UpdateConfigAdresses(Contract, str_):

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
    os.remove(_config)
    os.rename(dummy_file, _config)
    print('config file updated w/ deployment addresses\n\n')

    #----------------------------


def getConversionRate(_str): #https://docs.chain.link/data-feeds/historical-data/
    price_feed_address = config["networks"][network.show_active()][_str]
    price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = price_feed.latestRoundData()[1]
    converted_latest_price = latest_price*1e-18
    return float(converted_latest_price)


    