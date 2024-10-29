
from scripts.Load.helpful_scripts import *
from brownie import network
from web3 import Web3
import sys
import pandas as pd
import numpy as np
import time
import pytz
from scripts.Load.DICTS import *
from scripts.plotRates import plotRates

NETWORK = network.show_active()
if NETWORK not in LIVE_ENVS:
    print('must run on live environment (or configure live-env).')
    sys.exit(0)

network_name = NETWORK_NAMES[NETWORK]

#====================== UPDATE/ RETRIEVE MULTI LEVEL CONVERSION RATE DATA FRAME

def createDataTable(address, convertSym, period, H):
    
    h, start_dateTime = START_TIMES(period)
    print(f'\ngoing back to t = {start_dateTime}')

    # override pre-set roundID step value h if desired.
    if H :
        h = H
    print(f'\nh = {h}')
    
    # start date/time in seconds
    start_seconds = date_to_seconds(start_dateTime) 
    
    # file path to store table at
    dir_path = f'DataTables//Tables//{network_name}//{period}'
    check_dir(dir_path) # check directory/ create if needed.

    data_file_path = dir_path + f'//{convertSym}.csv'
    columns_ = ['time', convertSym]

    # initialize data arrays
    # Δd,Δh,Δm are the days, hours, minutes since last update
    # rndID will be latest round bID when roundID=None
    rndID,t,Δd,Δh,Δm,rate = getRoundData(address, None)
    T = seconds_t0_date(t)
    print(f'     t0: {T}   current rate: {rate}')  # 47298226.41695077
    rndID -= h

    # initialize data
    # *must convert time value from seconds to time-date format
    RND_data = np.array([seconds_t0_date(t),rate])

    while t > start_seconds:

        rndID_,t,Δd,Δh,Δm,rate = getRoundData(address, rndID)
        T = seconds_t0_date(t)
        print(f'     t: {T}   rate: {rate}')
        time.sleep(0.1)
        rnd_data = np.array([T,rate])
        RND_data = np.vstack([RND_data,rnd_data])
        rndID -= h
        
    print(f'\nNo. data pts.: {len(rnd_data)}')
    
    df = pd.DataFrame(RND_data , columns=columns_) 
    
    # save df to .csv
    df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
    
    return df

#============================================================

def main():
    print('\n=============== updateData.py ================')
    dictionary = POLYGON
    if dictionary['network'] != network_name:
        print(f'please run on {network_name} or update dict val.')

    H      = 10
    OPTION = 3 
                # OPTION = 0: update just one time period/ folder in selected network/ dictionary
                # OPTION = 1: update SELECTED RATES for a single time period
                # OPTION = 2: update ALL time period folders in selected network/ dictionary
                # OPTION = 4: updated latest_rates file.
    PLOT   = True

    if OPTION == 0:
        # update just one time period/ folder in selected network/ dictionary
        convertSym = 'eth_usd'
        period     = '3_day'
        addr       = dictionary[convertSym]
        createDataTable(addr, convertSym, period, H) 

        #-------- plotting
        if PLOT:
                t_stop      = 0 # datetime.datetime(2023, 10, 1, 12, 30, 0)
                PLOT_OPTION = 2
                # PLOT_OPTION 1: plot rate across multiple networks for selected period.
                # PLOT_OPTION 2: plot rate(s) on slected network [dict] for a selected period.
                syms = ['eth_usd']
                plotRates(dictionary, period, syms, t_stop, PLOT_OPTION)
    
    if OPTION == 1:
        # update SELECTED RATES for a single time period
        # convert_syms = [ 'avax_usd', 'usdc_usd' ]
        syms = [ 'mana_usd', 'matic_usd' ]
        period = '12_week'
        folders_dict = START_TIMES(None)
        for sym in syms:
            print('\n---------------------------')
            addr = dictionary[sym]
            print(f'creating {sym} {period} data table...')
            createDataTable(addr, sym, period, H) 

        #-------- plotting
        if PLOT:
                t_stop     = 0 # datetime.datetime(2023, 10, 1, 12, 30, 0)
                PLOT_OPTION = 1
                # PLOT_OPTION 1: plot rates across multiple networks for selected period.
                # PLOT_OPTION 2: plot multiple rates on slected network dict for a selected period.
                syms = ['eth_usd']
                plotRates(dictionary, period, syms, t_stop, PLOT_OPTION)           
                
    if OPTION == 2:
        # update ALL time period folders in selected network/ dictionary
        sym  = 'link_usd'  
        syms = [sym] ; t_stop = 0 # for PLOT
        addr = dictionary[sym]
        folders_dict = START_TIMES(None)
        for period, tuple_ in folders_dict.items():
            print('\n---------------------------')
            h, start_time = tuple_
            print(f'creating {period} {convertSym} data table...')
            createDataTable(addr, sym, period, H=0) 
            
            #-------- plotting
            if PLOT:
                    t_stop     = 0 # datetime.datetime(2023, 10, 1, 12, 30, 0)
                    PLOT_OPTION = 1
                    # PLOT_OPTION 1: plot rates across multiple networks for selected period.
                    # PLOT_OPTION 2: plot multiple rates on slected network dict for a selected period.
                    plotRates(dictionary, period, syms, t_stop, PLOT_OPTION)
        
    if OPTION == 3:
        if NETWORK not in LIVE_ENVS:
            print('   must run on live network!!')
            sys.exit(0)
        get_latest_rates(dictionary, True)