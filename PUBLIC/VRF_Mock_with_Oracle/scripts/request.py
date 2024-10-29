from scripts.helpful_scripts import * 
from scripts.VRFMachineryTest import *
import sys
import time


def runVRF():   
    
    # get account/ contracts
    COORDINATOR  = get_contract("mock2_") # get VRFCoordinator mock contract.
    WRAPPER      = get_contract("wrapper_")
    LINKCoordinator = get_contract("link_coordinator")
    account      = get_account() ; my_address  = str(account)

    #================================================================
    #===============================================================
    #getLINKBalances()


    #----------------- REQUEST RANDOM WORD
    requestWord = True
    if requestWord:
        # initialize VRF machinery to start listening for requests.
        listenForRequest()  
        if watcher._has_started:
            print('\nVRF machinery is watching for requests.')
            #print(f'\ntargets:  {watch.target_events_watch_data}')

            
            
        #define input parameters
        _keyHash = "0xd89b2bf150e3b9e13446986e571fb9cab24b13cea0a43ea20a6049a85cc807cc"
        _subId   = COORDINATOR.getCurrentSubId({"from": account}) 
        Sub      = getSubInfo(_subId, COORDINATOR, False)
        if Sub[0] == 0:
            print('subscription underfunded. please add funds to subscription to choose a different subId.')
            sys.exit(0)
            #!!! check consumers
        _requestConfirmations = 1
        _callbackGasLimit     = 300000
        _numWords             = 3

        print(f'\nrequesting a random word...')
        tx = WRAPPER.requestWords(_keyHash,
                                _subId,
                                _requestConfirmations,
                                _callbackGasLimit,
                                _numWords,
                                {"from": account})
        
        time.sleep(25) 

    #getLINKBalances()





    #---------------------- RECONFIGURE COORDINATOR (optional)
    # set configuration:
    configure = False
    if configure:
        minimumRequestConfirmations  = 1
        maxGasLimit                  = 2500000   # (gwei) ~ 0.77 LINK
        # default stalenessSeconds val is 2,700;
        # a high value will cause us to rely on V3Aggregator for 
        # 'fallbackWeiPerUnitLink' value. seegetFeedData() 
        stalenessSeconds             = 100000 
        gasAfterPaymentCalculation   = 33285     # (gwei) ~ 0.01 LINK
        fallbackWeiPerUnitLink       = 3.25*1e15 # 3.25*1E15 Wei = 0.00325 ETH = 1 LINK
        feeConfig                    = (100000, 100000, 100000, 100000, 100000, 0, 0, 0, 0) # 0.1 LINK = 400,0000 gwei
        setConfig(COORDINATOR,
                minimumRequestConfirmations, 
                maxGasLimit,
                stalenessSeconds,
                gasAfterPaymentCalculation,
                fallbackWeiPerUnitLink,
                feeConfig)
   
       
    
    



def main():
    runVRF() 