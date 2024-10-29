from brownie import (accounts, network, config, Contract, testings)
from scripts.helpful_scripts import *



def deploy_test(): 
    account = get_account() 
    test    = testings.deploy({"from": account}) 
    print(f'testings @ : {test.address}')
    
def main():
    deploy_test()
        