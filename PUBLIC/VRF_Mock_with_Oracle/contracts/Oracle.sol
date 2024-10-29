// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;
import "./VRFI.sol"; 
import "./MOCK.sol"; 
import "node_modules/@chainlink/contracts/src/v0.8/ConfirmedOwner.sol";
import "node_modules/@chainlink/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
import "node_modules/@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";
import "node_modules/@chainlink/contracts/src/v0.8/VRFCoordinatorV2.sol";


contract  Oracle is ConfirmedOwner, VRFI{ 

  LinkTokenInterface public immutable LINK;
  AggregatorV3Interface public immutable LINK_ETH_FEED;
  mock2 public immutable COORDINATOR;
  //VRFCoordinatorV2 public immutable COORDINATOR;

  mapping(uint256 => bytes32) public blokHashes; /*blockNum --> blockHash*/


  constructor(
    address _link,
    address _linkEthFeed,
    address _coordinator
  ) ConfirmedOwner(address(this))  {
    LINK = LinkTokenInterface(_link);
    LINK_ETH_FEED = AggregatorV3Interface(_linkEthFeed);
    COORDINATOR = mock2(_coordinator);

    // add Oracle to subscription?
    //ExtendedVRFCoordinatorV2Interface(_coordinator).addConsumer(subId, address(this));
  }

  function OracleCashesIn(uint96 amount) external {
      COORDINATOR.oracleWithdraw(address(this),address(this), amount);
  }

  function getBlockHash(uint256 blockNum) external view returns (bytes32 blockHash) {
    blockHash = blokHashes[blockNum];
  }
  function mapBlockHash(uint256 blockNum, bytes32 _blockHash) external  {
    blokHashes[blockNum] = _blockHash;
  }

  // just because implementation is required for Oracle to inherit VRFI
  function implementVRFI() public pure returns (uint256 VRFIimplementedNum){ 
  VRFIimplementedNum = VRFI.implement() ;}


  function getSender() public view returns(address Sender_){
    Sender_ = msg.sender;
  }
}

