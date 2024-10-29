from scripts.Load.helpful_scripts import (loadPool, 
                                          get_contract, 
                                          get_accounts,
                                          getNextTick,
                                          getTickInfo,
                                          getNFTPosition,
                                          getPoolPosition,
                                          time,
                                          gas_controls,
                                          getERC20,
                                          MIN_TICK, MAX_TICK)
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px
import plotly.offline as pyo
from plotly.subplots import make_subplots
import time, sys
from pathlib import Path


#===========  TICKS  =============
# ---------- UPDATE TICK INFO TABLE
def updateTicksInfoFile(pool, tickCurrent, tick_spacing, zeroForOne):
    data = np.array([
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
    i = 1; tickCurrent = tickStart
    while i < NumTicks:
        tickNext, tickNextInfo = getNextTick(pool, tickCurrent, tick_spacing, zeroForOne)
        tickRow = np.array([tickNext])
        stepInitialized = tickNextInfo['initialized']
        print(f'\n----tickNext: {tickNext} [{stepInitialized}]]')

        for key, value in tickNextInfo.items():
            print(f'   {key}: {value}')
            tickRow = np.append(tickRow, value)
        print(f'   tickRow: {tickRow}')
        data = np.vstack([data,tickRow])  
        tickCurrent = tickNext
        i += 1
    
    data_file_path = f'DataTables//tickInfo.csv'


    df = pd.DataFrame(data[1:] , columns=data[0]) 
    print(f'\nsaving df: \n{df}...')
    time.sleep(2)
    # save df to .csv
    df.to_csv(data_file_path, index=False)  # Set index=False to omit writing row numbers
    df = df.set_index('tick')
    print(f'\nsaved df: \n{df}...')
 
#----------- CHECK IF FILE EXISTS 
def check_dir(dir_path):
    
    path = Path(dir_path)
    print(f'\npath: {dir(path)}')
    sys.exit(0)
    # Check if the file already exists, create if not.
    if  path.is_file():
        # Create the file
        [replace]
    else:
        pass

#----------- PLOT TICKS
def plotTickValues(keysList, tickStart, tickStop, plotName, PLOT):
    scatter_traces = []
    
    # *tickInfo.csv always updates all key values.
    data_file_path = f'DataTables//tickInfo.csv'
    df = pd.read_csv(data_file_path)
    df = df.set_index('tick')
    #print(f'\nretrieved TickInfo df: \n{df}...')
    
    ticks = df.index.to_numpy()
    keys  = df.columns.to_numpy()

    # Create customdata for hover info
    custom_data = df
    input(F' tick custom df: {custom_data}')

    # *this will need some tweaking if more or less than 2 tick 
    #  attributes are plotted.
    _barWidth  = 1000
    _barWidths = _barWidth*np.ones(len(ticks))
    fig = go.Figure()
    for key in keys:
        if key in keysList:
            keyValues= df[key].values
            if key == 'liquidityGross':
                keyColor = 'blue'; _opacity = 0.6
                _offset  = 0
            if key == 'liquidityNet':
                keyColor = 'red'; _opacity = 0.6
                _offset  = _barWidth
                    
            fig.add_trace(go.Bar(
                x=ticks, 
                y=keyValues,
                width=_barWidths,
                offset=_offset,
                name=key,
                marker_color = keyColor,
                opacity=_opacity,
                customdata=custom_data,
                hovertemplate=
                '<b>tick: %{x}</b><br>' +
                'liquidityGross: %{y}<br>' +
                'liquidityNet: %{customdata[1]}<br>' +
                'feeGrowthOut0: %{customdata[2]}<br>' +
                'feeGrowthOut1: %{customdata[3]}<br>' +
                'tickCumulativeOut: %{customdata[4]}<br>' +
                'secsPerLiquidity: %{customdata[5]}<br>' +
                'secsOut: %{customdata[6]}<br>' +
                'initialized: %{customdata[7]}<br>'
            ))
            



    #---------------------------------------------------

    if PLOT:
        fig.update_layout(
            title='title',
            barmode='group',
            bargap=0.0,
            bargroupgap=0
        )
        
    
        # check if plot already exists. crete if not. override if so.
        plot_file_path = 'DataTables//TickPlots//'+plotName+'.html'

        pyo.plot(fig, filename=plot_file_path)
    
    return fig



#===========  POSITION  =============
# ---------- UPDATE NFT POSITION INFO 
def updateNFTPositionsFile():
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

    data_file_path = f'DataTables//NFTPositions.csv'
    df = pd.read_csv(data_file_path)
    unique_token_ids = df['tokenId'].unique()
    keys     = df.columns.to_numpy()
    dfIndexed       = df.set_index('tokenId')
    #print(f'\nretrieved NFT df: \n{df}...')
   
    TL = dfIndexed.loc[tokenId, 'tickLow'] ; 
    TH = dfIndexed.loc[tokenId, 'tickHigh']
    ΔT = TH-TL ; BarSpacing = ΔT/len(keysList)
        
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
                keyValue = int(keyValue)*1e-18
                barColors.append('blue')
            if key == 'feeGrowthIn':
                barColors.append('green')
                #keyValue = 20
            if key == 'feeGrowthOut':
                #keyValue = 50
                barColors.append('red')
            if key == 'token0Owed':
                barColors.append('grey')   
            if key == 'token1Owed':
                barColors.append('black')
                    
            plotHeaders   = np.append(plotHeaders, key+f' [{tokenId}]')
            barPositions  = np.append(barPositions, TL+BarSpacing*i)
            plotValues    = np.append(plotValues, keyValue)
            i += 1
        
 
    # Create customdata for hover info
    
    # locate what row number tokenId corresponds to
    rowNum = dfIndexed.index.get_loc(tokenId)
    # create new single row dataframe
    custom_data = df.loc[rowNum].to_frame().transpose()
    vals = custom_data.values

    # !!! hover data won't populate for more than first bar
    
    fig = go.Figure()
    # Add traces
    fig.add_trace(go.Bar(
        x=barPositions, 
        y=plotValues,
        text=plotHeaders,       # Text to appear on each bar
        textposition = 'auto',  # Position of the text
        marker_color = barColors,
        opacity=0.6,
        customdata=vals,
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
    #gas_controls(account, set_gas_limit=False, priority_fee=False)
    my_math = get_contract('MyMath')
    
    t0 = 'weth' 
    t1 = 'sand' 
    t2 = 'link' 

    token0 = get_contract(t0)
    token1 = get_contract(t1)
    token2 = get_contract(t2)
            
    # Load pool 
    fee = 3000
    if poolNum == 1:
        (pool, slot0, liquidity, tick_spacing) = loadPool(token0, token1, fee, account)
    if poolNum == 2:
        (pool, slot0, liquidity, tick_spacing) = loadPool(token1, token2, fee, account)
    
    Lpool  = pool.liquidity()
    tick0  = slot0['tick']

    # paid before the other.
    TokenA = getERC20(pool.token0())
    TokenB = getERC20(pool.token1())
    print(f'      {TokenA.symbol()}/  {TokenB.symbol()} pool')

    #================ SELECTION ================

    OPTIONS = [5]
    
    # UPDATE TICK INFO DATA FILE
    if 1 in OPTIONS:
        tickStart = tick0;   zeroForOne = False
        updateTicksInfoFile(pool, tickStart, tick_spacing, zeroForOne)
    
    # PLOT TICK INFO
    if 2 in OPTIONS:
        keyList   = [
            'liquidityGross',
            'liquidityNet'
            ] ; 
        tickStart = 0 ; tickStop = 138180 ; 
        plotName  = 'testing'
        plotTickValues(keyList, tickStart, tickStop, plotName, True)

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
        TickKeyList   = [
            'liquidityGross',
            'liquidityNet'
            ] ; 
        tickStart = 0 ; tickStop = 138180 ; 
        plotName  = 'testing'
        tick_fig  = plotTickValues(TickKeyList, tickStart, tickStop, plotName, False)
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
        plot_file_path = 'DataTables//NFTPlots//combined_'+plotName+'.html'
        pyo.plot(fig_combined, filename=plot_file_path)
    