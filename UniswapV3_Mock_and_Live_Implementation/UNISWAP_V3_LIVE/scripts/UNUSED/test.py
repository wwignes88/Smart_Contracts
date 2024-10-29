
from scripts.Load.helpful_scripts import get_contract, getERC20, get_accounts
from scripts.Load.BrownieFuncs import getEvents
from scripts.Load.EventWatcher import listenForEvent

def listenForEvents():
    account = get_accounts(0) 
    my_math = get_contract('MyMath')
    
    tickCurrent = 1500
    tickLimit   = 2000
    tickSpacing = 50
    option      = 2
    
    listenForEvent( [ 
                    [my_math, "SteppedA"], 
                    [my_math, "SteppedB"],
                    [my_math, "Swapped"]])
    
    tx = my_math.whileLoopEmission(tickCurrent, tickLimit, tickSpacing, option, {"from": account}) 
    tx.wait(1)
    
    #getEvents(tx)
    
    
def MultipHopParams():
    print('\n============= MultipHopParams.py ===============\n')

    my_math = get_contract('MyMath')
    factory = get_contract('MFactory')
    
    t0 = 'weth' 
    t1 = 'sand' 
    t2 = 'link'

    token0 = get_contract(t0)
    token1 = get_contract(t1)
    token2 = get_contract(t2)

    poolFee = 3000
    poolNum = 1
    
    (tokenInAddress, 
     tokenOutSddress, 
     fee, 
     zeroForOne, 
     pool_address) = my_math.MultiHopPathParams(
         factory.address,
         token1.address,
         token0.address,
         token2.address,
         poolFee,
         poolNum
     )

    tokenIn  = getERC20(tokenInAddress)
    tokenOut = getERC20(tokenOutSddress)
    
    print(f'\nMultiHop Params:')
    print(f'   tokenIn     : {tokenIn.symbol()}')
    print(f'   tokenOut    : {tokenOut.symbol()}')
    print(f'   fee         : {fee}')
    print(f'   zeroForOne  : {zeroForOne}')
    print(f'   pool_address: {pool_address}')
    

def main():
    option = 1
    if option == 1:
        listenForEvents()
    if option == 2:
        MultipHopParams()
    
    print('\n=============== end MultipHopParams.py =====================\n')

