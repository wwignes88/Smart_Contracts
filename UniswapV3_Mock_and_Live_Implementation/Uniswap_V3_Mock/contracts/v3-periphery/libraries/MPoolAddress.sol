// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;

/* this, together with hashPoolCreationCode.sol,
   is a mock of the PoolAddress.sol contract in the v3-periphery.
   When we alter the pool contract (e.g. in a mock) both its creation code 
   and the hash of the creation code gets altered. The uniswap protocol relies 
   on being able to replicate deployed pool addresses in a deterministic fashion,
   and for this the value of POOL_INIT_CODE_HASH is used.

   so, because we've altered the pool contract (or so we are able to alter it 
   for troubleshooting/ mocking purposes) we need a way to recalculate the value
   of POOL_INIT_CODE_HASH, then use this to deterministically compute the address
   of our deployed pools.

   *  requires that the UniswapV3Pool imported is the same as it was when this library was deployed.
   ** first deploy hashPoolCreationCode and use the function hashPoolCode to get the value of 
      POOL_INIT_CODE_HASH, updated this value here in this library, THEN deploy this library which will
      be used by the NonfungiblePositionManager and LiquidityManagement mock contracts.
   */

import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3PoolII.sol';

library MPoolAddress { 

    // update me before deployment!!
    bytes32 internal constant _POOL_INIT_CODE_HASHI  = 0x43cc9a8581352cd7e6a018f01072ab4c3778888d7514dbb29f920676b000ba7b;
    bytes32 internal constant _POOL_INIT_CODE_HASHII = 0xba2d6c0cd849096498b9331d232b124c363d52be5e579399863c368c093a42d9;

    /// @notice The identifying key of the pool
    struct PoolKey {
        address token0;
        address token1;
        uint24 fee;
    }
    function getPoolKey(
        address tokenA,
        address tokenB,
        uint24 fee
     ) internal pure returns (PoolKey memory) {
        if (tokenA > tokenB) (tokenA, tokenB) = (tokenB, tokenA);
        return PoolKey({token0: tokenA, token1: tokenB, fee: fee});
    }


    function computePoolAddress(address factory, 
                            address tokenA,
                            address tokenB,
                            uint24 fee) 
                            public pure returns (address _pool) 
    {
        if (tokenA > tokenB) (tokenA, tokenB) = (tokenB, tokenA);
        // (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        //require(tokenA < tokenB, "token1 > token0");
        //---------------- calculate pool address
            bytes32 pool_hash = keccak256(
            abi.encodePacked(
                hex'ff',
                factory,
                keccak256(abi.encode(tokenA, tokenB, fee)),
                _POOL_INIT_CODE_HASHI
            )
            );
            bytes20 addressBytes = bytes20(pool_hash << (256 - 160));
            _pool = address(uint160(addressBytes));
    }

    function computePoolAddressII(address factoryII, 
                            address tokenA,
                            address tokenB,
                            uint24 fee) 
                            public pure returns (address _poolII) 
    {
        if (tokenA > tokenB) (tokenA, tokenB) = (tokenB, tokenA);
        // (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        //require(tokenA < tokenB, "token1 > token0");
        //---------------- calculate pool address
            bytes32 pool_hashII = keccak256(
            abi.encodePacked(
                hex'ff',
                factoryII,
                keccak256(abi.encode(tokenA, tokenB, fee)),
                _POOL_INIT_CODE_HASHII
            )
            );
            bytes20 addressBytes = bytes20(pool_hashII << (256 - 160));
            _poolII = address(uint160(addressBytes));
    }

    //===============================================


    function get_pools(address factory, 
                        address factoryII,
                        address token0,
                        address token1,
                        uint24 fee) public pure  returns (
                            IUniswapV3Pool pool,
                            IUniswapV3PoolII poolII){ 
        address poolAddress = computePoolAddress(factory,
                                                token0,
                                                token1,
                                                fee);
        pool = IUniswapV3Pool(poolAddress);

        address poolIIAddress = computePoolAddressII(factoryII,
                                                token0,
                                                token1,
                                                fee);
        poolII = IUniswapV3PoolII(poolIIAddress);
    }


}



