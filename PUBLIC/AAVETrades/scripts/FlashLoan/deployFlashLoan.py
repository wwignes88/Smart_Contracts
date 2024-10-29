from brownie import (accounts, network, config, Contract, MyV2FlashLoan)
from scripts.helpful_scripts import *
from web3 import Web3


def deploy_FLASH(): 
    account  = get_account() 
    Provider = config["networks"][network.show_active()]['lending_pool_addresses_provider']
    FlashLoanContract  = MyV2FlashLoan.deploy(
        Provider,
        {"from": account}) 
    
    print(f'deployed FlashLoan @ : {FlashLoanContract.address}')
    UpdateConfigAdresses(FlashLoanContract)
    
def main():
    deploy_FLASH()
        
