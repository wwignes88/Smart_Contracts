
from scripts.Load.helpful_scripts import (get_accounts,
                                          get_contract,
                                          time)
from scripts.Load.DICTS import MIN_TICK, MAX_TICK, Q96 
import sys
import numpy as np

def pAtTick(tick):
    return np.sqrt(1.0001**tick) * (2**96)

def assembleMath():
    print(f'\n\n----------ASSEMBLE MATH')

    """
    MINT AMOUNTS [pool 1]:
        token0 WETH 6.0
        token1 SAND 12.0
    POOL PARAMS:
        liquidity: 0
        tick0    : -887272  [p0   : 4295128739]
    L MINT RANGE:
        tickLow  : -887220   [pLow : 4306310044]
        tickHigh : -887160   [pHigh: 4319247724]
    L AMOUNTS:

    !!! L_for_0 = 0 !!!
        int.: 0
        L: 0
    """
    account, accountII = get_accounts()
    my_math   = get_contract('MyMath')

    tick0    = -887272 
    tickLow  = -887220 
    tickHigh = -887160 

    pA = my_math.sqrtPatTick(tickLow)
    pB = my_math.sqrtPatTick(tickHigh)
    p0 = my_math.sqrtPatTick(tick0)

    print(f'PARAMS:')
    print(f'   tick0    : {tick0}   [p0   : {p0}]')
    print(f'   tickLow  : {tickLow}   [pLow : {pA}]')
    print(f'   tickHigh : {tickHigh}   [pHigh: {pB}]')

    # pAtTick(tick)
    print(f'COMPARE:')
    print(f'   p0   : {pAtTick(tick0)}')
    print(f'   pLow : {pAtTick(tickLow)}')
    print(f'   pHigh: {pAtTick(tickHigh)}')

    #----------------------
    A = pA
    B = pB
    denominator = Q96
    
    prod0_ = A*B
    res0_  = prod0_/denominator
    print(F'\nMulDiv0 OUTPUTS [CALCULATED]:')
    print(f'     prod0  : {prod0_}') 
    print(f'     res0   : {res0_}') 
    
    
    (res0, prod0) = my_math.MulDiv0(A, B, denominator)
    print(F'\nMulDiv0 OUTPUTS:')
    print(f'     prod0  : {prod0}') 
    print(f'     res0   : {res0}') 
    sys.exit(0)
    
    #-----------------------
    
    MOD = my_math.MOD(pA,pB)
    
    (p0, p1, r, twos, inv, res) = my_math.MulDivTroubleshoot(pB, pA, Q96, 0)
    print(F'\nMulDiv OUTPUTS:')
    print(f'     MOD  : {MOD}') 
    print(f'     p0  : {p0}') 
    print(f'     p1  : {p1}') 
    print(f'     r   : {r}') 
    print(f'     twos: {twos}') 
    print(f'     inv : {inv}') 
    print(f'     res : {res}') 
    
def main():
    assembleMath()
    