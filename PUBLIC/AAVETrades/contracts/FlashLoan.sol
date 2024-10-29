// SPDX-License-Identifier: agpl-3.0
pragma solidity 0.6.12;
  //import "contracts/VRFI.sol";
import { FlashLoanReceiverBase } from "contracts/FlashLoanReceiverBase.sol";
import { ILendingPool, ILendingPoolAddressesProvider, IERC20 } from "interfaces/Interfaces.sol";
import { SafeMath } from "contracts/Libraries.sol";

/** 
    !!!
    Never keep funds permanently on your FlashLoanReceiverBase contract as they could be 
    exposed to a 'griefing' attack, where the stored funds are used by an attacker.
    !!!
 */
contract MyV2FlashLoan is FlashLoanReceiverBase {

    event FlashEvent(uint256 flashEvent);

    address public owner;
    string constant private Symbol = "FLASH";
    using SafeMath for uint256;
    
    constructor(ILendingPoolAddressesProvider _addressProvider) 
    FlashLoanReceiverBase(_addressProvider) public {
        owner = msg.sender;
    }
 
    // Misc. funcs.

        function symbol() public view returns (string memory) {return Symbol;}
        //XX receive() external payable {}
        //XX fallback() external payable {}
        function deposit() public payable {}
        
        // Function to withdraw any remaining tokens back to the owner
        function withdrawToken(address tokenAddress) external onlyOwner {
            uint256 balance = IERC20(tokenAddress).balanceOf(address(this));
            IERC20(tokenAddress).transfer(owner, balance);
        }

        modifier onlyOwner() {
            require(msg.sender == owner, "Only the owner can call this function");
            _;
        }
    //=======================================================
    //========================== FLASH ======================
    //=======================================================
    function flashI(
            address[] calldata assets,
            uint256[] calldata amounts,
            uint256[] calldata premiums,
            uint256[] calldata modes,
            address onBehalfOf) public onlyOwner{

        for (uint i = 0; i < assets.length; i++) {
            uint256 amountOwing = amounts[i].add(premiums[i]); 
            IERC20(assets[i]).approve(address(LENDING_POOL), amountOwing);
        }

        address receiverAddress = address(this);
        bytes memory params = "";
        uint16 referralCode = 0;

        LENDING_POOL.flashLoan(
            receiverAddress,
            assets,
            amounts,
            modes,
            onBehalfOf,
            params,
            referralCode
        );
    }


    function executeOperation(
        address[] calldata assets,
        uint256[] calldata amounts,
        uint256[] calldata premiums,
        address initiator,
        bytes calldata params
        )
            external
            override
            returns (bool)
        {
            

            // At the end of your logic above, this contract owes
            // the flashloaned amounts + premiums.
            // Therefore ensure your contract has enough to repay
            // these amounts.

            // Approve the LendingPool contract allowance to *pull* the owed amount

            return true;
    }

}