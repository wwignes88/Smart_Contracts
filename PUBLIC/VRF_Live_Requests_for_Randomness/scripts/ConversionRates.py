
from scripts.helpful_scripts import *
from brownie import interface, config, network
from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://polygon-mumbai.g.alchemy.com/v2/8SR4c1UGYLHeFmTL3K2Gnr5jIKZk9aBc"))
NETWORK = network.show_active()
account = get_account()

#---------------------------------- MISC. CONTRACTS/ ADDRESSES


# Currency conversion rates [using V3 Aggregator]
matic_to_usd   =   getConversionRate("matic_to_usd")
eth_to_usd     =   getConversionRate("eth_to_usd")
matic_to_eth   =   matic_to_usd/eth_to_usd
link_to_matic  =   getConversionRate("link_to_matic")
link_to_usd    =   getConversionRate("link_to_usd")

def printConversionRates():
    print('\nConversion rates:')
    print(f'    matic_to_eth  : {matic_to_eth}') 
    print(f'    matic_to_usd  : {matic_to_usd}')  
    print(f'    eth_to_usd    : {eth_to_usd}')  
    print(f'    link_to_matic : {link_to_matic}')  
    print(f'    link_to_usd   : {link_to_usd}')  

