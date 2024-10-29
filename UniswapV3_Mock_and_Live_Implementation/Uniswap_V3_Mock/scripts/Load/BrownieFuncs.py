

from brownie import (accounts, interface, network, config, Contract)
import shutil, os, sys, binascii
from brownie.network.event import EventWatcher
from scripts.Load.helpful_scripts import getERC20
from scripts.Load.DICTS import contractList, contractToSym

#---------------------  DEPLOYMENT; UPDATE CONFIG  ADDRESSES

def UpdateConfigAdresses(Contract, str_):

    NETWORK = network.show_active()
    _dir = os.getcwd() ; #(f'current dir: {_dir}')
    _config = _dir + '\\brownie-config.yaml' ; 
    print(f'\nre-writing {_config}\n')
    dummy_file    = _config + '.bak'
    
    with open(_config, 'r') as read_obj, open(dummy_file, 'w') as write_obj:
        
        READ_LINES = read_obj.readlines() # file to be read
        data = []
        i = 0
        while i < len(READ_LINES):
            line = READ_LINES[i]
            data.append(line)
            if NETWORK in line:
                j = i+1; kill = False
                while kill == False:
                    line = READ_LINES[j]
                    if str_ in line:
                        line = F'    {str_} : "{Contract.address}"\n'
                        kill = True
                    data.append(line)
                
                    j += 1
                i=j-1
            i += 1
            

        #write new file:
        i = 0
        while i < len(data):
            write_obj.write(data[i]) # this is 'a' object
            i += 1

    # replace current file with new debugging file
    try:
        os.remove(_config)
        os.rename(dummy_file, _config)
        # shutil.move(dummy_file, _config)
        print('config file updated w/ deployment addresses\n\n')
    except:
        print('\n !! could not delete config file. delete brownie-config.yaml and \
            rename the .bak file.')

#--------------------- EVENT LISTENING

# get the events from a brownie transaction
def getEvents(tx):
    print(f"\nEVENTS")
    tx_events  = tx.events

    for i, (event, eventDict) in enumerate(tx_events.items()):
        print(f"\n-----[{i}] {event}:") #.upper()
        if event ==  '(unknown)':
            pass
        else:
            EventDict = dict(eventDict)
            for j, (param, value) in enumerate(EventDict.items()):
                print(f"      {param} : {value}")


# EVENT WATCHER
def resetEventWatcher():
     EventWatcher.reset()
def stopEventWatcher(Wait):
     EventWatcher.stop(Wait)
     
def listenForEvent(eventList):
    watcher = EventWatcher() 
    watcher.reset()
    #watcher._start_watch()
    
    for contract_event_pair in eventList:
        CONTRACT  = contract_event_pair[0]
        event_str = contract_event_pair[1]
        watcher.add_event_callback(event  = CONTRACT.events[event_str],
                                callback = callbackFunc, 
                                delay    = 0.1, 
                                repeat   = True)
        print(f'     added {event_str} event to watch list.')

def callbackFunc(event):

    event_name = event.event
    args_dict = event.args  # Accessing the 'args' AttributeDict
    print(f'\n[emitted] {event.event} :')
    for key, value in args_dict.items():
        nonToken = True
        if value in contractList:
            print(f"   {key}: {contractToSym[value]}")
            nonToken = False
        if nonToken:
            print(f"   {key}: {value}")


                
        


def CallbackResponse():

    print('\nresponding....')