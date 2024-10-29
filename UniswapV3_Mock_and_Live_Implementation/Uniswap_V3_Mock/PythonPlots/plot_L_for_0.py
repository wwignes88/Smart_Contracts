import numpy as np
import matplotlib.pyplot as plt
Q96 = 2**96
TICK_SPACING = 60
MIN_TICK  = -887272
MAX_TICK  = -MIN_TICK

def getSqrtRatioAtTick(tick):
    return np.sqrt(1.0001 ** tick)

def calculateL(x, tickLower, tickHigher):
    sqrtRatioAtTickLower  = getSqrtRatioAtTick(tickLower)
    sqrtRatioAtTickHigher = getSqrtRatioAtTick(tickHigher)
    
    # Adjusting the formula to match the given formula for L
    L = x / (1/sqrtRatioAtTickLower - 1/sqrtRatioAtTickHigher)
    return L


# Example values
x = 12*1e18  # Example liquidity amount
tickLower =  -860220
MIN = tickLower
MAX = tickLower+60

sqrtRatioAtTickLower  = getSqrtRatioAtTick(tickLower)
print(F' pLow: {sqrtRatioAtTickLower}')

# Generate a range of tickHigher values
tickHigherRange = np.linspace(MIN, MAX , 100)

# Calculate L for each tickHigher value
L_values = [calculateL(x, tickLower, t) for t in tickHigherRange]

# Plotting
plt.plot(tickHigherRange, L_values, label='L vs tickHigher')
plt.xlabel('tickHigher')
plt.ylabel('L')
plt.title('L as a function of tickHigher')
plt.legend()
plt.show()
