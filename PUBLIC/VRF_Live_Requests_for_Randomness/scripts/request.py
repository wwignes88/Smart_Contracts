import brownie
from brownie import network, config, interface
from scripts.listening import listenForRequest, wait_for_fulfillment
from scripts.helpful_scripts import (get_account,
                                     get_contract,
                                     fund_with_link)
from web3 import Web3
import time 
import sys
import json
from scripts.ConversionRates import*

link_to_usd  = link_to_usd*1e10
matic_to_usd = matic_to_usd*1e10
matic_link   = matic_to_usd/link_to_usd
#printConversionRates()

w3 = Web3(Web3.HTTPProvider("https://polygon-mumbai.g.alchemy.com/v2/8SR4c1UGYLHeFmTL3K2Gnr5jIKZk9aBc"))
account      = get_account()
COORDINATOR  = interface.ICoordinator(config["networks"][network.show_active()]["vrf_coordinator"])
REQUEST      = get_contract("request_")
    

    
def request_():

    print("""-------------------------------------------------------------""")
    # *Note: make sure subId matches deployment subId (it should, but double check)
    subID   = REQUEST.getMySubId()  ; print(f'subId: {subID}')  
    nonce_  = REQUEST.getConsumerNonce(REQUEST.address, subID )
    print(f'nonce: {nonce_}')
    if nonce_ == 0:
        print(f'no consumer allocated to subscription. Add NFT.sol address as consumer to subscription \
            using  "addConsumer" function below.')
        sys.exit(0)

    pending = COORDINATOR.pendingRequestExists(subID)
    if pending:
        input('pending request exists')
        #sys.exit(0)

    subBalA, gasBalA, REQUEST_LinkBal_A = getBals(subID, True)
    
    #================================================================= FUND W/ LINK
    fundSub       = False
    fundContract  = False
    request_      = True
 
    if fundContract  or REQUEST_LinkBal_A < 0.3:
        print('\n-------fund Request Contract:')
        fund_with_link(REQUEST.address, 1.3*1e18, "Reqeust")
    
    if fundSub or subBalA < 0.3:
        print('\n-------funding subscription:')
        tx = REQUEST.fundSubscription(subID, 0.4*1e18, {"from": account}) 
        tx.wait(1)
        subBalA, gasBalA, REQUEST_LinkBal = getBals(subID, True)
    
    # Make request:
    requestId, randomness = request(subID, nonce_)
    
    # simplify/ reduce the random number using the modulus function
    moddled = 27 
    reducedRandomNumber = randomness % moddled
    print(f'\nmy random number (modulo {moddled}): {reducedRandomNumber}')
        
    
    # calculate cost of request (gas included)
    subBalB, gasBalB, REQUEST_LinkBal_B = getBals(subID, True)
    subDIFF  = (subBalA-subBalB)*matic_to_usd
    gasDIFF  = (gasBalA - gasBalB)*matic_to_usd
    LINKdiff = (REQUEST_LinkBal_A - REQUEST_LinkBal_B)*link_to_usd
    print('\nPayments:')
    print(f'    sub  : {subDIFF}  USD')
    print(f'    gas  : {gasDIFF} USD')
    print(f'    total: {subDIFF + gasDIFF}')
    
    print(f'\n    LINK (contract)  : {gasDIFF} USD')
    

#==============================================================================================
#=======================================  FUNCTION   ==========================================
#==============================================================================================

        
#------------------ REQUEST RANDOMNESS
# request random words.
def request(subID, nonce):
    _keyHash = "0x4b09e658ed251bcafeebbc69400383d49f344ace09b9576fe248bb02c003fe9f"
    _subId   = subID
    _requestConfirmations = 3
    _callbackGasLimit     = 300000
    _numWords             = 1
    requestId, preSeed = REQUEST.computeReqId(_keyHash, REQUEST.address, _subId, nonce+1) ; print(f'reqID (nonce+1) : {requestId}')
    listenForRequest() # listen for emitted event from requestRandomWords function.
    
    print(f'\nrequesting a random word ...')
    tx = REQUEST.CoordinatedRequest(_keyHash,
                            _subId,
                            _requestConfirmations,
                            _callbackGasLimit,
                            _numWords,
                            REQUEST.address,
                            {"from": account})

    # listen for emitted event from fulfillRandomWords function.
    # will error if requestId fulfillment tx not deteced in time_seconds.
    timeout_seconds=30
    randomness = wait_for_fulfillment(requestId, timeout_seconds, _subId)
    
    return requestId, randomness
    


#------------------ GET BALS
def getBals(subID, PRINT):
    gasBal  = w3.eth.get_balance(account.address)*1e-18
    subInfo = REQUEST.getSub(subID) 
    subBal  = subInfo[0]*1e-18  ; 
    REQUEST_LinkBal = REQUEST.LINKBalance(REQUEST.address)*1e-18
    if PRINT:
        print('\nBalances:')
        print(f'    my gas balance   : {gasBal}')
        print(f'    subscription Bal : {subBal}, requ cnt.: {subInfo[1]}')
        print(f'    REQUEST LINK Bal : {REQUEST_LinkBal}')
        
    return subBal, gasBal, REQUEST_LinkBal


    def configs():
        
        config = COORDINATOR.getConfig() ; print(f'\nconfig: \n{config}')
        """
        (3, 2500000, 86400, 33285)
        returns (
        uint16 minimumRequestConfirmations,
        uint32 maxGasLimit,
        uint32 stalenessSeconds,
        uint32 gasAfterPaymentCalculation
        )"""
        
        FeeConfig = COORDINATOR.getFeeConfig() ; print(f'\nFeeConfig: \n{FeeConfig}')
        """    returns (
        uint32 fulfillmentFlatFeeLinkPPMTier1,
        uint32 fulfillmentFlatFeeLinkPPMTier2,
        uint32 fulfillmentFlatFeeLinkPPMTier3,
        uint32 fulfillmentFlatFeeLinkPPMTier4,
        uint32 fulfillmentFlatFeeLinkPPMTier5,
        uint24 reqsForTier2,
        uint24 reqsForTier3,
        uint24 reqsForTier4,
        uint24 reqsForTier5
        )
        """
    

#------------------ COORDINATOR CONFIGURATION
# get coordinator configuration info.
def addConsumer(subID, consumer):
    tx = REQUEST.addConsumer_( subID, consumer, {"from": account})
    tx.wait(0)





def main():
    request_()