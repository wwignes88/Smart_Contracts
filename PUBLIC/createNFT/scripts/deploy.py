from scripts.helpful_scripts import *
from brownie import NFT, network, config


def deploy_and_create():
    name   = "Str8_Jacket"
    symbol = 'ST8'
    
    account = get_account()
    # We want to be able to use the deployed contracts if we are on a testnet
    # Otherwise, we want to deploy some mocks and use those
    # Sepoli
    link_ = config["networks"][network.show_active()]["link_token"]
    nft_ = NFT.deploy(
        link_,
        {"from": account},
    )  
    UpdateConfigAdresses(nft_, 'nft_')
    

    return nft_


def main():
    deploy_and_create()
