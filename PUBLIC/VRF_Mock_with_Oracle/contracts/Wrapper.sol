// SPDX-License-Identifier: MIT
pragma solidity ^0.8.6;
import "node_modules/@chainlink/contracts/src/v0.8/VRFV2Wrapper.sol";



contract Wrapper is VRFV2Wrapper{  
  mapping(uint256 => bytes32) public blokHashes; /*blockNum --> blockHash*/
  constructor(
    address _link,
    address _linkEthFeed, 
    address _coordinator
  )VRFV2Wrapper(_link, _linkEthFeed, _coordinator){}

    function getSender() public view returns(address Sender_){
      Sender_ = msg.sender;
    }

    function requestWords(
      bytes32 _keyHash,
      uint64 _subId,
      uint16 _requestConfirmations,
      uint32 _callbackGasLimit,
      uint32 _numWords) external  returns (uint256 requestId) {
        requestId = COORDINATOR.requestRandomWords(
          _keyHash,
          _subId,
          _requestConfirmations,
          _callbackGasLimit,
          _numWords
        );
  }


}
