// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity =0.7.6;

import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';
import '@v3PeripheryMOCKS/libraries/MPoolAddress.sol';
/// @notice Provides validation for callbacks from Uniswap V3 Pools
library MCallbackValidation {
    /// @notice Returns the address of a valid Uniswap V3 Pool
    /// @param factory The contract address of the Uniswap V3 factory
    /// @param tokenA The contract address of either token0 or token1
    /// @param tokenB The contract address of the other token
    /// @param fee The fee collected upon every swap in the pool, denominated in hundredths of a bip
    /// @return pool The V3 pool contract address
    function verifyCallback(
        address factory,
        address tokenA,
        address tokenB,
        uint24 fee
    ) public view returns (IUniswapV3Pool pool) {
        return verifyCallback(factory, MPoolAddress.getPoolKey(tokenA, tokenB, fee));
    }

    /// @notice Returns the address of a valid Uniswap V3 Pool
    /// @param factory The contract address of the Uniswap V3 factory
    /// @param poolKey The identifying key of the V3 pool
    /// @return pool The V3 pool contract address
    function verifyCallback(address factory, MPoolAddress.PoolKey memory poolKey)
        internal
        view
        returns (IUniswapV3Pool pool)
    {
        pool = IUniswapV3Pool(MPoolAddress.computePoolAddress(
                                                        factory, 
                                                        poolKey.token0, 
                                                        poolKey.token1, 
                                                        poolKey.fee
                                                        ));
        require(msg.sender == address(pool), "MCallbackVal :: not pool address");
                //msg.sender = poolII = MLManager!!
    }
}
