// SPDX-License-Identifier: MIT 
// A mock for testing code that relies on VRFCoordinatorV2.
pragma solidity ^0.8.4; 
// IMPORT
  import "contracts/VRFI.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/interfaces/TypeAndVersionInterface.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/tests/MockV3Aggregator.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/interfaces/ERC677ReceiverInterface.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/interfaces/VRFCoordinatorV2Interface.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/interfaces/BlockhashStoreInterface.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/VRFConsumerBaseV2.sol";
  import "node_modules/@chainlink/contracts/src/v0.8/ConfirmedOwner.sol";
contract mock3 is MockV3Aggregator {
    // _DECIMALS=18 and _INITIALANSWER=3000000000000000
    constructor(uint8 _decimals, int256 _initialAnswer) 
    MockV3Aggregator(decimals, latestAnswer){} 
}

contract mock2 is 
  VRFI,
  ConfirmedOwner,
  TypeAndVersionInterface,
  VRFCoordinatorV2Interface,
  ERC677ReceiverInterface
 {
  //PERIPHERIAL   CONTRACTS:
    AggregatorV3Interface public immutable LINK_ETH_FEED;
    LinkTokenInterface public immutable LINK;
    BlockhashStoreInterface public  BLOCKHASH_STORE;
  // 
  //Declarations
    //constants:
      bytes32[] private s_provingKeyHashes;
      int256 private s_fallbackWeiPerUnitLink; 
      Config private s_config;       
      FeeConfig private s_feeConfig; 
      uint256 private constant GAS_FOR_CALL_EXACT_CHECK = 5000;
      uint96 public immutable BASE_FEE;
      uint96 public immutable GAS_PRICE_LINK;
      uint16 public immutable MAX_CONSUMERS = 100;
      uint96 s_totalBalance;
      uint64 s_currentSubId;
      uint16 public constant MAX_REQUEST_CONFIRMATIONS = 200;
      uint32 public constant MAX_NUM_WORDS = 500;
      uint256 public _commitId = 0;
      address public linkCoordinator;
    //errors & events:
      error PaymentTooLarge();
      error PendingRequestExists();
      error OnlyCallableFromLink();
      error NoCorrespondingRequest();
      error GasLimitTooBig(uint32 have, uint32 want);
      error InvalidSubscription();
      error InvalidLinkWeiPrice(int256 linkWei);
      error InsufficientBalance();
      error InvalidCalldata();
      error MustBeSubOwner(address owner);
      error MustBeRequestedOwner(address proposedOwner);
      error TooManyConsumers();
      error InvalidConsumer(uint64 subId, address consumer);
      error NumWordsTooBig(uint32 have, uint32 want);
      error InvalidRandomWords();
      error ProvingKeyAlreadyRegistered(string msg, bytes32 keyHash);
      error NoSuchProvingKey(string msg, bytes32 keyHash);
      error IncorrectCommitment();
      error Reentrant();
      error aSTR(string integerInput);
      
      event ConfigSet( 
        uint16 minimumRequestConfirmations,
        uint32 maxGasLimit,
        uint32 stalenessSeconds,
        uint32 gasAfterPaymentCalculation,
        int256 fallbackWeiPerUnitLink,
        FeeConfig feeConfig
      ); 
      event RandomWordsFulfilled(uint256 indexed requestId, uint256 outputSeed, uint96 payment, bool success);
      event SubscriptionCreated(uint64 indexed subId, address owner);
      event SubscriptionFunded(uint64 indexed subId, uint256 oldBalance, uint256 newBalance);
      event SubscriptionCanceled(uint64 indexed subId, address to, uint256 amount);
      event SubscriptionConsumerAdded(uint64 indexed subId, address consumer);
      event SubscriptionConsumerRemoved(uint64 indexed subId, address consumer);
      event ProvingKeyRegistered(bytes32 keyHash, address indexed oracle);
      event ProvingKeyDeregistered(bytes32 keyHash, address indexed oracle);
      event SubscriptionOwnerTransferRequested(uint64 indexed subId, address from, address to);
      event SubscriptionOwnerTransferred(uint64 indexed subId, address from, address to);
      event FundsRecovered(address to, uint256 amount);
      error BalanceInvariantViolated(uint256 internalBalance, uint256 externalBalance); // Should never happen
      error InvalidRequestConfirmations(uint16 have, uint16 min, uint16 max);
      event eva0(uint A);


      event request_I(
        bytes32 indexed keyHash,
        uint256 requestId,
        uint256 preSeed,
        uint64 indexed subId
        );
      event request_II(
        uint16 minimumRequestConfirmations,
        uint32 callbackGasLimit,
        uint32 numWords,
        address indexed sender
        );


    //structs
      struct Subscription {
        // There are only 1e9*1e18 = 1e27 juels in existence, so the balance can fit in uint96 (2^96 ~ 7e28)
        uint96 balance; // Common link balance used for all consumer requests.
        uint64 reqCount; // For fee tiers
      }
      struct SubscriptionConfig {
        address owner; // Owner can fund/withdraw/cancel the sub.
        address requestedOwner; 
        address[] consumers;
      }  

      struct RequestCommitment {
        uint256 blockNum;
        uint64 subId;
        uint32 callbackGasLimit;
        uint32 numWords;
        address sender;}


      struct Config {
        uint16 minimumRequestConfirmations;
        uint32 maxGasLimit;
        bool reentrancyLock;
        uint32 stalenessSeconds;
        uint32 gasAfterPaymentCalculation;
      } 
      struct FeeConfig {
        uint32 fulfillmentFlatFeeLinkPPMTier1;
        uint32 fulfillmentFlatFeeLinkPPMTier2;
        uint32 fulfillmentFlatFeeLinkPPMTier3;
        uint32 fulfillmentFlatFeeLinkPPMTier4;
        uint32 fulfillmentFlatFeeLinkPPMTier5;
        uint24 reqsForTier2;
        uint24 reqsForTier3;
        uint24 reqsForTier4;
        uint24 reqsForTier5;
      } 



    //mappings
      mapping(uint256 => Proof) /* requestId --> Proof */ public m_proofs;
      mapping(uint64 => Subscription) s_subscriptions; /* subId */ /* subscription */
      mapping(uint64 => SubscriptionConfig) private s_subscriptionConfigs;
      mapping(address => mapping(uint64 => uint64)) /* consumer */ /* subId */ /* nonce */
        private s_consumers;
      mapping(uint256 => bytes) /* commitId */ /* commitment */ public encoded_s_requestCommitments;
      mapping(uint256 => bytes32) /* commitId */ /* commitment */ public s_requestCommitments;
      mapping(uint256 => RequestCommitment) /* commitId */ /* commitment */ public m_requestCommitments;
      mapping(address => uint96) /* oracle */ /* LINK balance */ private s_withdrawableTokens;
      mapping(bytes32 => address) /* keyHash */ /* oracle */ private s_provingKeys;



  //                     ==== CONSTRUCTOR ===
    constructor(
      uint96  _baseFee, 
      uint96  _gasPriceLink, 
      address _link,
      address _linkEthFeed) ConfirmedOwner(msg.sender) {
      LINK           = LinkTokenInterface(_link);
      BASE_FEE       = _baseFee;
      GAS_PRICE_LINK = _gasPriceLink;
	    LINK_ETH_FEED = AggregatorV3Interface(_linkEthFeed);
      }
  //

  //REQUEST WORD/ FULFILL
    // request
      function requestRandomWords(
        bytes32 _keyHash,
        uint64 _subId,
        uint16 _requestConfirmations,
        uint32 _callbackGasLimit,
        uint32 _numWords) external  onlyValidConsumer(_subId, msg.sender)  returns (uint256 requestId) {

        //      **** REVERT CHECKS ****
        uint64  currentNonce = s_consumers[msg.sender][_subId];
        uint64  nonce        = currentNonce + 1;
        s_consumers[msg.sender][_subId] = nonce;
        (uint256 _requestId, uint256 _preSeed) = computeRequestId(_keyHash, msg.sender, _subId, nonce);



        // store request commitments
        m_requestCommitments[_requestId] = RequestCommitment({
          blockNum        : block.number,
          subId           : _subId,
          callbackGasLimit:_callbackGasLimit,
          numWords        :_numWords,
          sender          : msg.sender
        });
        s_requestCommitments[_requestId]  =  keccak256(
          abi.encode(_requestId, block.number, _subId, _callbackGasLimit, _numWords, msg.sender));

        emit request_I(
        _keyHash,              
        _requestId,
        _preSeed,
        _subId               
        );
        emit request_II(
        _requestConfirmations, 
        _callbackGasLimit,      
        _numWords,              
        msg.sender
        );

      }


    // fillment
      function fulfillRandomWords(Proof memory proof, RequestCommitment memory rc) external returns (uint96) {
        uint256 startGas = gasleft();
        (bytes32 keyHash, uint256 requestId, uint256 randomness) = getRandomnessFromProof(proof, rc);
        uint256[] memory randomWords = new uint256[](rc.numWords);
        for (uint256 i = 0; i < rc.numWords; i++) {
          randomWords[i] = uint256(keccak256(abi.encode(randomness, i))); }

        delete s_requestCommitments[requestId];
        VRFConsumerBaseV2 v;
        bytes memory resp = abi.encodeWithSelector(v.rawFulfillRandomWords.selector, requestId, randomWords);
        s_config.reentrancyLock = true;
        bool success = callWithExactGas(rc.callbackGasLimit, rc.sender, resp);
        s_config.reentrancyLock = false;
        uint64 reqCount = s_subscriptions[rc.subId].reqCount;
        s_subscriptions[rc.subId].reqCount += 1;
        uint96 payment = calculatePaymentAmount(
          startGas,
          s_config.gasAfterPaymentCalculation,
          getFeeTier(reqCount),
          tx.gasprice);
        if (s_subscriptions[rc.subId].balance < payment) {
          revert ("fulfillRandomWords: Insufficient Balance");}
        s_subscriptions[rc.subId].balance -= payment;
        s_withdrawableTokens[s_provingKeys[keyHash]] += payment;
        emit RandomWordsFulfilled(requestId, randomness, payment, success);
        return (payment);}


      function callWithExactGas(uint256 gasAmount, address target, bytes memory data) public returns (bool success) {
        // solhint-disable-next-line no-inline-assembly
        assembly {
          let g := gas()
          if lt(g, GAS_FOR_CALL_EXACT_CHECK) {
           revert(0, 0)}
          g := sub(g, GAS_FOR_CALL_EXACT_CHECK)
          if iszero(gt(sub(g, div(g, 64)), gasAmount)) {
            revert(0, 0)}
          if iszero(extcodesize(target)) {
            revert(0, 0)}
          success := call(gasAmount, target, 0, add(data, 0x20), mload(data), 0, 0)
        }
        return success;
      }

    //**** my funcs */
      function GetBlockHaashII(RequestCommitment memory rc) external view returns (bytes32 blockHash){ 
        blockHash = blockhash(rc.blockNum);
      }

      function GetBlockHaash(RequestCommitment memory rc) external view returns (bytes32 _blockHash){ 
        _blockHash = blockhash(rc.blockNum);
        if (_blockHash == bytes32(0)) {
          _blockHash = BLOCKHASH_STORE.getBlockhash(rc.blockNum);
        }
      }

      function getHashedCommit(uint256 requestId) external view returns (bytes32 commitment){
        commitment = s_requestCommitments[requestId];
      }
      function checkProvingKeyRegistration(Proof memory proof) public view returns(address oracle){
        bytes32 keyHash = proof.keyHash;
        oracle = s_provingKeys[keyHash];
      }

      function getRandomnessFromProof(Proof memory proof, RequestCommitment memory rc)
        public
        view
        returns (
          bytes32 keyHash,
          uint256 requestId,
          uint256 randomness
        )
      {
        keyHash = proof.keyHash;
        // Only registered proving keys are permitted.
        address oracle = s_provingKeys[keyHash];
        if (oracle == address(0)) {
          revert ("\ngetRandomnessFromProof: oracle == 0\n");
        }
        /*
        'UNUSED keyHash' is, as implied, not used. See READMEFILE; 
        without  knowing, via mathematics or by some other means, the pk value which,
        when hashed, produces a keyHash which matches that calculated/ emitted in the 
        request, we have no means of mocking the replication of the keyHash by the 
        Oracle. So we instead simply feed the keyHash value which was calculated
        in requestRandomWords, use it to replicate the requestId, and that is 
        all we need it for.
        */
        //UNUSED keyHash = hashOfKey(proof.pk);
        requestId = uint256(keccak256(abi.encode(keyHash, proof.seed)));
        bytes32 commitment = s_requestCommitments[requestId];
        if (commitment == 0) {
          revert ("getRandomnessFromProof: commitment = 0");
        }
        if (
          commitment != keccak256(abi.encode(requestId, rc.blockNum, rc.subId, rc.callbackGasLimit, rc.numWords, rc.sender))
        ) {
          revert ("getRandomnessFromProof: commitment != kkeccack...");
        }

        bytes32 blockHash = blockhash(rc.blockNum);
        if (blockHash == bytes32(0)) {
          blockHash = BLOCKHASH_STORE.getBlockhash(rc.blockNum);
          if (blockHash == bytes32(0)) {
            revert ("getRandomnessFromProof: blockHash == 0");
          }
        }

        randomness = 13;
      }


  //
  //MANAGE SUBSCRIPTIONS 
    function getCurrentSubId() external view returns (uint64) {
      return s_currentSubId;
    }

    function createSubscription() external returns (uint64) { //nonreentrant
      s_currentSubId += 1;
      address[] memory consumers = new address[](0);
      s_subscriptions[s_currentSubId] = Subscription({balance: 0, reqCount: 0});
      s_subscriptionConfigs[s_currentSubId] = SubscriptionConfig({
        owner: msg.sender,
        requestedOwner: address(0),
        consumers: consumers
      });
      emit SubscriptionCreated(s_currentSubId, msg.sender);
      return s_currentSubId;
    }
    
    function fundSubscription(uint64 _subId, uint96 _amount) public {
      if (s_subscriptionConfigs[_subId].owner == address(0)) {
        revert ("sub owner == {0}");
      }
      uint96 oldBalance = s_subscriptions[_subId].balance;
      s_subscriptions[_subId].balance += _amount;
      emit SubscriptionFunded(_subId, oldBalance, oldBalance + _amount);
    }

 
    function addConsumer(uint64 _subId, address _consumer) external {
      if (s_subscriptionConfigs[_subId].consumers.length == MAX_CONSUMERS) {
        revert ("addConsumer: too many consumers");
      }
      if (s_consumers[_consumer][_subId] != 0) {
        // Idempotence - do nothing if already added.
        // Ensures uniqueness in s_subscriptions[subId].consumers.
        return;
      }
      // Initialize the nonce to 1, indicating the consumer is allocated.
      // Initialize the nonce to 1, indicating the consumer is allocated.
      s_consumers[_consumer][_subId] = 1;
      s_subscriptionConfigs[_subId].consumers.push(_consumer);

      emit SubscriptionConsumerAdded(_subId, _consumer);
    }
    function consumerIsAdded(uint64 _subId, address _consumer) public view returns (bool) {
      address[] memory consumers = s_subscriptionConfigs[_subId].consumers ;
      for (uint256 i = 0; i < consumers.length; i++) {
        if (consumers[i] == _consumer) {
          return true;
        }
      }
      return false;
    }

    modifier onlyValidConsumer(uint64 _subId, address _consumer) {
      if (!consumerIsAdded(_subId, _consumer)) {
        revert ("addConsumer: consumer not added");
      }
      _;
    }


    function getSubscription(uint64 _subId)
      external
      view
      returns (
        uint96 balance,
        uint64 reqCount,
        address owner,
        address[] memory consumers
      )
    {
      if (s_subscriptionConfigs[_subId].owner == address(0)) {
        revert ("sub owner = {0}");
      }
      return (
        s_subscriptions[_subId].balance,
        s_subscriptions[_subId].reqCount,
        s_subscriptionConfigs[_subId].owner,
        s_subscriptionConfigs[_subId].consumers
      );
    }

      function requestSubscriptionOwnerTransfer(uint64 subId, address newOwner)
        external
        override
        onlySubOwner(subId)
        nonReentrant
      {
        // Proposing to address(0) would never be claimable so don't need to check.
        if (s_subscriptionConfigs[subId].requestedOwner != newOwner) {
          s_subscriptionConfigs[subId].requestedOwner = newOwner;
          emit SubscriptionOwnerTransferRequested(subId, msg.sender, newOwner);
        }
      }


      function acceptSubscriptionOwnerTransfer(uint64 subId) external override nonReentrant {
        if (s_subscriptionConfigs[subId].owner == address(0)) {
          revert("acceptSubOwner: sub owner = {0}");
        }
        if (s_subscriptionConfigs[subId].requestedOwner != msg.sender) {
          revert("acceptSubOwner: sub owner != sender");
        }
        address oldOwner = s_subscriptionConfigs[subId].owner;
        s_subscriptionConfigs[subId].owner = msg.sender;
        s_subscriptionConfigs[subId].requestedOwner = address(0);
        emit SubscriptionOwnerTransferred(subId, oldOwner, msg.sender);
      }


      function removeConsumer(uint64 subId, address consumer) external override onlySubOwner(subId) nonReentrant {
        if (s_consumers[consumer][subId] == 0) {
          revert("removeConsumer: invalid Consumer (nonce = 0)");
        }
        // Note bounded by MAX_CONSUMERS
        address[] memory consumers = s_subscriptionConfigs[subId].consumers;
        uint256 lastConsumerIndex = consumers.length - 1;
        for (uint256 i = 0; i < consumers.length; i++) {
          if (consumers[i] == consumer) {
            address last = consumers[lastConsumerIndex];
            // Storage write to preserve last element
            s_subscriptionConfigs[subId].consumers[i] = last;
            // Storage remove last element
            s_subscriptionConfigs[subId].consumers.pop();
            break;
          }
        }
        delete s_consumers[consumer][subId];
        emit SubscriptionConsumerRemoved(subId, consumer);
      }

      function cancelSubscription(uint64 subId, address to) external override onlySubOwner(subId) nonReentrant {
        if (pendingRequestExists(subId)) {
          revert ("cancelSubscription: PendingRequestExists");
        }
        cancelSubscriptionHelper(subId, to);}

      function cancelSubscriptionHelper(uint64 subId, address to) private nonReentrant {
        SubscriptionConfig memory subConfig = s_subscriptionConfigs[subId];
        Subscription memory sub = s_subscriptions[subId];
        uint96 balance = sub.balance;
        // Note bounded by MAX_CONSUMERS;
        // If no consumers, does nothing.
        for (uint256 i = 0; i < subConfig.consumers.length; i++) {
          delete s_consumers[subConfig.consumers[i]][subId];
        }
        delete s_subscriptionConfigs[subId];
        delete s_subscriptions[subId];
        s_totalBalance -= balance;
        if (!LINK.transfer(to, uint256(balance))) {
          revert ("cancelSubscriptionHelper: insufficient balance");
        }
        emit SubscriptionCanceled(subId, to, balance);}

      function pendingRequestExists(uint64 subId) public view override returns (bool) {
        SubscriptionConfig memory subConfig = s_subscriptionConfigs[subId];
        for (uint256 i = 0; i < subConfig.consumers.length; i++) {
          for (uint256 j = 0; j < s_provingKeyHashes.length; j++) {
            (uint256 reqId, ) = computeRequestId(
              s_provingKeyHashes[j],
              subConfig.consumers[i],
              subId,
              s_consumers[subConfig.consumers[i]][subId]
            );
            if (s_requestCommitments[reqId] != 0) {
              return true;
            }
          }
        }
        return false;
      }

      modifier onlySubOwner(uint64 subId) {
        address owner = s_subscriptionConfigs[subId].owner;
        if (owner == address(0)) {
          revert ("onlySubOwner: owner = {0}");
        }
        if (msg.sender != owner) {
          revert ("onlySubOwner: must be owner");
        }
      _;
     }
  // 
  //CONFIGURATION
      function setConfig(
        uint16 minimumRequestConfirmations,
        uint32 maxGasLimit,
        uint32 stalenessSeconds,
        uint32 gasAfterPaymentCalculation,
        int256 fallbackWeiPerUnitLink,
        FeeConfig memory feeConfig
      ) external onlyOwner {
        if (minimumRequestConfirmations > MAX_REQUEST_CONFIRMATIONS) {
          revert ("setConfig: minimumRequestConfirmations > MAX_REQUEST_CONFIRMATIONS");
        }
        if (fallbackWeiPerUnitLink <= 0) {
          revert ("setConfig: InvalidLinkWeiPrice");
        }
        s_config = Config({
          minimumRequestConfirmations: minimumRequestConfirmations,
          maxGasLimit: maxGasLimit,
          stalenessSeconds: stalenessSeconds,
          gasAfterPaymentCalculation: gasAfterPaymentCalculation,
          reentrancyLock: false
        });
        s_feeConfig = feeConfig;
        s_fallbackWeiPerUnitLink = fallbackWeiPerUnitLink;
        emit ConfigSet(
          minimumRequestConfirmations,
          maxGasLimit,
          stalenessSeconds,
          gasAfterPaymentCalculation,
          fallbackWeiPerUnitLink,
          s_feeConfig
        );
      }

      function getRequestConfig()
        external
        view
        returns (
          uint16,
          uint32,
          bytes32[] memory
        )
      {
        return (s_config.minimumRequestConfirmations, 
        s_config.maxGasLimit, 
        s_provingKeyHashes);
      }
    //    return (3, 2000000, new bytes32[](0));

      /// XX 
      function getConfig() 
        external
        view
        returns (
          uint16 minimumRequestConfirmations,
          uint32 maxGasLimit,
          uint32 stalenessSeconds,
          uint32 gasAfterPaymentCalculation
        )
      {
        return (
          s_config.minimumRequestConfirmations,
          s_config.maxGasLimit,
          s_config.stalenessSeconds,
          s_config.gasAfterPaymentCalculation
        );
      }
    //   return (4, 2_500_000, 2_700, 33285);
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
        )
      {
        return (
          s_feeConfig.fulfillmentFlatFeeLinkPPMTier1,
          s_feeConfig.fulfillmentFlatFeeLinkPPMTier2,
          s_feeConfig.fulfillmentFlatFeeLinkPPMTier3,
          s_feeConfig.fulfillmentFlatFeeLinkPPMTier4,
          s_feeConfig.fulfillmentFlatFeeLinkPPMTier5,
          s_feeConfig.reqsForTier2,
          s_feeConfig.reqsForTier3,
          s_feeConfig.reqsForTier4,
          s_feeConfig.reqsForTier5
        );
      }



    function getFeeTier(uint64 reqCount) public view returns (uint32) {
      FeeConfig memory fc = s_feeConfig;
      if (0 <= reqCount && reqCount <= fc.reqsForTier2) {
        return fc.fulfillmentFlatFeeLinkPPMTier1;
      }
      if (fc.reqsForTier2 < reqCount && reqCount <= fc.reqsForTier3) {
        return fc.fulfillmentFlatFeeLinkPPMTier2;
      }
      if (fc.reqsForTier3 < reqCount && reqCount <= fc.reqsForTier4) {
        return fc.fulfillmentFlatFeeLinkPPMTier3;
      }
      if (fc.reqsForTier4 < reqCount && reqCount <= fc.reqsForTier5) {
        return fc.fulfillmentFlatFeeLinkPPMTier4;
      }
      return fc.fulfillmentFlatFeeLinkPPMTier5;}


    function getFeedData() public view returns (int256) {
      uint32 stalenessSeconds = s_config.stalenessSeconds;
      bool staleFallback = stalenessSeconds > 0;
      uint256 timestamp;
      int256 weiPerUnitLink;
      (, weiPerUnitLink, , timestamp, ) = LINK_ETH_FEED.latestRoundData();
      if (staleFallback && stalenessSeconds < block.timestamp - timestamp) {
        weiPerUnitLink = s_fallbackWeiPerUnitLink;
      }
      return weiPerUnitLink;}





  // 
  //MISCELLANEOUS 

    function registerProvingKey(address oracle, bytes32 kh) external onlyOwner {
      // not used; see README file or note in 'getgetRandomnessFromProof'
      // bytes32 kh = hashOfKey(publicProvingKey);
      if (s_provingKeys[kh] != address(0)) {
        revert("register PK: proving key already registered");
      }
      s_provingKeys[kh] = oracle;
      s_provingKeyHashes.push(kh);
      emit ProvingKeyRegistered(kh, oracle);
    }



    function deregisterProvingKey(bytes32 kh) external onlyOwner {
      address oracle = s_provingKeys[kh];
      if (oracle == address(0)) {
        revert ("deregester PK: oracle = {0}");
      }
      delete s_provingKeys[kh];
      for (uint256 i = 0; i < s_provingKeyHashes.length; i++) {
        if (s_provingKeyHashes[i] == kh) {
          bytes32 last = s_provingKeyHashes[s_provingKeyHashes.length - 1];
          // Copy last element and overwrite kh to be deleted with it
          s_provingKeyHashes[i] = last;
          s_provingKeyHashes.pop();
        }
      }
      emit ProvingKeyDeregistered(kh, oracle);}



    function recoverFunds(address to) external onlyOwner {
      uint256 externalBalance = LINK.balanceOf(address(this));
      uint256 internalBalance = uint256(s_totalBalance);
      if (internalBalance > externalBalance) {
        revert ("recoverFunds: BalanceInvariantViolated");
      }
      if (internalBalance < externalBalance) {
        uint256 amount = externalBalance - internalBalance;
        LINK.transfer(to, amount);
        emit FundsRecovered(to, amount);
      }
      // If the balances are equal, nothing to be done.
    }
    
    function computeRequestId(
    bytes32 keyHash,
    address sender,
    uint64 subId,
    uint64 nonce
    ) private pure returns (uint256, uint256) {
    uint256 preSeed = uint256(keccak256(abi.encode(keyHash, sender, subId, nonce)));
    return (uint256(keccak256(abi.encode(keyHash, preSeed))), preSeed);
    }

    function getTotalBalance() external view returns (uint256) {
      return s_totalBalance;
    }

    function getFallbackWeiPerUnitLink() external view returns (int256) {
      return s_fallbackWeiPerUnitLink;
      //return 4000000000000000; // 0.004 Ether
    }

    function calculatePaymentAmount(
      uint256 startGas,
      uint256 gasAfterPaymentCalculation,
      uint32 fulfillmentFlatFeeLinkPPM,
      uint256 weiPerUnitGas)
      public view returns (uint96) {
      int256 weiPerUnitLink;
      weiPerUnitLink = getFeedData();
      if (weiPerUnitLink <= 0) {
        revert ("calculatePaymentAmount: InvalidLinkWeiPrice");
      }
      uint256 paymentNoFee = (1e18 * weiPerUnitGas * (gasAfterPaymentCalculation + startGas - gasleft())) /
        uint256(weiPerUnitLink);
      uint256 fee = 1e12 * uint256(fulfillmentFlatFeeLinkPPM);
      if (paymentNoFee > (1e27 - fee)) {
        revert ("calculatePaymentAmount: payment too large"); // Payment + fee cannot be more than all of the link in existence.
      }
      return uint96(paymentNoFee + fee);}


    function typeAndVersion() external pure virtual override returns (string memory) {
      return "VRFCoordinatorV2 1.0.0";
    }


  // 
  //FOR DIRECT FUNDING METHOD/ CONSUMING CONTRACT IMPLEMENTATION:
    function setLinkCoordinatorAddress(address link_coordinator) external {
      linkCoordinator = link_coordinator;
    }


    function oracleWithdraw(address oracle, address recipient, uint96 amount) external nonReentrant onlyOwner{
      if (s_withdrawableTokens[oracle] < amount) {
        revert ("oracleWithdraw: s_withdrawableTokens = 0");
      }
      s_withdrawableTokens[msg.sender] -= amount;
      s_totalBalance -= amount;
      if (!LINK.transfer(recipient, amount)) {
        revert ("oracleWithdraw: InsufficientBalance)");
      }
    }



    function onTokenTransfer(
      address /* sender */, 
      uint256 amount,
      bytes calldata data) external override nonReentrant {
      if (msg.sender != linkCoordinator) {
        revert ("only callable from LINK");
      }
      if (data.length != 32) {
        revert("onTokenTransfer: data.length != 32");
      }
      uint64 subId = abi.decode(data, (uint64));
      if (s_subscriptionConfigs[subId].owner == address(0)) {
        revert("onTokenTransfer: subOwner = {0}");
      }
      // We do not check that the msg.sender is the subscription owner,
      // anyone can fund a subscription.
      uint256 oldBalance = s_subscriptions[subId].balance;
      s_subscriptions[subId].balance += uint96(amount);
      s_totalBalance += uint96(amount);
      emit SubscriptionFunded(subId, oldBalance, oldBalance + amount);
    }

    modifier nonReentrant() {
      if (s_config.reentrancyLock) {
        revert ("Reentrant");
      }
      _;
    }


  //
  //MISC PERSONAL FUNCS
  
    function launchBlockHash(address blockHashStore) external {
      BLOCKHASH_STORE = BlockhashStoreInterface(blockHashStore);
    }

    function withdrawBal(address _consumer) public view returns (uint96 bal_){
      bal_ = s_withdrawableTokens[_consumer];}

    function getSender() external view returns (address Sendr){
      Sendr = msg.sender;}

    function getGas() public view returns (uint256 GAS_){
      GAS_ = gasleft();}

      // LINK comes from WrapperConsumerBase.sol
    function LINK_balance(address address_) external view returns (uint256) {
          uint256 bal = LINK.balanceOf(address_);
          return bal; }

    function getNonce(address person_, uint64 _subId) public view returns (uint64){
      return s_consumers[person_][_subId];}

    function hashOfKey(uint256[2] memory publicKey) public pure returns (bytes32) {
      return keccak256(abi.encode(publicKey));}


    function getExplicitCommit(uint256 _requestId) public view returns(
      uint256 blockNum,
      uint64 subId,
      uint32 callbackGasLimit,
      uint32 numWords,
      address sender){
      RequestCommitment memory rc = m_requestCommitments[_requestId];
      blockNum         = rc.blockNum;
      subId            = rc.subId;
      callbackGasLimit = rc.callbackGasLimit;
      numWords         = rc.numWords;
      sender           = rc.sender;}



 }
      
    





