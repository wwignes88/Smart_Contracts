from scripts.helpful_scripts import * 
from brownie.network.event import EventWatcher
import binascii
import time
import sys
watcher = EventWatcher()  


    """
    see comments in 'LISTEN FOR REQUESTS' section of 'scripts/FlashLoan/flashloan.py'
    """
FlashLoan   = get_contract("testing_") 
account = get_account()

def listenForRequest():
    #watcher._start_watch()
    watcher.add_event_callback(event    = FlashLoan.events["FlashEvent"],
                               callback = callbackFunc, 
                               delay    = 0.5, 
                               repeat   = True)
    print(f'      ...added event "FlashEvent" to watch list.')

variables = {}
def callbackFunc(event):
    event_name = event.event
    print(f"""
        **************************************
        {event.event} detected by VRF Machinery!
        ************************************** 
        """)

    # Retrieve event logs
    event_logs = FlashLoan.events.FlashEvent.getLogs()

        
    # Process the event logs
    for event_log in event_logs:
        print(f'event: {event_log}')
        # Access event data
        event_data = event_log.args
        # update variabvles dictionary
        variables.update(event_data)

    time.sleep(2)
    responseFunc = response 
    responseFunc()
        

#----------------------------------------------------
def response():
    #keyHash   = variables['keyHash'] 
    print('\nresponding....')
def main():
    listenForRequest()
    FlashLoan.emittt({"from":account})
