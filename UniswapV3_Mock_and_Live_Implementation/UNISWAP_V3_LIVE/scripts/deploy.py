import time
from scripts.Load.helpful_scripts import (
    get_accounts, 
    gas_controls,
    CurrencyConvert,
    sys
)
from scripts.Load.BrownieFuncs import UpdateConfigAdresses
from brownie import (accounts, interface, network, config, Contract,
                    MyMath,
                    LiquidityMiner,
                    MERC20
                    )
import numpy as np
# account  : 0x588c3e4FA14b43fdB25D9C2a4247b3F2ba76aAce # Goog
# accountII: 0x6dFa1b0235f1150008B23B2D918F87D4775fBba9 # explorer

def deploy():
    print('\n=============== deploy =====================\n')

    # load account
    account = get_accounts(0) 
    acct_native_bal = gas_controls(account, set_gas_limit=False, priority_fee=False)



    calculate_deployment_cost = False
    if calculate_deployment_cost:

        # Folder from which to pull rates (see PLOTS directory). 'None' for chainlink request.
        NetworkFolder = 'avalanche'

        # have amount = account balance (from gas controls ^^^)
        deploymentFunds = acct_native_bal
        myUSD           =  CurrencyConvert(deploymentFunds, 'ETH', 'USD', 'my bal      :',
                                           NetworkFolder)

        # amount needed to deploy (get from error message when deployment fails)
        deployment_cost = 65138713740000000
        deploymentUSD   =  CurrencyConvert(deployment_cost, 'ETH', 'USD', 'deploy cost  :',
                                           NetworkFolder)

        # difference = need - have
        needAmount      =  deployment_cost - deploymentFunds
        neededUSD       =  CurrencyConvert(needAmount     , 'ETH', 'USD', 'needed       :',
                                           NetworkFolder)


        sys.exit(0)


    # --------- DEPLOYMENTS
    # 1 SWAPPER
    # 2 LIQUIDITY MINER
    deployments = [2]
    if calculate_deployment_cost == False:

        try:

            # 0 ERC20s 
            # 1 SWAPPER
            # 2 LIQUIDITY MINER
            # ERC20s
            if 0 in deployments:
                print('\ndeploying ERC20s...')
                
                token_list = ['weth', 'link']
                for token_name in token_list:
                    symbol    = token_name.upper()
                    print(f'\n   deploying {symbol} ...')
                    mockERC20 =  MERC20.deploy(token_name,
                                                symbol,
                                                {"from": account})
                    UpdateConfigAdresses(mockERC20, token_name)
                    input('proceed to mint?')
                    tx = mockERC20.mint(100*1e18, account.address, {"from":account})
                    tx.wait(1)
                    


                #print('\ndeploying test...')
                #a_test = A.deploy({"from": account})    
                #UpdateConfigAdresses(a_test, 'a_test')
                sys.exit(0)

            # MyMath
            if 1 in deployments:
                # deployment_cost = $151.45 - arbitrum
                print('\ndeploying MyMath...')
                my_math = MyMath.deploy( {"from": account} )
                UpdateConfigAdresses(my_math, 'MyMath')

            # Liquidity Miner
            if 2 in deployments:
                # deployment_cost = $174.31 - arbitrum
                NFPManagerAddress = config["networks"][network.show_active()]['NonfungiblePositionManager']
                ERC721manager     = interface.IV3NPMManager(NFPManagerAddress)
                print('\ndeploying Liquidity Miner...')
                liquidityMiner_ = LiquidityMiner.deploy(ERC721manager, {"from": account})
                UpdateConfigAdresses(liquidityMiner_, 'LiquidityMiner')

        except Exception as e:
            e = str(e)
            print(f' \n!!error!!: {e} ')

            if 'tx cost' in e:
                tx_cost_str = e.split("tx cost ")[1].split(",")[0].strip()
                overshot_str = e.split("overshot ")[1].split(":")[0].strip()

            if 'want' in e:
                tx_cost_str = e.split("have ")[1].split(" ")[0].strip()
                overshot_str = e.split("want ")[1].strip()

            print(f'\ntx coststr: {tx_cost_str} {len(tx_cost_str)} ')
            print(f'\novershot_str: {overshot_str} {len(overshot_str)} ')

            # Convert the extracted strings to integers
            tx_cost = int(tx_cost_str)
            overshot = int(overshot_str)
            #print(f'\n tx cost: {tx_cost} ({tx_cost*1e-18} wei)')
            #print(f'overshot: {overshot}  ({np.round(overshot*1e-18,3)} wei)')
            

            NetworkFolder  = 'avalanche'
            networkSym     = network.show_active().split('-')[0]
            deploymentUSD  =  CurrencyConvert(overshot, 'ETH', 'USD', f'{networkSym} deploy cost  :',
                                                NetworkFolder)


def main():
    deploy()


""" 

 have 
2075080000000000 want 
56738130120000000

"""