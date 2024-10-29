// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.7.5;

import '@v3PeripheryMOCKS/libraries/MTransferHelper.sol';

import '@openzeppelin/contracts/token/ERC20/IERC20.sol';
import '@uniswap/v3-periphery/contracts/interfaces/IPeripheryPayments.sol';
import '@uniswap/v3-periphery/contracts/interfaces/external/IWETH9.sol';
//  [TransferHelper MOCKED]
import '@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol';

abstract contract MPeripheryPayments is IPeripheryPayments {

    address public immutable  WETH9;

    constructor(address _WETH9) {WETH9 = _WETH9;
    }

    receive() external payable {
        require(msg.sender == WETH9, 'Not WETH9');
    }

    /// @inheritdoc IPeripheryPayments
    function unwrapWETH9(uint256 amountMinimum, address recipient) public payable override {
        uint256 balanceWETH9 = IWETH9(WETH9).balanceOf(address(this));
        require(balanceWETH9 >= amountMinimum, 'Insufficient WETH9');

        if (balanceWETH9 > 0) {
            IWETH9(WETH9).withdraw(balanceWETH9);
            MTransferHelper.safeTransferETH(recipient, balanceWETH9);
        }
    }

    /// @inheritdoc IPeripheryPayments
    function sweepToken(
        address token,
        uint256 amountMinimum,
        address recipient
    ) public payable override {
        uint256 balanceToken = IERC20(token).balanceOf(address(this));
        require(balanceToken >= amountMinimum, 'Insufficient token');

        if (balanceToken > 0) {
            MTransferHelper.safeTransfer(token, recipient, balanceToken);
        }
    }

    /// @inheritdoc IPeripheryPayments
    function refundETH() external payable override {
        if (address(this).balance > 0) MTransferHelper.safeTransferETH(msg.sender, address(this).balance);
    }

    function pay(
        address token,
        address payer,
        address recipient,
        uint256 value,
        int8 option
    ) internal {
        if (option==50){
            MTransferHelper.safeTransferFromEmit(token, payer, recipient, value);
        }else{
            if (token == WETH9 && address(this).balance >= value) {
                // pay with WETH9
                IWETH9(WETH9).deposit{value: value}(); // wrap only what is needed to pay
                IWETH9(WETH9).transfer(recipient, value);
            } else if (payer == address(this)) {
                // pay with tokens already in the contract (for the exact input multihop case)
                MTransferHelper.safeTransfer(token, recipient, value);
            } else {
                // pull payment
                MTransferHelper.safeTransferFrom(token, payer, recipient, value);
            }
        }

    }

}
