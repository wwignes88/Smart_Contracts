from scripts.Load.helpful_scripts import (loadPool, 
                                          getConfigAddress,
                                          get_contract_from_abi, 
                                          get_accounts,
                                          getNextTick,
                                          getTickInfo,
                                          getTickInfo,
                                          getNFTPosition,
                                          getPoolPosition,
                                          time,
                                          gas_controls,
                                          MIN_TICK, MAX_TICK,
                                          network)
from scripts.Load.DICTS import TEST_ENVS, LIVE_ENVS
import numpy as np
import pandas as pd
import os
import plotly.graph_objs as go
import plotly.express as px
import plotly.offline as pyo
from plotly.subplots import make_subplots
import time, sys
from pathlib import Path
import os.path

# account  : 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce # Goog
# accountII: 0x6dFa1b0235f1150008B23B2D918F87D4775fBba9 # Explor

#===========  TICKS  =============

# ---------- UPDATE TICK INFO TABLE
def updateTicksInfoFile(
        pool, 
        poolName, 
        tick0, 
        tickStart, 
        NumTicks, 
        tick_spacing, 
        zeroForOne,
        updateTick0):
    
    print('\n---------updateTicksInfoFile:')
    PRINT = False
    
    _network = network.show_active()
    if _network in LIVE_ENVS:
        data_file_path = f'DataTables//'+poolName+f'_{tick_spacing}.csv'
    if _network in TEST_ENVS:
        data_file_path = f'DataTables//_test_env//'+poolName+f'_{tick_spacing}.csv'
        
        
    # check if file path exists.
    dfExists = os.path.exists(data_file_path)

    # column headers 
    _headers = np.array([
        'tick',
        'liquidityGross',
        'liquidityNet',
        'feeGrowthOut0',
        'feeGrowthOut1',
        'tickCumulativeOut',
        'secsPerLiquidity',
        'secsOut',
        'initialized'
    ])   
    
    # if dataFrame exists, split into two depending on zeroForOne direction.
    # one data frame will be updated, the other will not be. we then merge the two 
    # back together later.
    if dfExists:
        df = pd.read_csv(data_file_path) # omit first row (tick0)
        tick0Row = df.iloc[0].values
        df = df[1:]
        
        # find index of starting tick value
        dfIndexed = df.set_index('tick')
        print(f'\ndfIndexed: \n{dfIndexed.iloc[:, :2]}...')
        start_index  = dfIndexed.index.get_loc(tickStart)
        print(f'\nstarting update @ row {start_index}')

        
        # leftward updates
        if zeroForOne:
            if len(df) > start_index+1:
                df_notUpdating = df[start_index+1:]
                df_Updating    = df[:start_index+1]
            if len(df) < start_index+1:
                df_notUpdating = pd.DataFrame() 
                df_Updating    = df
        
        # rightward updates
        if zeroForOne==False:
            df_notUpdating = df[:start_index]
            df_Updating    = df[start_index:]       


        df_Updating_values    = df_Updating.values
        df_notUpdating_values = df_notUpdating.values
        print(f'\nNOT Updating values: \n{df_notUpdating_values[:,:2]}')
        print(f'\nUpdating df : \n{df_Updating_values[:,:2]}')
        Lupdate    = len(df_Updating)
        LNotUpdate = len(df_notUpdating_values)
        print(f'\nLupdate: {Lupdate}')
        print(f'LNotUpdate: {LNotUpdate}')
    
    
    
    # create updated data [rows : numpy matrix]

    i = 1; tickCurrent = tickStart
    CurrentTickInfo    = getTickInfo(pool, tickCurrent, False, 0)
    while i <= NumTicks:

        time.sleep(2)
        tickRow         = np.array([tickCurrent])
        stepInitialized = CurrentTickInfo['initialized']
        print(f'\n----tickCurrent: {tickCurrent} [{stepInitialized}]]')

        for key, value in CurrentTickInfo.items():
            if PRINT:
                print(f'   {key}: {value}')
            tickRow = np.append(tickRow, value)
        print(f'   tickRow: {tickRow}')
        
        # initialize data matrix, or append row.
        if i == 1:
            UpdateData = tickRow
        if i > 1:
            UpdateData = np.vstack([UpdateData,tickRow])  
        
        # move to next tick
        tickCurrent, CurrentTickInfo = getNextTick(pool, tickCurrent, tick_spacing, zeroForOne, i)

        i += 1
    Ldata = len(UpdateData)
    print(f'Ldata: {Ldata}')
    
    
    
    # if dfExists, Merge data 
    if dfExists:
        if zeroForOne:
            if Ldata < Lupdate:
                df_Updating_values[::-1][:NumTicks] = UpdateData
            if Ldata >= Lupdate:
                df_Updating_values = UpdateData[::-1]

        if zeroForOne==False:
            if Ldata < Lupdate:
                df_Updating_values[:NumTicks] = UpdateData
            if Ldata >= Lupdate:
                df_Updating_values = UpdateData
                
        # merge update and not_update data
        if LNotUpdate > 0:
            if zeroForOne:
                df_data = np.vstack([df_Updating_values, df_notUpdating_values])     
            if zeroForOne == False:
                df_data = np.vstack([df_notUpdating_values, df_Updating_values])    
                
        if LNotUpdate == 0:
            df_data = df_Updating_values

    if dfExists==False:
        df_data = UpdateData
        updateTick0 = True # must update in this case

    
    # update tick0 row
    if updateTick0:
        time.sleep(2)
        Tick0Info   = getTickInfo(pool, tick0, False, 0)
        tick0Row    = np.array([tick0])
        for key, value in Tick0Info.items():
            if PRINT:
                print(f'   {key}: {value}')
            tick0Row = np.append(tick0Row, value)
        
    # stack merged data to tick0 row
    DF_data = np.vstack([tick0Row, df_data])
    df = pd.DataFrame(DF_data , columns=_headers) 
    # save df to .csv
    time.sleep(2)
    print(f'\nsaving df: \n{df}...')
    df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
 
#----------- PLOT TICKS
def plotTickValues(keysList, tickStart, tickStop, poolName, tick_spacing, PLOT):
    PRINT = False
    print('\n\n---------plotTickValues----------')

    # *tickInfo.csv always updates all key values.
    _network = network.show_active()
    if _network in LIVE_ENVS:
        data_file_path = f'DataTables//'+poolName+f'_{tick_spacing}.csv'
        plot_file_path = 'DataTables//TickPlots//'+poolName+f'_{tick_spacing}.html'
    if _network in TEST_ENVS:
        data_file_path = f'DataTables//_test_env//'+poolName+f'_{tick_spacing}.csv'
        plot_file_path = 'DataTables//_test_env//TickPlots//'+poolName+f'_{tick_spacing}.html'

    file_exists = os.path.exists(data_file_path)
    if file_exists == False:
        print(f'\n{file_exists} does not exist.')
        sys.exit(0)
        
    df       = pd.read_csv(data_file_path)
    keys     = df.columns.to_numpy() # label of values to plot
    
    # initizlie figure
    fig = go.Figure()
    _barWidth  = 10000
    
    
    
    
    # ------------------------ get tick0 row
    tick0DF = df.iloc[0:1]
    tick0DF = tick0DF.set_index('tick')

    
    tick0          = tick0DF.index.to_numpy()
    custom_data    = tick0DF

    # start plot with tick0 trace
    for key in keys:
        if key in keysList:
            keyValues = tick0DF[key].values
            if key == 'liquidityGross':
                keyColor = 'black'; _opacity = 0.6
                _offset  = 0
            if key == 'liquidityNet':
                keyColor = 'grey'; _opacity = 0.6
                _offset  = _barWidth
                    
            fig.add_trace(go.Bar(
                x=tick0, 
                y=keyValues,
                #width=_barWidths,
                #offset=_offset,
                name=key,
                marker_color = keyColor,
                opacity=_opacity,
                customdata=custom_data,
                hovertemplate=
                '<b>tick: %{x}</b><br>' +
                'liquidityGross: %{customdata[0]}<br>' +
                'liquidityNet: %{customdata[1]}<br>' +
                'feeGrowthOut0: %{customdata[2]}<br>' +
                'feeGrowthOut1: %{customdata[3]}<br>' +
                'tickCumulativeOut: %{customdata[4]}<br>' +
                'secsPerLiquidity: %{customdata[5]}<br>' +
                'secsOut: %{customdata[6]}<br>' +
                'initialized: %{customdata[7]}<br>'
            ))

    
    # omit tick0 row
    df = df[1:]


    
    """-----------------------------------------------------
     now we repeat the process to add a traces which cover 
     the rest of the ticks. It seems innefficient, but it
     is a result of how we've chosen to save our dataframe; 
     because we do not distinguish tick0's row by anythin other
     than the convention it is the first row, there is no dictionary
     key value which would identify it, and the loop which 
     creates traces to add depends on the column keys, not 
     row indices or tick values.
    """
    # locate tickStart/ tickStop and cut down df
    dfIndexed    = df.set_index('tick')
    start_index  = dfIndexed.index.get_loc(tickStart)
    stop_index   = dfIndexed.index.get_loc(tickStop)
    
    
    cutDF = df.iloc[start_index:stop_index+1]
    cutDF = cutDF.set_index('tick')
    
    if PRINT:
        print(f'\nTick0DF: \n{tick0DF.iloc[:, :2]}...')
        print(f'\nretrieved TickInfo df: \n{df.iloc[:, :2]}...')
        print(f'\nstart/stop indices: {start_index, stop_index}')
        print(f'\nplot df: \n{cutDF.iloc[:, :2]}...')
    
    ticks = cutDF.index.to_numpy()
    # Create customdata for hover info
    custom_data = cutDF

    for key in keys:
        if key in keysList:
            keyValues = cutDF[key].values
            if key == 'liquidityGross':
                keyColor = 'blue'; _opacity = 0.6
                _offset  = 0
            if key == 'liquidityNet':
                keyColor = 'red'; _opacity = 0.6
                _offset  = _barWidth
                    
            fig.add_trace(go.Bar(
                x=ticks, 
                y=keyValues,
                #width=_barWidths,
                #offset=_offset,
                name=key,
                marker_color = keyColor,
                opacity=_opacity,
                customdata=custom_data,
                hovertemplate=
                '<b>tick: %{x}</b><br>' +
                'liquidityGross: %{customdata[0]}<br>' +
                'liquidityNet: %{customdata[1]}<br>' +
                'feeGrowthOut0: %{customdata[2]}<br>' +
                'feeGrowthOut1: %{customdata[3]}<br>' +
                'tickCumulativeOut: %{customdata[4]}<br>' +
                'secsPerLiquidity: %{customdata[5]}<br>' +
                'secsOut: %{customdata[6]}<br>' +
                'initialized: %{customdata[7]}<br>'
            ))
            



    #---------------------------------------------------

    # if only plotting pool ticks, PLOT = True. When plotting pool ticks
    # + NFT positions, PLOT = False.
    if PLOT:
        fig.update_layout(
            title='title',
            barmode='group',
            bargap=0.8,
            bargroupgap=0
        )
        fig.update_xaxes(range=[-1000, tickStop])
    
        # check if plot already exists. crete if not. override if so.

        pyo.plot(fig, filename=plot_file_path)
    
    return fig



#===========  POSITION  =============
# ---------- UPDATE NFT POSITION INFO 
def updateNFTPositionsFile():
    account    = get_accounts(0) 
    liquid     = get_contract_from_abi('MliquidityMiner')
    ManagerII  = get_contract_from_abi('MNonfungiblePositionManagerII')

    #---------------- GET TOKEN ID's
    mytokenIdCount = liquid.getTokenCount(account.address)
    mytokenIds     = liquid.getTokenIds(account.address)
    print(f'mytokenIdCount: {mytokenIdCount}')

    if mytokenIdCount == 0:
        print(f'\nno liquidity positions minted.')
        sys.exit(0)
    
    #---------------- UPDATE NFTPositions.cvs
    # create dataFrame
    data = np.array([
        'tokenId',
        'nonce',
        'operator',
        'token0SYM',
        'token1SYM',
        'fee',
        'tickLow',
        'tickHigh',
        'liquidity',
        'feeGrowthIn',
        'feeGrowthOut',
        'token0Owed',
        'token1Owed'
    ])

    mytokenIds = [2] #  <<<---------------- xxx
    
    for tokenId in mytokenIds:
        print(f'\n----POSITION {tokenId} INFO:')
        NFTRow = np.array([tokenId])
        
        NFTposition   = getNFTPosition(ManagerII, tokenId, account, True)
        for key, value in NFTposition.items():
            print(f'   {key}: {value}')
            NFTRow = np.append(NFTRow, value)

    
    data = np.vstack([data,NFTRow])  
      
    # save dataFram to .csv file
    data_file_path = f'DataTables//NFTPositions.csv'      
    df = pd.DataFrame(data[1:] , columns=data[0]) 
    print(f'\nsaving df: \n{df}...')
    time.sleep(2)
    # save df to .csv
    df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
    df = df.set_index('tokenId')
    print(f'\nsaved df: \n{df}...')

# ---------- UPDATE POOL POSITION INFO
def updatePoolPositionsFile():
    account    = get_accounts(0) 
    liquid     = get_contract('MliquidityMiner')
    ManagerII  = get_contract('MNonfungiblePositionManagerII')

    #---------------- GET TOKEN ID's
    mytokenIdCount = liquid.getTokenCount(account.address)
    mytokenIds     = liquid.getTokenIds(account.address)
    print(f'mytokenIdCount: {mytokenIdCount}')

    if mytokenIdCount == 0:
        print(f'\nno liquidity positions minted.')
        sys.exit(0)
    
    #---------------- UPDATE NFTPositions.cvs
    # create dataFrame
    data = np.array([
        'tokenId',
        'liquidity',
        'feeGrowthIn0',
        'feeGrowthIn1',
        'token0Owed',
        'token1Owed'
    ])

    mytokenIds = [2]  #  <<----------  xxx
    
    for tokenId in mytokenIds:
        print(f'\n----POSITION {tokenId} INFO:')
        
        # get corresponding NFT position and some params
        NFTposition = getNFTPosition(ManagerII, tokenId, account, True)
        token0 = NFTposition['token0']  ; token1 = NFTposition['token1'] 
        TL     = NFTposition['tickHigh']; TH     = NFTposition['tickLow']
        fee    = NFTposition['fee']
        
        # load pool params
        (pool, slot0, liquidity, tick_spacing) = loadPool(token0, token1, fee, account)
        tick0  = slot0['tick']

        # pool position
        PoolPositionOwner = ManagerII.address
        PoolPosition      = getPoolPosition(pool, PoolPositionOwner, TL, TH, True)

        # construct the row for tokenId
        POOLRow = np.array([tokenId])
        for key, value in PoolPosition.items():
            print(f'   {key}: {value}')
            POOLRow = np.append(POOLRow, value)
    
    
        data = np.vstack([data,POOLRow])  
      
        # save dataFram to .csv file
        data_file_path = f'DataTables//POOLPositions.csv'      
        df = pd.DataFrame(data[1:] , columns=data[0]) 
        print(f'\nsaving df: \n{df}...')
        time.sleep(2)
        # save df to .csv
        df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
        df = df.set_index('tokenId')
        print(f'\nsaved df: \n{df}...')

#----------- PLOT NFT POSITION
def plotNFTPosition(keysList, tokenId, tickStart, tickStop,  plotName, PLOT):
    
    PRINT = False
    
    print('\n---------plotNFTPosition------------')
    data_file_path = f'DataTables//NFTPositions.csv'
    df = pd.read_csv(data_file_path)
    unique_token_ids = df['tokenId'].unique()
    keys      = df.columns.to_numpy()
    dfIndexed = df.set_index('tokenId')
    
   
    TL = dfIndexed.loc[tokenId, 'tickLow'] ; 
    TH = dfIndexed.loc[tokenId, 'tickHigh']
    ΔT = TH-TL ; BarSpacing = ΔT/len(keysList)

    # Create customdata for hover info
    # locate what row number tokenId corresponds to
    rowNum = dfIndexed.index.get_loc(tokenId)
    # create new single row dataframe
    custom_dataT = df.loc[rowNum].to_frame()
    custom_data  = custom_dataT.transpose()
    fig = go.Figure()

    plotValues    = np.array([])
    plotHeaders   = np.array([])
    barColors     = []
    barPositions  = np.array([])
    i = 0.5
    for key in keys:
        if key in keysList:
            keyValue = dfIndexed.loc[tokenId, key]
            #print(f' {key}: {keyValue} ({type(keyValue)})')
            
            if key == 'liquidity':
                barColor = 'blue'
                keyValue = int(keyValue)*1e-18
                barColors.append('blue')
            if key == 'feeGrowthIn':
                barColor = 'green'
                keyValue = int(keyValue)*3*1e-18
                barColors.append('green')
                #keyValue = 20
            if key == 'feeGrowthOut':
                keyValue = int(keyValue)*2e-18
                #keyValue = 50
                barColor = 'red'
                barColors.append('red')
            if key == 'token0Owed':
                barColors.append('grey')   
            if key == 'token1Owed':
                barColors.append('black')
                    
            plotHeaders   = np.append(plotHeaders, key+f' [{tokenId}]')
            barPositions  = np.append(barPositions, TL+BarSpacing*i)
            plotValues    = np.append(plotValues, keyValue)
            i += 1
        

            # Add traces
            fig.add_trace(go.Bar(
                x=[TL+BarSpacing*i], 
                y=[keyValue],
                text=key,       # Text to appear on each bar
                textposition = 'auto',  # Position of the text
                marker_color = [barColor],
                opacity=0.6,
                customdata=custom_data,
                hovertemplate=
                'tokenId: %{customdata[0]}<br>' +
                'nonce: %{customdata[1]}<br>' +
                'operator: %{customdata[2]}<br>' +
                'token0SYM: %{customdata[3]}<br>' +
                'token1SYM: %{customdata[4]}<br>' +
                'fee: %{customdata[5]}<br>' +
                'tickLow: %{customdata[6]}<br>' +
                'tickHigh: %{customdata[7]}<br>' +
                'liquidity: %{customdata[8]}<br>' +
                'feeGrowthIn: %{customdata[9]}<br>' +
                'feeGrowthOut: %{customdata[10]}<br>' 
            ))

    if PRINT:
        print(f'\nretrieved NFT: \n{custom_dataT}...')
        print(f'\nbarPositions : {barPositions}...')
        print(f'barColors    : {barColors}...')
        print(f'plotValues   : {plotValues}...')
        
    if PLOT:
        
        fig.update_xaxes(range=[tickStart, tickStop])

        fig.update_layout(
            title='Lower figure',
            barmode='group',
            bargap=0.0,
            bargroupgap=0
        )
        
        # check if plot already exists. crete if not. override if so.
        plot_file_path = 'DataTables//NFTPlots//'+plotName+'.html'
        pyo.plot(fig, filename=plot_file_path)
    
    return fig




#----------- MAIN
def main():
    print(f'\n\n\n======= PLOT')
    poolNum = 1
    
    account = get_accounts(0) 
    t0 = 'weth' ; token0 = getConfigAddress(t0)
    t1 = 'link' ; token1 = getConfigAddress(t1)
    fee = 3000
    
    # Load pool + pool parameters
    (pool, slot0, liquidity, tick_spacing) = loadPool(token0, token1, fee, account)
    tick0 = slot0['tick']
    print(f'\nloaded {t0}/{t1} pool. tick0 = {tick0}')
    print(f'   tick0        = {tick0}')
    print(f'   tick_spacing = {tick_spacing}')
    print(f'   liquidity    = {liquidity}')
    

    #================ SELECTION ================

    OPTIONS = [5]
    
    # UPDATE TICK INFO DATA FILE
    if 1 in OPTIONS:
        # gas_controls(account, set_gas_limit=False, priority_fee=False)
        tickStart   = 0;   
        zeroForOne  = False; 
        NumTicks    = 6    ;   
        updateTick0 = False
        
        updateTicksInfoFile(
            pool, 
            'shitPool', 
            tick0, 
            tickStart, 
            NumTicks, 
            tick_spacing, 
            zeroForOne,
            updateTick0)

    # PLOT TICK INFO
    if 2 in OPTIONS:
        keyList   = [
            'liquidityGross',
            'liquidityNet'
            ] ; 
        tickStart = 0 ; tickStop = 61380 ; 
        poolName  = 'shitPool'
        plotTickValues(keyList, tickStart, tickStop, poolName, tick_spacing, True)

    # UPDATE POSITION INFO
    if 3 in OPTIONS:
        updateNFTPositionsFile()
        updatePoolPositionsFile()
        
    # PLOT NFT POSITION
    if 4 in OPTIONS:
        NFTPlotKeyList   = [
            'feeGrowthIn',
            'feeGrowthOut',
            'liquidity'
            ] ; 
        tickStart = 0 ; tickStop = 138180  # bounds
        plotNFTPosition(NFTPlotKeyList, 2, tickStart, tickStop, 'testing', True)
    
    # PLOT NFT+TICKS POSITION
    if 5 in OPTIONS:
        
        figList = []
        
        #------------- CREATE TICK GRAPH
        TickKeyList = [
            'liquidityGross',
            'liquidityNet'
            ] ; 
        tickStart = 15300 ; tickStop = 61380 ; 
        poolName  = 'shitPool'
        tick_fig  = plotTickValues(TickKeyList, tickStart, tickStop, poolName, tick_spacing,  False)
        figList.append(tick_fig)
        
        #------------- CREATE NFT GRAPH
        tokenIds = [2,3]
        numNFTplots = len(tokenIds)
        NFTPlotKeyList   = [
            'feeGrowthIn',
            'feeGrowthOut',
            'liquidity'
            ] ; 
        for tokenId in tokenIds:
            NFT_fig = plotNFTPosition(NFTPlotKeyList, tokenId, tickStart, tickStop, 'testing', False)
            figList.append(NFT_fig)
        

        #------------ MAKE COMBINED FIGURE:
        # Step 3: Use make_subplots to combine figures
        fig_combined = make_subplots(rows=numNFTplots+1, cols=1, shared_xaxes=True)

        # Step 4: Add individual figures as subplots
        for i, f in enumerate(figList):
            for trace in f.data:
                fig_combined.add_trace(trace, row=i+1, col=1)

        fig_combined.update_layout(
            barmode='group',
            bargap=0.0,
            bargroupgap=0
        )

        # check if plot already exists. crete if not. override if so.
        plot_file_path = f'DataTables//NFTPlots//combined_'+poolName+f'_{tick_spacing}.html'
        pyo.plot(fig_combined, filename=plot_file_path)
    