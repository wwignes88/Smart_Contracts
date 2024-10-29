
from brownie import network
from scripts.Load.DICTS import *
from scripts.Load.helpful_scripts import (current_dateTime, 
                                          check_dir,
                                          get_data_df)
import sys
import time
import pandas as pd

import plotly.graph_objs as go
import plotly.express as px
import plotly.offline as pyo


def plotRates(dictionary, period, syms, t_stop, OPTION):
    
    h, t_start  = START_TIMES(period)
    
    scatter_traces = []

    # plot SINGLE RATE across MULTIPLE NETWORKS for selected period.
    if OPTION == 1:
        sym = syms # should be string input, not list
        dir_path  = f'DataTables//Graphs'
        filename_ = dir_path + f'//AcrossNetworks//{period}_{sym}.html'
        title_ = f"{sym}, Multi-network. {period}"
        NETWORKS_FOLDERS = getNetworksFolders()
        
        for ParentFolderName in NETWORKS_FOLDERS:
            
            try:
                data_file_path = f'DataTables//Tables//{ParentFolderName}//{period}//{sym}.csv'
                times,rates = get_data_df(data_file_path)

                trace = go.Scatter(x=times, y=rates, mode='lines', name=f'{ParentFolderName}')
                scatter_traces.append(trace)
            except:
                print(f'\n passed on {ParentFolderName}//{period}//{sym}.csv file.\n')
                time.sleep(1)

    #---- plot MULTIPLE RATES on SINGLE NETWORK dict for a selected period.
    if OPTION == 2:
        # syms should be list of strings
        network_name = dictionary['network']
        dir_path  = f'DataTables//Graphs//AcrossRates'
        filename_ = dir_path + f'//{period}.html'
        title_ = f"{network_name} network. multi-plot. {period}"
        for  sym in syms:
            addr = dictionary[sym]
            try:
                print(f'\n----retrieving {sym}.csv file...')
                data_file_path = f'DataTables//Tables//{network_name}//{period}//{sym}.csv'
                df = pd.read_csv(data_file_path)
                
                # df = df.set_index('time')
                # time = df.index.to_numpy()
                times = df['time'].values; print(f'   # data pts.: {len(times)}')
                rates = df[sym].values

                trace = go.Scatter(x=times, y=rates, mode='lines', name=f'{sym}')
                scatter_traces.append(trace)
            except:
                print(f'\n passed on {sym} file. Please create this file.\n')
                time.sleep(1)
        else:
            pass

    #-----------------
    
    if t_start == 0:
        t_start = min(times)
    if t_stop == 0:
        t_stop = current_dateTime()


    layout = go.Layout(
        title=title_,
        xaxis=dict(title='time',  range=[t_start, t_stop]),
        yaxis=dict(title="Value")
    )

    # Create a Figure object and add the scatter traces to it
    fig = go.Figure(data=scatter_traces, layout=layout)


    # Check if the directory exists, create it if not
    check_dir(dir_path)
    
    # Display the plot using the plotly.offline.plot function
    pyo.plot(fig, filename=filename_)
    
"""    
def main():
    print('\n     ======= plotRates.py ======')
    dictionary    = AVAX
    period        = '3_week'
    h,t_start     = START_TIMES(period)
    t_stop        = 0 # datetime.datetime(2023, 10, 1, 12, 30, 0)
    
    OPTION = 2
    
    # OPTION 1: plot rates across multiple networks for selected period.
    # OPTION 2: plot multiple rates on slected network dict for a selected period.

    #syms = ['avax_usd', 'usdc_usd'] # AVAX
    #syms = [ 'mana_usd', 'matic_usd'] # POLYGON
    syms = ['eth_usd']
    
    plotRates(dictionary, period, syms, t_start, t_stop, OPTION)
    print('\n')
    """
