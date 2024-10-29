from scripts.helpful_scripts import get_account 
from brownie import interface, config, network
from brownie.network.event import EventWatcher
import binascii
import time 
import sys
COORDINATOR  = interface.ICoordinator(config["networks"][network.show_active()]["vrf_coordinator"])
account = get_account()
watcher = EventWatcher()  
def listenForRequest():
    
    watcher.add_event_callback(event=COORDINATOR.events["RandomWordsRequested"],
                             callback=callbackFunc, 
                             delay=0.5, 
                             repeat=True)
    
    
def callbackFunc(event):
    event_name = event.event
    
    if event_name == "SubscriptionFunded":
        print('\nsub funded!')
        event_logs = COORDINATOR.events.SubscriptionFunded.getLogs()
        for event_log in event_logs:
            oldBalance = event_log.args["oldBalance"] ;  print(f'*OldBal    : {newBoldBalancealance*1e-18}')
            newBalance = event_log.args["newBalance"] ;  print(f'*NewBal    : {newBalance*1e-18}')

    if event_name == "RandomWordsRequested":
        event_logs = COORDINATOR.events.RandomWordsRequested.getLogs()
        for event_log in event_logs:
            #print(f'\nargs      : {event_log.args}')
            preSeed      = event_log.args["preSeed"]
            requestId    = event_log.args["requestId"]
            subId        = event_log.args["subId"]
            keyHash      = event_log.args["keyHash"]
            
            if subId == 5701:
                print(f'\nREQUEST DETECTED')
                #print(f'----preSeed    : {preSeed}')
                print(f'----requestId  : {requestId}')
                print(f'----subId      : {subId}')
                #print(f'----keyHash    : {keyHash}')
                


def wait_for_fulfillment(reqId, timeout_seconds, subID):

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        request_logs = COORDINATOR.events.RandomWordsRequested.getLogs()
        for event in request_logs:
            #print(f'\nargs      : {event_log.args}')
            preSeed      = event.args["preSeed"]
            requestId    = event.args["requestId"]
            subId        = event.args["subId"]
            keyHash      = event.args["keyHash"]
            
            if subId == subID:
                print(f'\nUSER REQUEST DETECTED')
                #print(f'----preSeed    : {preSeed}')
                print(f'----requestId  : {requestId}')
                print(f'----subId      : {subId}')
                #print(f'----keyHash    : {keyHash}')
                
        
        
        fulfill_logs = COORDINATOR.events.RandomWordsFulfilled.getLogs()
        for event in fulfill_logs:
            randomNumber = event.args["outputSeed"]
            requestId    = event.args["requestId"]
            payment      = event.args["payment"]
            success      = event.args["success"]
            print(f'\nrequest {str(requestId)[:6]}... fulfilled')
            pending = COORDINATOR.pendingRequestExists(subID)
            if pending:
                print(f'request {str(reqId)[:6]}... still pending\n')

            if requestId == reqId:
                print(f'\nUSER REQUEST FULFILLED! ')
                print(f'----requestId_  : {requestId}')
                print(f'----outputSeed  : {randomNumber}')
                return randomNumber
            if pending == False and requestId != reqId:
                msg = """
                OOPS! fulfillment event was missed by listener.
                Try adjusting the 'time.sleep(...) parameter in the 
                'wait_for_fulfillment' [callback] function in listening.py file.
                Reducing this parameter will increase the frequency of checks.
                """
                print(f'{msg}')
        time.sleep(0.5)  # Wait for a few seconds before polling again
        
    print('\nfullfimment not detected!!')
    sys.exit(0)
