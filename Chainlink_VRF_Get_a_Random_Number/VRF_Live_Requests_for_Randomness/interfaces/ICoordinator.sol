
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface ICoordinator {

    
    event SubscriptionFunded(uint64 indexed subId, uint256 oldBalance, uint256 newBalance);
    event RandomWordsRequested(
      bytes32 indexed keyHash,
      uint256 requestId,
      uint256 preSeed,
      uint64 indexed subId,
      uint16 minimumRequestConfirmations,
      uint32 callbackGasLimit,
      uint32 numWords,
      address indexed sender
    );
    event RandomWordsFulfilled(uint256 indexed requestId, uint256 outputSeed, uint96 payment, bool success);
    function randomnessRequest(
        bytes32 _keyHash,
        uint256 _fee,
        uint256 _seed,
        address _callbackContract,
        bytes4 _callbackFunctionId
    ) external returns (bytes32 requestId);

    function fulfillRandomness(bytes32 requestId, uint256 randomness) external;
    
    function createSubscription() external  returns (uint64) ;
    function getCurrentSubId() external view returns (uint64) ;
    function getSubscription(uint64 subId)
        external
        view
        returns (
        uint96 balance,
        uint64 reqCount,
        address owner,
        address[] memory consumers
        );

    function requestRandomWords(
        bytes32 keyHash,
        uint64 subId,
        uint16 requestConfirmations,
        uint32 callbackGasLimit,
        uint32 numWords
    ) external returns (uint256) ;

    function addConsumer(uint64 subId, address consumer) external;

  function getConfig()
    external
    view
    returns (
      uint16 minimumRequestConfirmations,
      uint32 maxGasLimit,
      uint32 stalenessSeconds,
      uint32 gasAfterPaymentCalculation
    );
    function pendingRequestExists(uint64 subId) external view returns (bool);
    function requestRandomnessII( address vrfCoordinator, uint256 _fee)  external;

//config: (3, 2500000, 86400, 33285)


  function getFeeConfig()
    external
    view
    returns (
      uint32 fulfillmentFlatFeeLinkPPMTier1,
      uint32 fulfillmentFlatFeeLinkPPMTier2,
      uint32 fulfillmentFlatFeeLinkPPMTier3,
      uint32 fulfillmentFlatFeeLinkPPMTier4,
      uint32 fulfillmentFlatFeeLinkPPMTier5,
      uint24 reqsForTier2,
      uint24 reqsForTier3,
      uint24 reqsForTier4,
      uint24 reqsForTier5
    );

      
  
  
        
}




