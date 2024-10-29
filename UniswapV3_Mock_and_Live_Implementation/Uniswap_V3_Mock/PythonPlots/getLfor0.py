import numpy as np
import matplotlib.pyplot as plt
import sys
import time

MIN_SQRT_RATIO = 4295128739 
MAX_SQRT_RATIO = 1461446703485210103287273052203988822378723970342
MIN_TICK = -887272
           #7098180
MAX_TICK = -MIN_TICK
Q96 = 2**96 # 79228162514264337593543950336  = 7.92*1e28

tick_spacing = 60

def getSqrtRatioAtTick(tick):
    if tick%tick_spacing != 0:
        print(F'   % tick value')
        sys.exit(0)
    #print(f'\n p = {np.sqrt(1.0001**tick)}, {type(np.sqrt(1.0001**tick))}')
    #input(f' Q96 = {2**96}, {2**96}')
    return np.sqrt(1.0001**tick) * (2**96)

def getLForZero(x, tickLow, tickHigh):
    pL = getSqrtRatioAtTick(tickLow)
    pU = getSqrtRatioAtTick(tickHigh)
    intermediate = pL*pU/Q96
    if intermediate < 0.5:
        print('\n   intermediate == 0!!')
        sys.exit(0)     
    L = x*intermediate/(pU - pL)
    return L
    

OPTION = 1

if OPTION == 0:
    tickLow  = -469140 + 100*tick_spacing
    tickHigh = -860220 
    x = 6*1e18
    L = getLForZero(x, tickLow, tickHigh)
    print(f'\nL = {L}')
    
    
if OPTION == 1:
    
    # SET PARAMETERS
    x = 12*1e18
    tickLow = -875580
    
    
    pA      = getSqrtRatioAtTick(tickLow)
    print(f'pA    = {pA}')
    # find pB such that pA*pB/Q96 >= 0.5 so that intermediate >= 1
    # * see getLiquidityForAmount0 in LiquidityAmounts.sol library
    tick = tickLow
    pB = 0
    intermediateSwitch = False
    STOP = False
    while STOP == False:
        tick += 2*tick_spacing
        pTick = getSqrtRatioAtTick(tick)
        
        intermediate = pTick*pA/Q96
        print(f'intermediate({tick}) = {intermediate}')
        if intermediate > 1 and intermediateSwitch==False:
            print(f'   *intermediate = {intermediate} > 0 !!')
            time.sleep(2)
            intermediateSwitch = True
        if intermediateSwitch:
            L = getLForZero(x, tickLow, tick)
            print(f'L = {L}')
            if abs(L) > 1 :
                tickHigh = tick
                print(f'   |L| >= 0 @ tickHigh = {tickHigh}')
                pB = getSqrtRatioAtTick(tickHigh)
                print(f'   p({tick}) = {pB}')
                STOP = True
        if tick >= MAX_TICK:
            print('\nMAX_TICK exceeded.')
            break
    
   
    
    
    