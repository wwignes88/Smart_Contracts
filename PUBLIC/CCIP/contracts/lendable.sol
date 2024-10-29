// SPDX-License-Identifier: MIT
pragma solidity 0.8.19;

import {IRouterClient} from "@CCIP/node_modules/@chainlink/contracts-ccip/src/v0.8/ccip/interfaces/IRouterClient.sol";
import {OwnerIsCreator} from "@CCIP/node_modules/@chainlink/contracts-ccip/src/v0.8/shared/access/OwnerIsCreator.sol";
import {Client} from "@CCIP/node_modules/@chainlink/contracts-ccip/src/v0.8/ccip/libraries/Client.sol";
import {CCIPReceiver} from "@CCIP/node_modules/@chainlink/contracts-ccip/src/v0.8/ccip/applications/CCIPReceiver.sol";
import {IERC20} from "@CCIP/node_modules/@chainlink/contracts-ccip/src/v0.8/vendor/openzeppelin-solidity/v4.8.0/token/ERC20/IERC20.sol";
import {SafeERC20} from "@CCIP/node_modules/@chainlink/contracts-ccip/src/v0.8/vendor/openzeppelin-solidity/v4.8.0/token/ERC20/utils/SafeERC20.sol";
import {EnumerableMap} from "@CCIP/node_modules/@chainlink/contracts-ccip/src/v0.8/vendor/openzeppelin-solidity/v4.8.0/utils/structs/EnumerableMap.sol";

import {LinkTokenInterface} from "@CHAINLINK/node_modules/@chainlink/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
import {AggregatorV3Interface} from "@CHAINLINK/node_modules/@chainlink/contracts/src/v0.8/interfaces/AggregatorV3Interface.sol";

import {MockUSDC} from "./MockUSDC.sol";


contract Lendable is CCIPReceiver, OwnerIsCreator {
    using EnumerableMap for EnumerableMap.Bytes32ToUintMap;
    EnumerableMap.Bytes32ToUintMap internal s_failedMessages;
    /*using EnumerableMap for EnumerableMap.AddressToUintMap;
    EnumerableMap.AddressToUintMap internal deposit_map;*/
    using SafeERC20 for IERC20;
    
    //
    // variables
        // errors
            error NotEnoughBalance(uint256 currentBalance, uint256 calculatedFees); // Used to make sure contract has enough balance to cover the fees.
            error NothingToWithdraw(); // Used when trying to withdraw Ether but there's nothing to withdraw.
            error FailedToWithdrawEth(address owner, address target, uint256 value); // Used when the withdrawal of Ether fails.
            error DestinationChainNotAllowlisted(uint64 destinationChainSelector); // Used when the destination chain has not been allowlisted by the contract owner.
            error SourceChainNotAllowed(uint64 sourceChainSelector); // Used when the source chain has not been allowlisted by the contract owner.
            error SenderNotAllowed(address sender); // Used when the sender has not been allowlisted by the contract owner.
            error OnlySelf(); // Used when a function is called outside of the contract itself.
            error ErrorCase(); // Used when simulating a revert during message processing.
            error MessageNotFailed(bytes32 messageId);

            // Example error code, could have many different error codes.
            enum ErrorCode {
                // RESOLVED is first so that the default value is resolved.
                RESOLVED,
                // Could have any number of error codes here.
                BASIC
            }

        // Events
            event MessageSent(
                bytes32 indexed messageId, // The unique ID of the CCIP message.
                uint64 indexed destinationChainSelector, // The chain selector of the destination chain.
                address receiver, // The address of the receiver on the destination chain.
                string text, // The text being sent.
                address token, // The token address that was transferred.
                uint256 tokenAmount, // The token amount that was transferred.
                address feeToken, // the token address used to pay CCIP fees.
                uint256 fees // The fees paid for sending the message.
            );

            // Event emitted when a message is received from another chain.
            event MessageReceived(
                bytes32 indexed messageId, // The unique ID of the CCIP message.
                uint64 indexed sourceChainSelector, // The chain selector of the source chain.
                address sender, // The address of the sender from the source chain.
                string text, // The text that was received.
                address token, // The token address that was transferred.
                uint256 tokenAmount // The token amount that was transferred.
            );

            event MessageFailed(bytes32 indexed messageId, bytes reason);
            event MessageRecovered(bytes32 indexed messageId);

        
        // singleton variables
            bool public s_simRevert;
            uint256 public mark1;
            uint256 public mark2;
            uint256 public mark3;
            uint256 public mark4;
            uint256 public mark5;
            uint256 public mark6;
            uint256 public mark7;
            uint256 feeBal;

        // structs
            struct MessageOut {
                uint64 destinationChainSelector; 
                uint64 sourceChainSelector;
                address sender;
                address receiver; // The address of the sending contract on the source chain.
                string text; // The content of the message which will be the EOA of the person sending tokens.
                address token; // received token.
                uint256 sentAmount; // sent amount.
                uint8 feeOption; // 0 = pay Native, 1 = pay Link
                uint256 PaymentFee; // fee paid for ccip [router] service
                }

            struct MessageIn {
                uint64 sourceChainSelector; // The chain selector of the source chain.
                address sender; // The address of the sender.
                address depositor; // The content of the message.
                address token; // received token.
                uint256 amount; // received amount.
                string text;
            }

        // mappings/ arrays
            bytes32[] public sentMessages;
            bytes32[] public receivedMessages; 
            mapping(address => mapping(address => uint256)) public deposits;
            mapping(bytes32 => MessageIn) public ReceivedMsgDetails; 
            mapping(bytes32 => MessageOut) public SentMsgDetails; 
            mapping(uint64 => bool) public allowlistedDestinationChains;
            mapping(uint64 => bool) public allowlistedSourceChains;
            mapping(address => bool) public allowlistedSenders;
            mapping(bytes32 => Client.Any2EVMMessage)
                public failed_messageContents;
            mapping(address => mapping(address => uint256)) public borrowings; 
            IERC20 private s_linkToken;

        MockUSDC public usdcToken;
        LinkTokenInterface linkToken;
        uint256 private contract_chain_selector;
        //
        //=============== CONSTRUCTOR
            constructor(address _router, address _link, uint256 chain_selector_) CCIPReceiver(_router) {
                s_linkToken = IERC20(_link);
                usdcToken = new MockUSDC();
                contract_chain_selector = chain_selector_;
            }

        //
        // [modifier] onlyAllowlistedDestinationChain
            /// @dev Modifier that checks if the chain with the given destinationChainSelector is allowlisted.
            /// @param _destinationChainSelector The selector of the destination chain.
            modifier onlyAllowlistedDestinationChain(uint64 _destinationChainSelector) {
                if (!allowlistedDestinationChains[_destinationChainSelector])
                    revert("destination not allowed");
                _;
            }

        //
        // [modifier] onlyAllowlisted
            /// @dev Modifier that checks if the chain with the given sourceChainSelector is allowlisted and if the sender is allowlisted.
            /// @param _sourceChainSelector The selector of the destination chain.
            /// @param _sender The address of the sender.
            modifier onlyAllowlisted(uint64 _sourceChainSelector, address _sender) {
                if (!allowlistedSourceChains[_sourceChainSelector])
                    revert ("SourceChainNotAllowed");
                if (!allowlistedSenders[_sender]) revert ("SenderNotAllowed");
                _;
            }
        //
        // *** [modifier] onlySelf
            /// @dev Modifier to allow only the contract itself to execute a function.
            /// Throws an exception if called by any account other than the contract itself.
            modifier onlySelf() {
                if (msg.sender != address(this)) revert("   only self   ");
                _;
            }

        //
    //
    // allowlistDestinationChain
        function allowlistDestinationChain(
            uint64 _destinationChainSelector,
            bool allowed
        ) external onlyOwner {
            allowlistedDestinationChains[_destinationChainSelector] = allowed;
        }
    //
    // isDestinationChainAllowed
        function isDestinationChainAllowed(uint64 _destinationChainSelector) external view returns (bool) {
            return allowlistedDestinationChains[_destinationChainSelector];
        }
    //
    // allowlistSourceChain
        function allowlistSourceChain(
            uint64 _sourceChainSelector,
            bool allowed
        ) external onlyOwner {
            allowlistedSourceChains[_sourceChainSelector] = allowed;
        }
    //
    // allowlistSender
        function allowlistSender(address _sender, bool allowed) external onlyOwner {
            allowlistedSenders[_sender] = allowed;
        }
    // islistSender
        function islistSender(address _sender) external view returns (bool) {
            return allowlistedSenders[_sender];
        }
    //
    // isSourceChainAllowed
        function isSourceChainAllowed(uint64 _destinationChainSelector) external view returns (bool) {
            return allowlistedSourceChains[_destinationChainSelector];
        }
    // isChainSupported
        function isChainSupported(uint64 destChainSelector) external view returns (bool supported) {
            return IRouterClient(this.getRouter()).isChainSupported(destChainSelector);
        }
    // --------------------------- SENDING MESSAGE
        //
        // approximateSendFees 
            function approximateSendFees(
                uint64  _destinationChainSelector,
                address _receiver,
                string calldata _text,
                address _token,
                uint256 send_amount,
                uint8   _feeOption) public view returns (uint256 fees){

                address _FeeToken;

                // pay Native
                if (_feeOption == 0) {
                    _FeeToken = address(0);
                } 
                // pay Link 
                if (_feeOption == 1) {
                    _FeeToken = address(s_linkToken);
                }

                // construct message
                Client.EVM2AnyMessage memory message = _buildCCIPMessage(
                    _receiver,
                    _text,
                    _token,
                    send_amount,
                    _FeeToken
                );

                //initialize router
                IRouterClient router = IRouterClient(this.getRouter());

                // get fees for sending message
                fees = router.getFee(_destinationChainSelector, message);
                return (fees);
                }
        //
        // sendMessagePayLINK
            function sendMessagePayLINK(
                uint64 _destinationChainSelector,
                uint64 _sourceChainSelector,
                address _receiver,
                string calldata _text,
                address _token,
                uint256 _amount
            )
                external
                onlyOwner
                onlyAllowlistedDestinationChain(_destinationChainSelector)
                returns (uint256 fees, bytes32 messageId)
            {
                Client.EVM2AnyMessage memory evm2AnyMessage = _buildCCIPMessage(
                    _receiver,
                    _text,
                    _token,
                    _amount,
                    address(s_linkToken)
                );
                IRouterClient router = IRouterClient(this.getRouter());

                fees = router.getFee(_destinationChainSelector, evm2AnyMessage);

                if (fees > s_linkToken.balanceOf(address(this)))
                    revert("  not enough balance  ");

                // approve the Router to transfer LINK tokens on contract's behalf. It will spend the fees in LINK
                s_linkToken.approve(address(router), fees);

                // approve the Router to spend tokens on contract's behalf. It will spend the amount of the given token
                IERC20(_token).approve(address(router), _amount);

                // Send the message through the router and store the returned message ID
                messageId = router.ccipSend(_destinationChainSelector, evm2AnyMessage);

                // store message details in this contract
                MessageOut memory sent_detail = MessageOut(_destinationChainSelector,
                                                            _sourceChainSelector,
                                                            msg.sender,
                                                            _receiver,
                                                            _text,
                                                            _token,
                                                            _amount,
                                                            1,
                                                            fees
                                                        );
                SentMsgDetails[messageId] = sent_detail;
                sentMessages.push(messageId);

                // Emit an event with message details
                emit MessageSent(
                    messageId,
                    _destinationChainSelector,
                    _receiver,
                    _text,
                    _token,
                    _amount,
                    address(s_linkToken),
                    fees
                );

                // Return the message ID
                return (fees, messageId);
            }

        //
        // sendMessagePayNative
            function sendMessagePayNative(
                uint64 _destinationChainSelector,
                uint64 _sourceChainSelector,
                address _receiver,
                string calldata _text,
                address _token,
                uint256 _amount
            )
                external
                onlyOwner
                onlyAllowlistedDestinationChain(_destinationChainSelector)
                returns (uint256 fees, bytes32 messageId)
            {
                // Create an EVM2AnyMessage struct in memory with necessary information for sending a cross-chain message
                // address(0) means fees are paid in native gas
                Client.EVM2AnyMessage memory evm2AnyMessage = _buildCCIPMessage(
                    _receiver,
                    _text,
                    _token,
                    _amount,
                    address(0)
                );

                // Initialize a router client instance to interact with cross-chain router
                IRouterClient router = IRouterClient(this.getRouter());

                // Get the fee required to send the CCIP message
                fees = router.getFee(_destinationChainSelector, evm2AnyMessage);

                if (fees > address(this).balance)
                    revert ('not enough balance');

                // approve the Router to spend tokens on contract's behalf. It will spend the amount of the given token
                IERC20(_token).approve(address(router), _amount);

                // Send the message through the router and store the returned message ID
                messageId = router.ccipSend{value: fees}(
                    _destinationChainSelector,
                    evm2AnyMessage
                );

                // store message details in this contract
                MessageOut memory sent_detail = MessageOut(_destinationChainSelector,
                                                            _sourceChainSelector,
                                                            msg.sender,
                                                            _receiver,
                                                            _text,
                                                            _token,
                                                            _amount,
                                                            0,
                                                            fees
                                                        );
                SentMsgDetails[messageId] = sent_detail;
                sentMessages.push(messageId);

                // Emit an event with message details
                emit MessageSent(
                    messageId,
                    _destinationChainSelector,
                    _receiver,
                    _text,
                    _token,
                    _amount,
                    address(0),
                    fees
                );

                // Return the message ID
                return (fees, messageId);
            }

        //
        // _buildCCIPMessage
            function _buildCCIPMessage(
                address _receiver,
                string calldata _text,
                address _token,
                uint256 _amount,
                address _feeTokenAddress
            ) internal pure returns (Client.EVM2AnyMessage memory) {
                // Set the token amounts
                Client.EVMTokenAmount[]
                    memory tokenAmounts = new Client.EVMTokenAmount[](1);
                Client.EVMTokenAmount memory tokenAmount = Client.EVMTokenAmount({
                    token: _token,
                    amount: _amount
                });
                tokenAmounts[0] = tokenAmount;
                // Create an EVM2AnyMessage struct in memory with necessary information for sending a cross-chain message
                Client.EVM2AnyMessage memory evm2AnyMessage = Client.EVM2AnyMessage({
                    receiver: abi.encode(_receiver), // ABI-encoded receiver address
                    data: abi.encode(_text), // ABI-encoded string
                    tokenAmounts: tokenAmounts, // The amount and type of token being transferred
                    extraArgs: Client._argsToBytes(
                        // Additional arguments, setting gas limit and non-strict sequencing mode
                        Client.EVMExtraArgsV1({gasLimit: 2_000_000, strict: false})
                    ),
                    // Set the feeToken to a feeTokenAddress, indicating specific asset will be used for fees
                    feeToken: _feeTokenAddress
                });
                return evm2AnyMessage;
            }

            /// @notice Fallback function to allow the contract to receive Ether.
            /// @dev This function has no function body, making it a default function for receiving Ether.
            /// It is automatically called when Ether is sent to the contract without any data.
        //
        // getNumberOfSentMessages 
            function getNumberOfSentMessages() external view returns (uint256 number) {
                return sentMessages.length;
            }
        //
        // getSentMessageId 
            function getSentMessageId(uint8 arg_)
                external
                view
                returns (bytes32)
                {
                    // Revert if no messages have been received
                    if (sentMessages.length == 0) revert (" No messages have been sent. ");
                    if (arg_ > sentMessages.length - 1) revert(" input greater than number of messages sent. ");
                    // Fetch the last received message ID
                    bytes32 SentMessageId = sentMessages[arg_];
                    return SentMessageId;
                }
        //
        // getSentMessage
            function getSentMessage(bytes32 messageId)
                external
                view
                returns (uint64 destinatioChainSelector,
                        address ,
                        address ,
                        string memory,
                        address ,
                        uint256 ,
                        uint8 ,
                        uint256 )
                {
                    // Fetch the details of the last received message
                    MessageOut memory Sentdetail = SentMsgDetails[messageId];

                    return (Sentdetail.destinationChainSelector, 
                            Sentdetail.sender, 
                            Sentdetail.receiver, 
                            Sentdetail.text, 
                            Sentdetail.token,
                            Sentdetail.sentAmount,
                            Sentdetail.feeOption,
                            Sentdetail.PaymentFee);
                }
        //
    //
    // --------------------------- RECEIVING MESSAGE
    //  getFailedMessagesIds

        function getFailedMessagesIds()
            external
            view
            returns (bytes32[] memory ids)
        {
            uint256 length = s_failedMessages.length();
            bytes32[] memory allKeys = new bytes32[](length);
            for (uint256 i = 0; i < length; i++) {
                (bytes32 key, ) = s_failedMessages.at(i);
                allKeys[i] = key;
            }
            return allKeys;
        }

    // 
    //  ccipReceive
        function ccipReceive(
            Client.Any2EVMMessage calldata any2EvmMessage
        )
            external
            override
            onlyRouter
            onlyAllowlisted(
                any2EvmMessage.sourceChainSelector,
                abi.decode(any2EvmMessage.sender, (address))
            ) // Make sure the source chain and sender are allowlisted
        {
            mark1 = 1;
            /* solhint-disable no-empty-blocks */
            try this.processMessage(any2EvmMessage) {
                // Intentionally empty in this example; no action needed if processMessage succeeds
            } catch (bytes memory err) {
                // Could set different error codes based on the caught error. Each could be
                // handled differently.
                mark4 = 1;
                s_failedMessages.set(
                    any2EvmMessage.messageId,
                    uint256(ErrorCode.BASIC)
                );
                mark5= 1;
                failed_messageContents[any2EvmMessage.messageId] = any2EvmMessage;
                mark6 = 1;
                // Don't revert so CCIP doesn't revert. Emit event instead.
                // The message can be retried later without having to do manual execution of CCIP.
                emit MessageFailed(any2EvmMessage.messageId, err);
                return;
            }
        }

    // 
    //  processMessage
        function processMessage(
            Client.Any2EVMMessage calldata any2EvmMessage
        )
            external
            onlySelf
            onlyAllowlisted(
                any2EvmMessage.sourceChainSelector,
                abi.decode(any2EvmMessage.sender, (address))
            ) // Make sure the source chain and sender are allowlisted
        {
            mark2 = 1;
            // Simulate a revert for testing purposes
            if (s_simRevert) revert("___SIM REVERT___");
            mark3 = 1;
            _ccipReceive(any2EvmMessage); // process the message - may revert as well
        }

    //
    //  retryFailedMessage
        function retryFailedMessage(
            bytes32 messageId,
            address tokenReceiver
        ) external onlyOwner {
            // Check if the message has failed; if not, revert the transaction.
            if (s_failedMessages.get(messageId) != uint256(ErrorCode.BASIC))
                revert ("message not failed");

            // Retrieve the content of the failed message.
            Client.Any2EVMMessage memory message = failed_messageContents[messageId];

            // This example expects one token to have been sent, but you can handle multiple tokens.
            // Transfer the associated tokens to the specified receiver as an escape hatch.
            IERC20(message.destTokenAmounts[0].token).safeTransfer(
                tokenReceiver,
                message.destTokenAmounts[0].amount
            );

            // Set the error code to RESOLVED to disallow reentry and multiple retries of the same failed message.
            s_failedMessages.set(messageId, uint256(ErrorCode.RESOLVED));

            _ccipReceive(message);
            // Emit an event indicating that the message has been recovered.
            emit MessageRecovered(messageId);
        }
    //
    //  setSimRevert
        function setSimRevert(bool simRevert) external  {
            s_simRevert = simRevert;
        }
    //  isSimRevert
        function isSimRevert() external view returns (bool){
            return s_simRevert;
        }
    //
    // _ccipReceive
        function _ccipReceive(
            Client.Any2EVMMessage memory any2EvmMessage
        ) internal override {
            bytes32 messageId = any2EvmMessage.messageId; // fetch the messageId
            uint64 sourceChainSelector = any2EvmMessage.sourceChainSelector; // fetch the source chain identifier (aka selector)
            address sender = abi.decode(any2EvmMessage.sender, (address)); // abi-decoding of the sender address
            address depositor = abi.decode(any2EvmMessage.data, (address)); // abi-decoding of the depositor's address

            // Collect tokens transferred. This increases this contract's balance for that Token.
            Client.EVMTokenAmount[] memory tokenAmounts = any2EvmMessage.destTokenAmounts;
            address token = tokenAmounts[0].token;
            uint256 amount = tokenAmounts[0].amount;
            string  memory text         = abi.decode(any2EvmMessage.data, (string)); 

            //uid, sourceChainSelector, sender, depositor, tokenAmounts[0]);nt64 destinationChainSelector = 
            
            MessageIn memory last_received_message = MessageIn(sourceChainSelector, 
                                                                sender,
                                                                depositor, 
                                                                token, 
                                                                amount,
                                                                text);
            ReceivedMsgDetails[messageId] = last_received_message;
            receivedMessages.push(messageId);

            deposits[depositor][token] += amount;

            emit MessageReceived(
                any2EvmMessage.messageId,
                any2EvmMessage.sourceChainSelector, // fetch the source chain identifier (aka selector)
                abi.decode(any2EvmMessage.sender, (address)), // abi-decoding of the sender address,
                abi.decode(any2EvmMessage.data, (string)),
                any2EvmMessage.destTokenAmounts[0].token,
                any2EvmMessage.destTokenAmounts[0].amount
            );
        }
    //
    // getNumberOfReceivedMessages
        function getNumberOfReceivedMessages() external view returns (uint256 number) {
            return receivedMessages.length;
        }
    //
    // getReceivedMessageId 
        function getReceivedMessageId(uint8 arg_)
            external
            view
            returns (bytes32)
            {
                // Revert if no messages have been received
                if (receivedMessages.length == 0) revert (" No messages have been sent. ");
                if (arg_ > receivedMessages.length - 1) revert(" input greater than number of messages sent. ");
                // Fetch the last received message ID
                bytes32 ReceivedMessageId = receivedMessages[arg_];
                return ReceivedMessageId;
            }
    //
    // getReceivedMessage
        function getReceivedMessage(bytes32 messageId)
            external
            view
            returns (uint64, address , address,  uint256,  string memory)
            {
                MessageIn memory detail = ReceivedMsgDetails[messageId];

                return (detail.sourceChainSelector, 
                        detail.sender, 
                        detail.token, 
                        detail.amount, 
                        detail.text);
            }
    //
    // ------------------------- BORROWS/ REPAYMENTS
    //
    /* !!!  NOT IMPLEMENTED  !!! 
    // priceFeed
        function getPriceFeed(address snx_asset) public view returns (uint256){
            AggregatorV3Interface priceFeed = AggregatorV3Interface(snx_asset);
            (, int256 price, , , ) = priceFeed.latestRoundData();
            uint256 price18decimals = uint256(price * (10 ** 10)); // make USD price 18 decimal places from 8 decimal places.
            return price18decimals;
        }
    //
    // get deposited
        function lendingInfo(address borrower, address token) public view returns(uint256, uint256){
                uint256 deposited  = deposits[borrower][token];
                uint256 borrowed   = borrowings[borrower][token];
                return (deposited, borrowed);
        }
    //
    //------------ borrowUSDC
        function borrowUSDC(address transferredToken, 
                            uint256 borrow_amnt, 
                            address SNX_asset) public  {
            require(transferredToken != address(0), "Caller has not transferred this token");

            uint256 borrowed   = borrowings[msg.sender][transferredToken];
            uint256 deposited  = deposits[msg.sender][transferredToken];
            uint256 collateral = deposited - borrowed;
            uint256 borrowable = (collateral * 70) / 100; // 70% collaterization ratio.

            // SNX/USD on Sepolia (https://sepolia.etherscan.io/address/0xc0F82A46033b8BdBA4Bb0B0e28Bc2006F64355bC)
            // Docs: https://docs.chain.link/data-feeds/price-feeds/addresses#Sepolia%20Testnet
            // uint256 price = getPriceFeed(0xc0F82A46033b8BdBA4Bb0B0e28Bc2006F64355bC);
            uint256 price = getPriceFeed(SNX_asset);
            uint256 borrowableInUSDC = borrowable * price;
            require(borrow_amnt <= borrowableInUSDC, "borrow amount greater than allowed amount");

            // MintUSDC
            usdcToken.mint(msg.sender, borrow_amnt);

            // Update state.
            borrowings[msg.sender][address(usdcToken)] += borrow_amnt;
            assert(borrowings[msg.sender][address(usdcToken)] == borrow_amnt);
        }
    //
    //------------ repayAndSendMessage
        function repay(uint256 repay_amount, address transferredToken) public {
            uint256 borrowed = borrowings[msg.sender][address(usdcToken)];
            
            // if repay amount greater than borrowed amount, add to deposit balance
            if (repay_amount > borrowed){
                deposits[msg.sender][transferredToken] += repay_amount - borrowed;
            }

            uint256 mockUSDCBal = usdcToken.balanceOf(msg.sender);
            require(mockUSDCBal >= repay_amount, "Caller's USDC token balance insufficient for repayment");

            if (usdcToken.allowance(msg.sender, address(this)) < borrowings[msg.sender][address(usdcToken)]) {
            revert("Protocol allowance is less than amount borrowed");
            }

            usdcToken.burnFrom(msg.sender, repay_amount);

            borrowings[msg.sender][address(usdcToken)] -= repay_amount;
            //deposits[msg.sender][transferredToken] -= amount;

        }

        function recordDeposit(address sender, uint256 amount) internal {
            deposits[sender].amount += amount;
            if (!deposits[sender].locked) {
            deposits[sender].locked = true;
            }
        }

    //  */
    // ------------------------- MISC
    receive() external payable {}
    //
    // withdraw

        function withdraw(address _beneficiary) public onlyOwner {
            // Retrieve the balance of this contract
            uint256 amount = address(this).balance;

            // Revert if there is nothing to withdraw
            if (amount == 0) revert NothingToWithdraw();

            // Attempt to send the funds, capturing the success status and discarding any return data
            (bool sent, ) = _beneficiary.call{value: amount}("");

            // Revert if the send failed, with information about the attempted transfer
            if (!sent) revert FailedToWithdrawEth(msg.sender, _beneficiary, amount);
        }
    //
    // withdrawToken

        function withdrawToken(
            address _beneficiary,
            address _token
        ) public onlyOwner {
            // Retrieve the balance of this contract
            uint256 amount = IERC20(_token).balanceOf(address(this));

            // Revert if there is nothing to withdraw
            if (amount == 0) revert NothingToWithdraw();

            IERC20(_token).transfer(_beneficiary, amount);
        }
    // 
    // misc functions
        uint256 ccip_tx_count;
        mapping(uint256 => bytes32) public transactionHashes;

        // Function to get the count for a specific transaction hash
        function getHash(uint256 tx_number) external view returns (bytes32) {
            return transactionHashes[tx_number];
        }

        // Function to get the count for a specific transaction hash
        function mapHash(bytes32 tx_hash) external {
            transactionHashes[ccip_tx_count] = tx_hash;
            ccip_tx_count++;
        }
        // Function to get the count for a specific transaction hash
        function get_tx_count() external view returns (uint256 ){
            return ccip_tx_count;
        }
    // 

}
