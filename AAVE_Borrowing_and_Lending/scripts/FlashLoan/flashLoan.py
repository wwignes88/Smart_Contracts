from scripts.helpful_scripts import * 
from scripts.LoadContracts import * 
# from scripts.ListenAndSwap import * # what the listener script would be called. see comments below.
from brownie import interface, config, network
import sys
import time
 

def FlashExecute():  
    
    # check FlashLoan.sol Wmatic balance (for gas)...fund if needed
    erc20 = Wmatic
    FlashBal    = token_balance(erc20, flashAddr)
    myWmaticBal = token_balance(erc20, account.address)

    # withdrawWMATIC from FlashLoan.sol
    # set this to True and run BEFORE you re-deploy FlashLoan.sol
    withdraw_Wmatic = False 
    
    if FlashBal*1e-18 < 0.02 and withdraw_Wmatic == False:  
        
        if myWmaticBal *1e-18 < 0.04:
            # deposit WMATIC to account (converts MATIC TO WMATIC)
            # *make sure to import WMATIC into wallet using the "WMatic_token"
            # address in the config file.
            depositTokens(erc20, 0.05*1e18)

        # transfer WMATIC to FlashLoan contract
        # will be used for gas charged to FlashLoan.sol during flash loan.
        transferAmount = 0.03*1e18
        print(f'\ntransfering {transferAmount*1e-18} {erc20.symbol()} to FlashLoan contract....')
        tx = erc20.transfer(flashAddr, transferAmount, {"from": account}) ; tx.wait(1)
    
    # get balances of FlashLoan contract.
    getContractBalances(FlashLoan)  
    
    if withdraw_Wmatic:    
        print('\nwithdrawing Wmatic from FlashLoan contract...')
        tx = FlashLoan.withdrawToken(erc20.address, {"from": account}) ; tx.wait(1) 
        print('withdrew Wmatic.')
        sys.exit(0) # exit then re-deploy FlashLoan.sol (FlashLoan would revert without 
        #             Wmatic funds for gas anyway).


    

    #------------------------------ LISTEN FOR REQUESTS
    """
    see testListener.py in scripts/TEST_SCRIPTS folder.
    
    I would LIKE to test if it is possible to detect an emitted event from the flashLoan
    and then run a python script after its detection. I am curious if 
    
        A) this would in some way be blocked by the ILendingPoool contract
        B) if it would complete in time [before the flashloan is withdrawn]
        C) how secure is this method?
        
    However, I am relying on 'EventWatcher' to listen for requests. For whatever reason,
    it does not jive with infura. I believe this relates to the use of https vs wss 
    (websocket) node provider addresses.
    Alchemy requires an upgrade ($$) to use the mumbai network.
    The other option is to run on sepolia which Alchemy supports for free. 
    However, AAVE does not have contracts available on sepolia!!
    
    I could troubleshoot this issue, but right now I am not even sure what I want to 
    use flashloans for, so I'll wait on this.
    
    
    listenForRequest()  
    if watcher._has_started:
        print('\nVRF machinery is watching for requests.')
        print(f'\ntargets:  {watcher.target_events_watch_data}')
        """
        
    #==================================================
    #================== FLASH LOAN ====================
    #==================================================

    getFlashLoan = False
    
    if getFlashLoan:
        print('\n getting flashloan...')
        assets  = [Wmatic.address]
        amounts = [0.1*1e18]
        premiums= [0.005*1e18]
        modes   = [0]
        onBehalfOf = flashAddr
        tx = FlashLoan.flashI(assets,
                                amounts,
                                premiums,
                                modes,
                                onBehalfOf,
                                {"from": account})
        tx.wait(1)
    


def main():
    FlashExecute() 