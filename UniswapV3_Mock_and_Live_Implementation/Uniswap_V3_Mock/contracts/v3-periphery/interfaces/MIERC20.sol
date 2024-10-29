// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.6.0;

import '@openzeppelin/contracts/token/ERC20/IERC20.sol';

interface MIERC20 is IERC20{
    function transferFromEmit(address sender, address recipient, uint256 amount) external returns (bool);
}