// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;
import "node_modules/@chainlink/contracts/src/v0.8/interfaces/ERC677ReceiverInterface.sol";
contract LinkCoordinator {
    ERC677ReceiverInterface public immutable COORDINATOR;
  constructor(address _coordinator){COORDINATOR = ERC677ReceiverInterface(_coordinator);}

    function onTokenTransfer(
      uint256 amount,
      bytes calldata data) external {
        COORDINATOR.onTokenTransfer(
            address(this),
            amount,
            data); 
      }


    function encodeSubId(uint64 SubId) public pure returns (bytes memory encodedSubId){
        encodedSubId = abi.encode(SubId);
    }
    function decodeMEMORY(bytes memory encodedSubId) public pure returns (uint64 subId){
        subId = abi.decode(encodedSubId, (uint64));
    }


    function decodeCALLDATA(bytes calldata encodedSubId) public pure returns (uint64 subId){
        subId = abi.decode(encodedSubId, (uint64));
    }




}

