// An NFT Contract
// Where the tokenURI can be one of 3 different dogs
// Randomly selected

// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "node_modules/@chainlink/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
import "node_modules/@openzeppelin/contracts/utils/Strings.sol";
import "../interfaces/ICoordinator.sol";


contract Request {
    ICoordinator internal immutable COORDINATOR;
    LinkTokenInterface internal immutable LINK;
    address private immutable vrfCoordinator;
    uint64 public mySubId;

    using Strings for uint256;
    uint256 public tokenCounter;
    bytes32 public keyhash;
    uint256 public fee;

    mapping(address => mapping(uint64 => uint64)) /* consumer */ /* subId */ /* nonce */
    private s_consumers;

    constructor(address _vrfCoordinator, address _linkToken, bytes32 _keyhash, uint256 _fee) public 

    {
        tokenCounter = 0;
        keyhash = _keyhash;
        vrfCoordinator = _vrfCoordinator;
        fee = _fee;
        COORDINATOR = ICoordinator(_vrfCoordinator);
        LINK = LinkTokenInterface(_linkToken);
    }

//======================================================================
//====================== MY VRFConsumerBase funcs ======================

    receive() external payable {}
    fallback() external payable {}
    //function deposit() public payable {}

    function LINKBalance(address QueryAddress) public view returns (uint256 Balance_){
      Balance_ = LINK.balanceOf(QueryAddress);
    }

//=======================================================================
//========================== COORDINATOR FUNCS  =========================
//=======================================================================
  function formWords(uint32 numWords, uint256 randomness) public view returns (uint256[] memory){
      uint256[] memory randomWords = new uint256[](numWords);
      for (uint256 i = 0; i < numWords; i++) {
        randomWords[i] = uint256(keccak256(abi.encode(randomness, i)));
      }
      return randomWords;
  }
  // replicates function in VRFCoordintorV2.sol to compute requestId and seed.
  function computeReqId(
    bytes32 keyHash,
    address sender,
    uint64 subId,
    uint64 nonce
  ) public view returns (uint256, uint256) {
    uint256 preSeed = uint256(keccak256(abi.encode(keyHash, sender, subId, nonce)));
    return (uint256(keccak256(abi.encode(keyHash, preSeed))), preSeed);
  }
  // create subscription
  function createSub() public  returns(uint64){
    return COORDINATOR.createSubscription();
  }
  // fund subscription
  function fundSubscription(uint64 subId, uint256 amount) external {
    LINK.transferAndCall(vrfCoordinator, amount, abi.encode(subId)); 
  }

  // returns latest subId from coordinator. if executed immediately after subscription is created it will return
  // your subId. CreateSub returns the subId, b
  function getSubId() public view returns (uint64){
    return COORDINATOR.getCurrentSubId();
  }

  // set my subId so it can be retrieved by multiple scripts.
  function setMySubId(uint64 subId_) external {
    mySubId = subId_;
  }
  // retrieve my subId
  function getMySubId() external view returns (uint256){
    return mySubId;
  }
  // get subscription info
  function getSub(uint64 subId) external view returns (
      uint96 balance,
      uint64 reqCount,
      address owner,
      address[] memory consumers
    ){
      return COORDINATOR.getSubscription( subId);
    }
  // add consumer to subscription
  function addConsumer_(uint64 subId, address consumer) external{
    COORDINATOR.addConsumer( subId,  consumer);
    setConsumerNonce( consumer,  subId, 1) ;
  }
  // get Coordinator contract configuration
  function getConfig_()
    external
    view
    returns (
      uint16 minimumRequestConfirmations,
      uint32 maxGasLimit,
      uint32 stalenessSeconds,
      uint32 gasAfterPaymentCalculation
    ){
      return COORDINATOR.getConfig();
    }
  // request random words
  function CoordinatedRequest(
                bytes32 keyHash,
                uint64 subId,
                uint16 requestConfirmations,
                uint32 callbackGasLimit,
                uint32 numWords,
                address consumer) public returns (uint256 requestID){ 
                  requestID = COORDINATOR.requestRandomWords(
                                keyHash,
                                subId,
                                requestConfirmations,
                                callbackGasLimit,
                                numWords);
                  uint64 nonce_ = getConsumerNonce( consumer,  subId);
                  setConsumerNonce( consumer,  subId, nonce_ + 1);

  }

    function getConsumerNonce(address consumer, uint64 subId) public view returns (uint64 nonce_){
      nonce_ = s_consumers[consumer][subId];
    }
    //setConsumerNonce( consumer,  subId, 1) ;
    function setConsumerNonce(address consumer, uint64 subId, uint64 nonce_) public {
      s_consumers[consumer][subId] = nonce_;
    }
//========================================================================
//========================================================================
//========================================================================


}
