
"""
data table files are generated in SUBGRAPH project and need to be 
imported to DataTables/LiquidityPools in this project manually.
Use this plot script to see liquidity values of various pools.
For detailed bar graphs of positions held in individual pools
see UNSWAP projects. 

In summary;

    - SUBGRAPH :: query for pools and their liquidity values
    - PLOTS    :: plot the resulting query data
    - UNISWAP  :: plot detailed position info of a single pool

this seems innefficient, but there is a reason for it. Querying with
subraph is its own software package so deserves its own project directory.
Plotting position info for a single pool requires interacting with the pool
contract itself, so this is properly in the UNISWAP projects(s) (LIVE or MOCK).
We can easily put this script into the SUBGRAPH project so as to be able to 
get a visual of queried data, but I prefer it here so as to more easily
compare this queried [liquidity] data to trends in the prices [or rates] of
tokens.
"""
import sys #PATH_ = sys.path
import pandas as pd
import numpy as np

from brownie import network

from scripts.Load.helpful_scripts import (getPoolFromAddress,
                                          get_accounts,
                                          gas_controls)

def findPoolNetwork(filename_):
    
    dir_path  = f'DataTables//LiquidityPools'
    data_file_path = dir_path + f'//{filename_}.csv'
    df = pd.read_csv(data_file_path)

    #poolSyms = df['poolSym'].values # x axis labels
    poolIds  = df['pool_id'].values
    liquidities_str = df['liquidity'].values

    # convert to wei units 
    liquidities  = liquidities_str.astype(float)*1e-18 
    LiquidiesWei    = liquidities.astype(int)



    #---------------------------------------------
    # cycle through pools, test if it is deployed.
    account = get_accounts(0)
    gas_controls(account, set_gas_limit=False, priority_fee=False)
    columns_ = np.array(['pool_id', 'poolSym','liquidity'])
    i = 0; j = 0
    for pool_address in poolIds:
        # Load pool 
        try:
            (pool, slot0, liquidity, tick_spacing, fee, token0, token1) = getPoolFromAddress(pool_address, account)
            tick0 = slot0['tick']
            sym0  = token0.symbol() 
            sym1  = token1.symbol() 

            print(f'\n loaded pool.')
            print(f'   token0       : {sym0}')
            print(f'   token1       : {sym1}')
            print(f'   liquidity    : {liquidity*1e-18} [{LiquidiesWei[i]}]')
            print(f'   tick0        : {slot0['tick']}')
            print(f'   tick_spacing : {tick_spacing}')
            print(f'   fee          : {fee}')
            pool_entry = np.array([pool_address, sym0+'_'+sym1, liquidity])
            if j == 0:
                network_pool_data = pool_entry
            if j > 0:
                network_pool_data = np.vstack([network_pool_data,pool_entry])
            j += 1
            if j > 5:
                break
        except Exception as e:
            print(f' \n!!error!!: {e}')
            print(f' no pool @ entry i = {i}')
        i += 1

    df = pd.DataFrame(network_pool_data , columns=columns_) 
    print(f'\ndf: \n{df}')
    network_data_file_path = dir_path + f'//{network.show_active()}.csv'
    df.to_csv(network_data_file_path, index=False)  # Set index=False to omit writing row numbers
    sys.exit(0)



    #------------------------------------------------------
    PLOT = False 
    if PLOT:

        import plotly.graph_objs as go
        import plotly.express as px
        import plotly.offline as pyo

        LiquidWeiDF  = pd.DataFrame(liquidities)
        #print(f'liquidities: \n{liquidities}')

        # plot log scale?
        LOG = True
        if LOG:
            liquidities = np.log(liquidities)
            #print(f'LOG liquidities: \n{liquidities}')

        print(f'LiquidWeiDF: \n{LiquidWeiDF[0]}')
        # create figure
        scatter_traces = []
        fig = go.Figure()

        HOVER_DATA = True
        if HOVER_DATA:
            custom_data = df
            custom_data['liquidity'] = LiquidWeiDF[0]
            print(f'custom_data: \n{custom_data[:5]}')
            fig.add_trace(go.Bar(
                x = df['poolSym'], 
                y = liquidities,
                customdata=custom_data,
                hovertemplate=
                '<b>poolSym: %{customdata[1]}</b><br>' +
                'liquidity: %{customdata[2]}<br>' +
                'poolID: %{customdata[0]}<br>' 
            ))

        if not HOVER_DATA:
            custom_data = df
            fig.add_trace(go.Bar(
                x = poolSyms, 
                y = liquidities
            ))

        pyo.plot(fig, filename=filename_)


def main():
    findPoolNetwork('0_500_pool_queries')
    

