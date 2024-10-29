import subprocess
from brownie import NFT, network, config, interface
from scripts.upload_to_pinata import uploadToPinata
from scripts.helpful_scripts import (get_account,
                                     get_contract,
                                     fund_with_link,
                                     OPENSEA_URL)
import sys
from scripts.ConversionRates import link_to_usd, matic_to_usd

link_to_usd  = link_to_usd*1e10
matic_to_usd = matic_to_usd*1e10
matic_link   = matic_to_usd/link_to_usd

from web3 import Web3
w3 = Web3(Web3.HTTPProvider("https://polygon-mumbai.g.alchemy.com/v2/[enter your alchemy key]"))
account      = get_account()
NFT          = get_contract("nft_")
    

    
def CreateNFT():

    gasBalA, NFT_LinkBal_A = getBals(True)
    print(f'link_to_usd : {link_to_usd}')
    print(f'matic_to_usd: {matic_to_usd}')
    print(f'matic_link  : {matic_link}')
    
    
    # Fund W/ LINK
 
    if NFT_LinkBal_A < 0.3:
        print('\n-------fund advanced:')
        fund_with_link(NFT.address, 1.3*1e18, "advanced")
    

    # Create NFT
    print(f"\n-------- Creating NFT...")
    tokenId    = NFT.tokenCounter()      ;  print(f'\ntokenId  : {tokenId}')
    
    # Check tokenId is available
    tokenOwner = NFT.getTokenOwner( tokenId, {"from": account})  ; 
    print(f'token owner; {tokenOwner}')
    
    # Check ipfs DAEMON is running
    DAEMON = is_ipfs_daemon_running()
    print(f'\nDAEMON: \n{DAEMON}')
    
    # create metadata/ upload to pinata
    breedType  = 'Turtle'
    luvability = 3
    ipfsHash, imgURL, metadata_url  = uploadToPinata(breedType, luvability) 

    #---------- create NFT
    owner = account.address # set owner of NFT
    tx    = NFT.createCollectible(owner, metadata_url, {"from": account} )  ; tx.wait(1)
    item  = NFT.tokenURI(tokenId)
    print(f'    current token URI: {item}')
    print(f"\n    view your NFT at {OPENSEA_URL.format(NFT.address, tokenId)}")
    

    #------------ Calculate Transaction Cost 
    # calculate cost of the above transaction
    # * Once you create an NFT it does not need to be recreated, so this part is
    # someone unneccessary, but it is just a good habit to get into to get a 
    # feel for the cost of whatever transactions you perform.
    gasBalB, NFT_LinkBal_B = getBals(False)
    print('\nPayments:')
    LINKdiff = (NFT_LinkBal_A - NFT_LinkBal_B)*link_to_usd
    gasDIFF  = (gasBalA-gasBalB)*matic_to_usd
    print(f'    gas   : {gasDIFF} [{gasDIFF} USD]')
    print(f'    LIINK : {LINKdiff} [{LINKdiff} USD]')
    print(f'    total : {gasDIFF + LINKdiff}')
    


    
#==============================================================================================
#=======================================  FUNCTION   ==========================================
#==============================================================================================


def createNFT(_tokenURI):
    print(f"\n-------- Creating NFT...")
    owner      = account.address
    tokenId    = NFT.getTokenCounter()      ;  print(f'\ntokenId  : {tokenId}')
    tx = NFT.createCollectible(owner, _tokenURI, {"from": account} )  ; tx.wait(1)
    return tokenId

#------------------ GET BALS
def getBals(PRINT):
    gasBal  = w3.eth.get_balance(account.address)*1e-18
    NFT_LinkBal = NFT.LINKBalance(NFT.address)*1e-18
    if PRINT:
        print('\nBalances:')
        print(f'    my gas balance   : {gasBal}')
        print(f'    NFT LINK Bal     : {NFT_LinkBal}')
        
    return gasBal, NFT_LinkBal


def is_ipfs_daemon_running():
    try:
        subprocess.run(["ipfs", "swarm", "peers"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
        return True
    except subprocess.CalledProcessError:
        print('ipfs DAEMON is not running!')
        return False



def main():
    CreateNFT()
