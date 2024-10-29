from scripts.helpful_scripts import * 
from brownie.network.event import EventWatcher
import binascii
import time
import sys
watcher = EventWatcher()  

COORDINATOR  = get_contract("mock2_") # get VRFCoordinator mock contract.
WRAPPER      = get_contract("wrapper_")
ORACLE       = get_contract("oracle_")
LINK         = get_contract("link_")
account      = get_account() 
    
def listenForRequest():
    
    #watcher._start_watch()
    watcher.add_event_callback(event=COORDINATOR.events["request_I"],
                             callback=callbackFunc, 
                             delay=0.5, 
                             repeat=True)
    #print(f'      ...added event "RandomWordsRequestedI" to watch list.')
    watcher.add_event_callback(event=COORDINATOR.events["request_II"],
                             callback=callbackFunc, 
                             delay=0.5, 
                             repeat=True)
    #print(f'      ...added event "RandomWordsRequestedII" to watch list.')

variables = {}
def callbackFunc(event):
    event_name = event.event
    print(f"""
        **************************************
        {event.event} detected by VRF Machinery!
        ************************************** 
        """)

    # Retrieve event logs
    if event_name == "request_I":
        event_logs = COORDINATOR.events.request_I.getLogs()
    if event_name == "request_II":
        event_logs = COORDINATOR.events.request_II.getLogs()
        
    # Process the event logs
    for event_log in event_logs:
        # Access event data
        event_data = event_log.args
        # update variabvles dictionary
        variables.update(event_data)

    if len(variables) == 8:
        time.sleep(2)
        blockHash = event.blockHash.hex()
        blockNum  = event.blockNumber
        
        print('\nupdating BLOCK_HASH_STORE ...')
        mapBlock = ORACLE.mapBlockHash
        mapBlock( blockNum, blockHash, {"from": account})
        print('BLOCK_HASH_STORE updated!\n')
        time.sleep(1)
        
        # initiate response.
        responseFunc = response 
        responseFunc(blockNum,blockHash)
        

#----------------------------------------------------
def response(_blockNum,_blockHash):

    # update blockHashStore (map block number to blockHash)
    # *presumes ORACLE is set to blockHash [default in deployment]



    
    # load variables....
    keyHash   = variables['keyHash'] 
    keyHash_ = f'0x{keyHash.hex()}'
    requestId = variables['requestId']   
    preSeed   = variables['preSeed']   
    subId     = variables['subId']    
    minimumRequestConfirmations = variables['minimumRequestConfirmations'] 
    callbackGasLimit  = variables["callbackGasLimit"]
    numWords          = variables['numWords']  
    sender            = variables['sender']      
     
    # Mocking some mathematical calculation (**HERE IS WHERE THE MATH WOULD COME INTO PLAY!)
    print('\n===============================================')
    print('     VRF MachinerY is providing randomness\n\
            ... not really [mocking]')
    print('===============================================\n')
    time.sleep(2)
    
    gamma    = [1,2]  ; pk = [2,5] 
    proof    = [keyHash, pk, gamma, preSeed]
    rc       = [_blockNum, subId, callbackGasLimit, numWords, WRAPPER.address]
    
    # check proving key is registered/ register if not
    _oracle = str(COORDINATOR.checkProvingKeyRegistration(proof))
    if _oracle != ORACLE.address:
        print('\nregistering proving key...')
        registTX = COORDINATOR.registerProvingKey
        registTX(ORACLE.address, keyHash, {"from":account})
        time.sleep(1)
        print(f'registered proving key!')
    if _oracle == ORACLE.address:
        print(f'proving key already registerd.') 
    time.sleep(2)
    

    
    # fulfill request
    print('\nfulfilling request...') 
    WithdrawableOracle_0 = COORDINATOR.withdrawBal(ORACLE.address)         
    FULLFILL = COORDINATOR.fulfillRandomWords
    FULLFILL(proof, rc, {"from": account})
    time.sleep(5)
    WithdrawableOracle_1 = COORDINATOR.withdrawBal(ORACLE.address)   
    payment = (WithdrawableOracle_1 - WithdrawableOracle_0)*1e-18
    print(f'fulfilled! ')
    print(f'---payment  : {payment}') 
    time.sleep(1)
    
    
    # transfer payment from COORDINATOR to ORACLE contract.
    print('\ndepositing fulfillment payment to Oracle...')
    deposit_to_oracle = COORDINATOR.oracleWithdraw
    #deposit_to_oracle = ORACLE.OracleCashesIn
    deposit_to_oracle(ORACLE.address, ORACLE.address, payment, {"from":account})
    print('deposited payment to Oracle.')
    time.sleep(1)
 
    
 
    # unregister proving key:
    print(f'\nderegistering proving key...')
    deregistTX = COORDINATOR.deregisterProvingKey
    deregistTX(keyHash, {"from":account})
    print(f'De-registered proving key.')
    
    RConfig = COORDINATOR.getRequestConfig
    print(f'\npending requestIds: \n{RConfig({"from":account})[2]}\n\n')



    




