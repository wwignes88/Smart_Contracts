
from scripts.helpful_scripts import *
from scripts.CCIP_dicts import *
from brownie import interface, config, network, Wei, convert
import sys
import time
import datetime
from brownie.network import priority_fee, max_fee


def test_():
    print('\n=============== test.py =====================\n')
    
    OPTION = 1
    if OPTION == 1:
        receive_network = "polygon-test"
        send_network    = "sepolia"
    if OPTION == 2:
        receive_network = "sepolia"
        send_network    = "polygon-test"
    
    if network.show_active() == receive_network:
        active_contract_str    = 'receiver'
        passive_contract_str   = 'sender'
    if network.show_active() == send_network:
        active_contract_str    = 'sender'
        passive_contract_str   = 'receiver'
        
        
    account    = get_account()
    accountII  = get_ALT_account()
    BnM        = get_BnM_contract('BnM') 
    LnM        = get_BnM_contract('LnM') 
    LINK       = interface.LinkTokenInterface(config["networks"][network.show_active()]['link'])

    active_contract  = get_contract('lendable')
    
    # get relevant balances
    (GasBal,
     my_BnM, 
     my_LINK, 
     contract_BnM, 
     contract_LINK,
     contract_native) = update_CCIP_Bals(account, BnM, LnM, LINK, active_contract, True )

    # check gas balance
    if GasBal*1e-18 < 0.01:
        print('\n gas balance is low. Get ETH.')
        sys.exit(0)


    # get BnM Token in sender account
    if my_BnM < 0.1*1e18:
        dep_amount = 0.2*GasBal
        print(f'\ndripping BnM Token...')
        BnM.drip(account.address, {"from":account})

    #===============================================================
    #===============================================================
    #               Retrieve Received Messages
    #===============================================================
    #===============================================================
    
    if network.show_active() == receive_network:

        #-------------------------------------------------
        #               BEFORE SENDING
        #-------------------------------------------------

        # simulate revert
        want_revert = False
        simulate_revert = active_contract.isSimRevert()
        print(f'\nsim revert set? {simulate_revert}')
        if not simulate_revert and want_revert:
            tx = active_contract.setSimRevert(True, {"from": account}) 
            tx.wait(2)


        # allow receiving CCIP messages from sender chain
        source_selector = chain_selectors[send_network]
        source_selector_status = active_contract.isSourceChainAllowed(source_selector)
        if not source_selector_status:
            print(f'---------\nenabling source chain ({send_network})...')
            tx = active_contract.allowlistSourceChain(source_selector, True, {"from": account})
            tx.wait(1)

        # enable sender contract address to send messages
        # *sender contract presumed to be lendable.sol on sender network. 
        sender_address = config["networks"][send_network]["lendable"]
        source_selector_status = active_contract.islistSender(sender_address)
        if not source_selector_status:
            print(f'---------\nenabling sender address...')
            tx = active_contract.allowlistSender(sender_address, True, {"from": account})
            tx.wait(1)

        #-------------------------------------------------
        #               AFTER SENDING
        #-------------------------------------------------
        get_failed_messages = True

        if get_failed_messages:
            print(f'\nretrieving failed message IDs...')
            failed_messages = active_contract.getFailedMessagesIds()
            print(f'failed message: \n{failed_messages}')
            time.sleep(2)

        num_received_messages = active_contract.getNumberOfReceivedMessages() 
        print(f'\nNumber received messages: {num_received_messages}')
        
        if num_received_messages == 0:
            sys.exit(0)
            
        last_msg_Id = active_contract.getReceivedMessageId(0)
        print(f'\nLast received message Id:\n     {last_msg_Id}')

        message = active_contract.getReceivedMessage(last_msg_Id)
        print(F'\nlast message:')
        source_chain = get_chain(message[0])
        print(f'    source chain : {source_chain}')
        print(f'    sender       : {message[1]}')
        token     = interface.IERC20(message[2])
        tokenSym  = token.symbol()
        print(f'    token        : {tokenSym}')
        sent_amnt = message[3]
        print(f'    sent amount  : {sent_amnt*1e-18}')
        print(f'    text         : {message[4]}')
        

        #------------------------------------------------
        #           RETRY
        #------------------------------------------------

        retry = False
        if retry:
            tokenReceiver = account.address
            messageId     = failed_messages[-1]

            print(f'\nretrying message...')
            tx = transferer.retryFailedMessage(messageId, tokenReceiver, {"from": account}) 
            tx.wait(1)


    #===============================================================
    #===============================================================
    #                  Send Messages
    #===============================================================
    #===============================================================
    
    if network.show_active() == send_network:

        #--------------------------------------
        #       Fund Contract
        #--------------------------------------

        # fund sender contract with BnM
        if contract_BnM < 0.002*1e18 :
            transfer_amount = my_BnM*0.2
            print(f'---------\ntransfering {transfer_amount*1e-18} BnM to sender...')
            BnM.transfer(active_contract.address, transfer_amount, {"from": account})


        #---------------------------------------
        #          Transfer 
        #---------------------------------------
    
        _receiver = config["networks"][receive_network]["lendable"]
        _text     = f"time: {datetime.datetime.now()}"
        _token    = BnM.address
        _amount   = 0.001*1e18
        destination_selector = chain_selectors[receive_network]
        source_selector = chain_selectors[send_network]

        approximate_Fees = False
        if approximate_Fees:
            print(f'\napproximating fees...')
            # approximate send fees
            send_fee = active_contract.approximateSendFees(
                destination_selector,
                _receiver,
                _text,
                _token,
                _amount,
                _feeOption) 

            print(F'\nSend Fees: {send_fee*1e-18}')

        sendMessage = False  ;  _feeOption = 1 # 0: pay native, 1: pay LINK
        if sendMessage:
            
            # allow receiving CCIP messages from sender chain
            destination_selector_status = active_contract.isDestinationChainAllowed(destination_selector)
            if not destination_selector_status:
                print(f'---------\nenabling destination chain ({receive_network})...')
                tx = active_contract.allowlistDestinationChain(destination_selector, True, {"from": account})
                tx.wait(1)
            
            
            # transfer and pay with NATIVE
            if _feeOption == 0:
                
                # deposit native ETH into contract
                if contract_native*1e-18 < 0.01:
                    transfer_amount = 0.05*GasBal
                    print(f'\ndepositing {transfer_amount*1e-18} native into {active_contract_str} contract....')
                    tx = account.transfer(active_contract, transfer_amount)
                    tx.wait(1)
                    
                print(f'---------\nsending BnM token to {receive_network} network [NATIVE pyment]')
                
                tx = active_contract.sendMessagePayNative(
                    destination_selector,
                    source_selector,
                    _receiver,
                    _text,
                    _token,
                    _amount,
                    {"from": account}) 

            # transfer and pay with LINK
            if _feeOption == 1:
                print(f'---------\ntransfering BnM token to {receive_network} network [LINK pyment]')
                
                if my_LINK < 1*1e18 :
                    print('\n   user LINK balance is low. Use faucet [testnets], purchase [mainnets] or swap with uniswap.')
                    sys.exit(0)
                    
                # fund sender contract with LINK
                if contract_LINK < 0.5*1e18 :
                        transfer_amount = 1*1e18
                        print(f'---------\ntransfering {transfer_amount*1e-18} LINK to sender...')
                        LINK.transfer(active_contract.address, transfer_amount, {"from": account})

                
                tx = active_contract.sendMessagePayLINK(
                    destination_selector,
                    source_selector,
                    _receiver,
                    _text,
                    _token,
                    _amount,
                    {"from": account}) 
                tx.wait(2)
  
                """
                    # Get the transaction hash
                    tx_hash = tx.txid
                    print(f"Transaction Hash: {tx_hash}")
                    tx2 = transferer.mapHash(tx_hash, {"from": account})
                    tx2.wait(1)
                    
                    tx_count = transferer.get_tx_count()
                    print(f'\ntx count: {tx_count}')
                    last_hash = transferer.getHash(tx_count-1)
                    print(f'last_hash: {last_hash}')"""
            
        get_last_msg = True
        if get_last_msg:
                
            num_sent_messages = active_contract.getNumberOfSentMessages() 
            print(f'\nNo. sent messages: {num_sent_messages}')
            
            last_msg_Id = active_contract.getSentMessageId(0)
            print(f'\nLast message Id: {last_msg_Id}')

            message = active_contract.getSentMessage(last_msg_Id)
            
            print(F'\nlast message:')
            dest_chain = get_chain(message[0])
            print(f'    dest. chain  : {dest_chain}')
            print(f'    sender       : {message[1]}')
            print(f'    receiver     : {message[2]}')
            print(f'    text         : {message[3]}')
            token     = interface.IERC20(message[4])
            tokenSym  = token.symbol()
            print(f'    token        : {tokenSym}')
            sent_amnt = message[5]
            print(f'    sent amount  : {sent_amnt*1e-18}')
            feeType = Fee_Options[message[6]]
            print(f'    fee type     : {feeType}')
            fee       = message[7]
            print(f'    payment fee  : {fee*1e-18}')

    
    
    
    
    
    
    
    
    #=================================
    #         WITHDRAW
    #================================
    withdraw      = False
    withdrawToken = False

    # withdraw native [network] ETH
    if withdraw:
        print(f'\n withdrawing native...')
        _beneficiary = account.address
        transferer.withdraw(_beneficiary, {"from": account})
    
    # withdraw Token
    if withdrawToken:
        _beneficiary = account.address
        _token = BnM
        print(f'\n withdrawing {_token.symbol()} Token...')
        transferer.withdrawToken(
            _beneficiary,
            _token,
            {"from": account}
        ) 

    # update balances
    (GasBal,
     my_BnM, 
    my_LINK, 
    transferer_BnM, 
    transferer_LINK,
    transferer_native) = update_CCIP_Bals(account, BnM, LnM, LINK, active_contract, True )
    
    
def main():
    test_()

