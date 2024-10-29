// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.7.5;
pragma abicoder v2;

import '@uniswap/v3-periphery/contracts/interfaces/INonfungiblePositionManager.sol';
import '@openzeppelin/contracts/token/ERC20/IERC20.sol';
import '@v3PeripheryMOCKS/interfaces/MIERC20.sol';

interface NFTmanager is INonfungiblePositionManager{}


interface AggregatorV3Interface {

  function decimals()
    external
    view
    returns (
      uint8
    );

  function description()
    external
    view
    returns (
      string memory
    );

  function version()
    external
    view
    returns (
      uint256
    );

  // getRoundData and latestRoundData should both raise "No data present"
  // if they do not have data to report, instead of returning unset values
  // which could be misinterpreted as actual reported values.
  function getRoundData(
    uint80 _roundId
  )
    external
    view
    returns (
      uint80 roundId,
      int256 answer,
      uint256 startedAt,
      uint256 updatedAt,
      uint80 answeredInRound
    );

  function latestRoundData()
    external
    view
    returns (
      uint80 roundId,
      int256 answer,
      uint256 startedAt,
      uint256 updatedAt,
      uint80 answeredInRound
    );
}

interface myERC20 is IERC20{
  function mint(uint256 amount_) external; // change to external in contract !!
  function symbol() external view returns (string memory); 
  function transferFromEmit(address sender, address recipient, uint256 amount) external returns (bool);

  event transferFromParams(
      address Sender, 
      address Recipient, 
      address msgSender, 
      uint256 currentAllowance,
      uint256 requestedAmount);
}
