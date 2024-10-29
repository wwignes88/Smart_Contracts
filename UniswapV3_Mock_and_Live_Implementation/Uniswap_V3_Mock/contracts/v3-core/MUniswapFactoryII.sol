// SPDX-License-Identifier: BUSL-1.1
pragma solidity 0.7.6;

import "@v3CoreMOCKS/MUniswapV3PoolII.sol";
contract MUniswapFactoryII {
    address public  ownerII;
    mapping(uint24 => int24) public feeAmountTickSpacingII;
    mapping(address => mapping(address => mapping(uint24 => address))) public  getPoolII;

    constructor() {
        ownerII = msg.sender;
        feeAmountTickSpacingII[500]  = 10;
        feeAmountTickSpacingII[3000] = 60;
    }

    struct ParametersII {
        address factoryII;
        address token0II;
        address token1II;
        uint24 feeII;
        int24 tickSpacingII; 
    }


    ParametersII public  parametersII;

    function deployII(
        address _factoryII,
        address token0,
        address token1,
        uint24 fee,
        int24 tickSpacing
    ) internal returns (address pool) {
        parametersII = ParametersII({factoryII: _factoryII, token0II: token0, token1II: token1, feeII: fee, tickSpacingII: tickSpacing});
        pool = address(new MUniswapV3PoolII{salt: keccak256(abi.encode(token0, token1, fee))}());
        delete parametersII;
    }

    function createPoolII( 
        address tokenA,
        address tokenB,
        uint24 fee
    ) external   returns (address pool) {
        require(tokenA != tokenB);
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        require(token0   != address(0));
        int24 tickSpacing = feeAmountTickSpacingII[fee];
        require(tickSpacing != 0);
        require(getPoolII[token0][token1][fee] == address(0));
        pool = deployII(address(this), token0, token1, fee, tickSpacing);
        getPoolII[token0][token1][fee] = pool;
        // populate mapping in the reverse direction, deliberate choice to avoid the cost of comparing addresses
        getPoolII[token1][token0][fee] = pool;
    }


}