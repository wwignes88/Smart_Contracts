from scripts.helpful_scripts import *
from brownie import Request, network, config


def deploy_and_create():

    
    
    account = get_account()
    # We want to be able to use the deployed contracts if we are on a testnet
    # Otherwise, we want to deploy some mocks and use those
    # Sepoli
    link_ = config["networks"][network.show_active()]["link_token"]
    vrf_coordinator = config["networks"][network.show_active()]["vrf_coordinator"]
    request_ = Request.deploy(
        vrf_coordinator,
        link_,
        config["networks"][network.show_active()]["keyhash"],
        config["networks"][network.show_active()]["fee"],
        {"from": account},
    )  
    UpdateConfigAdresses(request_, 'request_')
    
    
    print('\ncreating subscription....')
    tx = request_.createSub({"from": account})
    tx.wait(1)
    subID = request_.getSubId()
    print(f'subID: {subID}')
    
    
    # ADD consumers
    print('adding consumers....')
    # add Request contract as consumer
    tx = request_.addConsumer_(subID, request_.address,  {"from": account})
    tx.wait(1)
    # add metamask account as consumer (optional)
    #tx = advanced_collectible.addConsumer_(subID, account.address,  {"from": account})
    #tx.wait(1)
 
    
    
    print(f'sub info: \n{request_.getSub(subID)}')
    print(f'config: {request_.getConfig_()}')
    
    # update my subId in collectible.sol so that it can be retrieved in other scripts
    print('\nsetting my subId...')
    tx = request_.setMySubId(subID,{"from": account})
    tx.wait(1)




def main():
    deploy_and_create()
