// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.5.0;
pragma abicoder v2;

import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Factory.sol';
import '@uniswap/v3-core/contracts/interfaces/IUniswapV3Pool.sol';
import '@uniswap/v3-core/contracts/interfaces/IERC20Minimal.sol';

interface IV3Pool is IUniswapV3Pool{}
interface IV3Factory is IUniswapV3Factory{}
interface IERC20Min is IERC20Minimal{
    function symbol() external view returns (string memory);
}


