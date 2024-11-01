// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.6.12;
 
//  import "contracts/VRFI.sol";
import {IFlashLoanReceiver, ILendingPoolAddressesProvider, ILendingPool, IERC20  } from "interfaces/Interfaces.sol";
import { SafeERC20, SafeMath } from "contracts/Libraries.sol";
 
abstract contract FlashLoanReceiverBase is IFlashLoanReceiver {
  using SafeERC20 for IERC20;
  using SafeMath for uint256;

  ILendingPoolAddressesProvider public immutable  ADDRESSES_PROVIDER;
  ILendingPool public immutable  LENDING_POOL;

  constructor(ILendingPoolAddressesProvider provider) public {
    ADDRESSES_PROVIDER = provider;
    LENDING_POOL = ILendingPool(provider.getLendingPool());
  }
}