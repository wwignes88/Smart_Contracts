// SPDX-License-Identifier: BUSL-1.1
pragma solidity 0.7.6;

import '@v3CoreMOCKS/MUniswapV3Pool.sol';
contract MUniswapFactory {
    address public  owner;
    mapping(uint24 => int24) public feeAmountTickSpacing;
    mapping(address => mapping(address => mapping(uint24 => address))) public  getPool;

    constructor() {
        owner = msg.sender;
        feeAmountTickSpacing[500]  = 10;
        feeAmountTickSpacing[3000] = 60;
    }

    struct Parameters {
        address factory;
        address token0;
        address token1;
        uint24 fee;
        int24 tickSpacing; 
    }

    Parameters public  parameters;

    function deploy(
        address factory,
        address token0,
        address token1,
        uint24 fee,
        int24 tickSpacing
    ) internal returns (address pool) {
        parameters = Parameters({factory: factory, token0: token0, token1: token1, fee: fee, tickSpacing: tickSpacing});
        pool = address(new MUniswapV3Pool{salt: keccak256(abi.encode(token0, token1, fee))}());
        delete parameters;
    }

    function createPool( 
        address tokenA,
        address tokenB,
        uint24 fee
    ) external   returns (address pool) {
        require(tokenA != tokenB);
        (address token0, address token1) = tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
        require(token0   != address(0));
        int24 tickSpacing = feeAmountTickSpacing[fee];
        require(tickSpacing != 0);
        require(getPool[token0][token1][fee] == address(0));
        pool = deploy(address(this), token0, token1, fee, tickSpacing);
        getPool[token0][token1][fee] = pool;
        // populate mapping in the reverse direction, deliberate choice to avoid the cost of comparing addresses
        getPool[token1][token0][fee] = pool;
    }


}