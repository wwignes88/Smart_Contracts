
from scripts.helpful_scripts import *
from brownie import (interface, config, network, Wei, convert, 
                     Enumerate, Lendable)
from scripts.CCIP_dicts import *
import sys
from brownie.network import priority_fee, max_fee

NETWORK = network.show_active()

_gwei = 1e-9
_wei  = 1e-18
_ETH  = 1e18

def deploy():
    print('\n=============== deploy  =====================\n')

    account     = get_account() ; GasBal = account.balance()
    LINK        = TokenContract('link')
    router_addr = config["networks"][network.show_active()]['router']
    chain_selector = chain_selectors[network.show_active()]

    print('\ndeploying lendable...')
    lendable = Lendable.deploy(router_addr,
                                LINK.address,
                                chain_selector,
                                {"from": account})    
    UpdateConfigAdresses(lendable, 'lendable')

def main():
    deploy()

