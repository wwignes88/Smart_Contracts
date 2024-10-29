
from scripts.Load.helpful_scripts import *
from scripts.Load.DICTS import *
from brownie import interface, config, network, Wei, convert
import sys
from brownie.network import priority_fee, max_fee

NETWORK = network.show_active()
active_network = NETWORK_NAMES[NETWORK] 
_gwei = 1e-9
_wei  = 1e-18
_ETH  = 1e18

def getTokens():
    print('\n=============== getTokens.py =====================\n')
    get_wrapped_token = False
    withdraw          = False 
    deposit_to_pool   = False
    dict_             = POLYGON

    # --------------------- Set Parameters
    GasLimit    = 400422
                  
    priorityFee = "2 gwei"  ; priority_fee(priorityFee)
    maxFee      = "43 gwei" ; max_fee(maxFee)
    
    lending_pool  = get_lending_pool()
    account       = get_account() ; GasBal = account.balance()
    EXPLORaccount = get_ALT_account()
    dict_network  = dict_['network']

    # make sure dictionary matches network.
    if dict_network != active_network:
        print(f'   must use {active_network} ditionary on {active_network} network!\n\n')
        sys.exit(0)

    # get conversion rates
    df, times, rates, syms = get_latest_rates(dict_, False)

    # native token for active network:
    native_rate_sym = NETWORK_SYMS[NETWORK]
    native_sym      = dict_['symb']

    # rates:
    native_usd = df.loc[native_rate_sym, 'rates_usd']
    eth_usd    = df.loc['eth_usd', 'rates_usd'] 
    eth_native = eth_usd/native_usd
    print('\nNative [network] conversion rates:')
    print(f'    {native_rate_sym} : {native_usd}')
    print(f'    eth_usd   : {eth_usd}')
    print(f'    eth_{native_sym} : {eth_native}')

    
    #------------ Token asset
    # contract
    asset_ = 'matic'
    Token  = TokenContract(asset_) 
    print(f'\n{Token.symbol()} balances:')
    Token_bal = tok_bal(Token, account.address, True)
    if NETWORK in aTOKEN_ENVS:
        aToken = TokenContract('a'+asset_) ; a_bal = tok_bal(aToken, account.address, True)
        sToken = TokenContract('s'+asset_) ; s_bal = tok_bal(sToken, account.address, True)
        vToken = TokenContract('v'+asset_) ; v_bal = tok_bal(vToken, account.address, True)

    # get asset configuration; LTV, liquidation threshold, reserve is frozen/active, etc.
    asset_config_list, asset_config_dict = get_asset_configuration(lending_pool, Token, False)
    reserve_froze = asset_config_dict['reserve_froze']
    
    # asset conversion rate
    if NETWORK in LIVE_ENVS:
        asset_usd  = getRoundData(dict[asset_+'_usd'], None)
    else:
        asset_usd = df.loc[asset_+'_usd', 'rates_usd'] 
    eth_asset = eth_usd/asset_usd
    native_asset = native_usd/asset_usd

    print(f'\n{Token.symbol()} rates:')
    print(f'    {asset_}_usd : {asset_usd}')
    print(f'    eth_{asset_} : {eth_asset}')
    print(f'    {native_sym}_{asset_} : {native_asset}')

    #----------- gas info
    print(f'\nGas Balance : {GasBal*_wei} {native_sym} = \
${np.round(GasBal*native_usd*_wei,6)} = {np.round(GasBal*_gwei/eth_native,4)} GWETH')
    
    #----------- get lending pool info
    c1,d1,b1,LT,LTV,H  = get_borrowable_data(lending_pool, account, False)

    eth_print(c1 ,b1 ,d1 , Token, eth_usd, eth_asset)





                            #######################
                            #######################
                            #######################




    # set option.
    OPTIONS = [11] 


    #---------------- GET TOKEN/ DEPOSIT TO POOL
    if 1 in OPTIONS:
        # get wrapped [erc20] native tokens/ deposit these to pool to get aTokens
        # transfer/ transfer from to move Tokens between accounts.
        print('\n---- DEPOSIT/TRANSFER TOKENS, DEPOSIT TO POOL [1]')
        transfer        = False
        transferFrom    = False
        get_token       = True
        deposit_to_pool = False

        if transfer :  # *** untested; needs work
            asset_ = 'dai'
            transfer_asset     = TokenContract(asset_) 
            transfer_token_bal = tok_bal(transfer_asset, account.address, True)
            transfer_to        = account.address
            transfer_amount    = transfer_token_bal*0.1 
            print(f'\ntransfering {transfer_amount*_wei} {transfer_asset.symbol()}...')
            transfer_asset.transfer(transfer_to, transfer_amount, {"from": account})

        if transferFrom :  # **** untested; needs work
            transfer_amount = GasBal*native_asset*0.1 
            print(f'\ntransfering {transfer_amount*_wei} {asset_}...')

            transfer_asset  = Token
            transfer_asset.transferFrom(transfer_asset.address, transfer_amount, {"from": account})

        if get_token :

            from_account         = EXPLORaccount
            from_acc_balance     = from_account.balance()
            token_deposit_amount = from_acc_balance*0.1    # should be native units

            gasUsed, gasPrice, gasCost = depositTokens(from_account,
                                                        Token, 
                                                        token_deposit_amount, 
                                                        GasLimit, 
                                                        priorityFee, 
                                                        maxFee,
                                                        eth_usd,
                                                        eth_native,
                                                        eth_asset,
                                                        native_usd,
                                                        native_asset,
                                                        native_sym)

        if deposit_to_pool:
            dep_amount = Token_bal*0.1 # in Tokens [asset] units

            print(f'\ndepositing \n\
                = {dep_amount*1e-18} {Token.symbol()} <-------\n\
                    = {dep_amount*1e-18/native_asset} {native_sym}\n\
                        = {dep_amount*1e-9/eth_asset} GWETH\n\
                            = {dep_amount*asset_usd*1e-18} USD\n\
                                ....')

            deposit_to_Pool(dep_amount,
                            lending_pool,
                            Token,
                            priorityFee,
                            maxFee,
                            GasLimit)

    #*--------------------------- WITHDRAW          
    if 2 in OPTIONS:
        # withdraw aTokens
        print('\n---- WITHDRAW [2]')

        asset_withdraw_amount = a_bal*0.1   # must be <= aToken balance
        rateMode = 2

        # Check if asset is froze
        if reserve_froze:
            input(f'\n{Token.symbol()} aset is frozen. Cannot withdraw')
            #sys.exit(0)
            
        print(f'\n    withdrawing {asset_withdraw_amount*_gwei/eth_asset} GWETH  ')
        print(f'                = {asset_withdraw_amount*_wei/native_asset} {native_sym}')
        print(f'                = {asset_withdraw_amount*_wei} {Token.symbol()}\n')
        #check_gas_ratio(withdraw_amount, GasLimit)
        
        try:
            lending_pool.withdraw(Token.address, asset_withdraw_amount, account.address, {"from": account})
            a_bal = tok_bal(aToken, account.address, True)
        except:
            print(f'   !!! failed to withdraw {Token.symbol()}!!!')

    #---------------------------- BORROW             
    if 3 in OPTIONS:
        # get debt tokens; 1: stable debt, 2: variable debt
        print('\n---- BORROW [3]')
        
        # borrow amount in ETH units. This is convenient because collateral is reported in ETH (wei).
        ETH_borrow_amount = c1*0.1 
                                
        # borrow amount must be less than collateral*LTV [run option 9 to get updated value]
        if ETH_borrow_amount >= c1*0.4:
            print(f'{ETH_borrow_amount*_gwei} GWETH >= {c1*0.4*_gwei} GWETH\n\
                cannot borrow.')
            sys.exit(0)

        # Check if asset is froze
        if reserve_froze:
            input(f'\n{Token.symbol()} aset is frozen. Cannot withdraw')
            #sys.exit(0)
            
            
        asset_borrow_amount = ETH_borrow_amount*eth_asset
        interestRateMode  = 1 # 1: stable, 2: variable
        
        print(f'\n    borrowing {ETH_borrow_amount*_gwei} GWETH  ')
        print(f'             = {ETH_borrow_amount*eth_native*_wei} {native_sym}')
        print(f'             = {asset_borrow_amount*_wei} {Token.symbol()}...\n')

        try:
            tx = lending_pool.borrow(Token, asset_borrow_amount, interestRateMode, 0, account.address, {"from": account, "gas_limit": GasLimit})
            print_Δb = True
            
            #c1,d1,b1,LT,LTV,H   = get_borrowable_data(lending_pool, account, False)
            #eth_print(c1 ,b1 ,d1 , Token, eth_usd, eth_asset)

            block_number = tx.block_number
            gas_used     = tx.gas_used    
            gas_price    = tx.gas_price   
            gas_cost     = gas_price*gas_used
            print(f'     Gas cost: {gas_cost*1e-18} ETH ( % {gas_cost/ETH_borrow_amount} )')
            print(f'             = {gas_cost*eth_asset*_wei} {Token.symbol()}')
            print(f'             = {gas_cost*eth_usd*_wei} USD')
            

        except Exception as e:
            print('\      !!!  failed to borrow  !!!')
            print(f"An error occurred: {str(e)}")

    #---------------------------- REPAY           
    if 4 in OPTIONS:
        print('\n---- REPAY [4]')

        rateMode = 2     # select rate mode; 1=stable, 2=variable
        per      = 0.1   # enter percentage of debt to be repaid.

        # set debt token
        if rateMode == 1:
            debt_token = sToken
        if rateMode == 2:
            debt_token = vToken

        debt_bal = tok_bal(debt_token, account.address, True)
        if debt_bal == 0:
            print(f'    no {debt_token.symbol()} debt to pay\n')

        if debt_bal > 0:
            # amount of debt to be paid
            repay_amount = debt_bal*per
            ETH_repay_amount = repay_amount/eth_asset

            # approve lending pool
            approve_tx = approve_erc20(account, repay_amount, lending_pool.address, Token)

            print(f'\n    repaying  {repay_amount*_wei} {Token.symbol()}')
            print(f'            = {ETH_repay_amount*_wei} ETH')
            print(f'            = {ETH_repay_amount*eth_usd*_wei} USD...\n')

            try:
                tx = lending_pool.repay(Token.address, repay_amount, rateMode, account.address, {"from": account})
                block_number = tx.block_number
                gas_used     = tx.gas_used    
                gas_price    = tx.gas_price   
                gas_cost     = gas_price*gas_used
                print(f'     Gas cost: {gas_cost*1e-18} ETH ( % {gas_cost/ETH_repay_amount} )')
                print(f'             = {gas_cost*eth_asset*_wei} {Token.symbol()}')
                print(f'             = {gas_cost*eth_usd*_wei} USD')
                
            except Exception as e:
                print(f'\n    !!! failed to repay {Token.symbol()} !!!')
                print(f"        An error occurred: {str(e)}\n")

    #---------------------------- SWAP BORROW RATE   ****** not working
    if 5 in OPTIONS:
        print('\n---- SWAP BORROW RATE [5]')
        rateMode = 1 # Stable: 1, Variable: 2

        try:
            lending_pool.swapBorrowRateMode(Token.address, rateMode, {"from": account}) 
        except Exception as e:
            print(f'\n    !!! failed to swap rate mode !!!')
            print(f"        An error occurred: {str(e)}\n")

    #---------------------------- SET USER RESERVE AS COLLATERAL    
    if 6 in OPTIONS:
        print('\n---- SET USER RESERVE AS COLLATERAL [6]')
        reserve_asset = Token
        useAsCollateral = 0
        lending_pool.setUserUseReserveAsCollateral( reserve_asset, useAsCollateral, {"from": account})
        
        c1,d1,b1,LT,LTV,H = get_borrowable_data(lending_pool, account, False)
        eth_print(c1 ,b1 ,d1 , Token, eth_usd, eth_asset)

    #---------------------------- GET ASSET RESERVE DATA
    if 7 in OPTIONS:
        print('\n---- GET RESERVE DATA [7]')
        reserve_asset  =  Token
        config = lending_pool.getReserveData(reserve_asset.address)

        rate_names = ['liquidityIndex', 'variableBorrowIndex',
                    'currentLiquidityRate', 'currentStableBorrowRate',
                    'currentVariableBorrowRate']

        print(f'{reserve_asset.symbol()}:')
        for name, value in config.items():
            if name in rate_names:
                value_in_ether = float(value) * 1e-18
                print(f'    {name} : %{value*1e-36} ')
            elif isinstance(value, convert.datatypes.EthAddress):
                print(f'    {name} : {value}')
            else:
                print(f'    {name} : {value}.')

    #---------------------------- GET RESERVE LIST/ USER CONFIGURATION
    if 8 in OPTIONS:
        print('\n---- RESERVE LIST [8]')
        # generate active reserve list
        reserve_list = lending_pool.getReservesList()
        reserve_symb_list = []
    
        for token in reserve_list:
            tok_contract = interface.IERC20(token)
            symb = tok_contract.symbol()
            #print(f'    {symb}   ')
            reserve_symb_list.append(symb)
        
        # for each asset in the above list, will return bits representing 
        # if it is used as collateral and if it is borrowed, respectively.
        user_config = lending_pool.getUserConfiguration(account.address)
        print(f'\n   user_config : {user_config}')
        user_bitmask = format(user_config[0], "016b") 
        c_list, b_list = bitmask_user_config(user_bitmask, reserve_symb_list)

    #--------------------------- GET ASSET CONFIGURATION
    if 9 in OPTIONS:
        print('\n ---- GET ASSET CONFIGURATION [9]:')
        # get LTV, liquidation threshhold, see if reserve is active or frozen, etc.
        config_list, config_dict = get_asset_configuration(lending_pool, Token, True)

    #---------------------------- GET DEBT AND INCOME
    if 10 in OPTIONS:
        print('\n---- GET ASSET DEBT/ INCOME [10]')
        debt_asset = Token
        debt = lending_pool.getReserveNormalizedVariableDebt(debt_asset.address)*1e-27
        print(f'\n    {debt_asset.symbol()} debt: {debt} ray, {type(debt)}')
        
        income_asset = Token
        income = lending_pool.getReserveNormalizedIncome(income_asset.address)*1e-27
        print(f'    {debt_asset.symbol()} income: {income} ray, {type(income)}')

    # calculated change in borrow amount
    c2, d2, b2, LT, LTV, H = get_borrowable_data(lending_pool, account, False)
    Δb = b2-b1 ; per = Δb/b1
    Δc = c2-c1 ; per = Δc/c1
    Δd = d2-d1 ; per = Δd/d1
    #eth_print(c2,b2,d2, asset, eth_usd, eth_asset)

    #---------------------------- LIQUIDATE      ****** !!! not working yet !!!
  
    if 11 in OPTIONS:
        print('\n---- LIQUIDATE [11]')
        rateMode = 2     # select rate mode; 1=stable, 2=variable
        per      = 0.1   # enter percentage of debt to be repaid.

        print(f'\n   LTV: {LTV}')

        # set debt token
        if rateMode == 1:
            debt_token = sToken
        if rateMode == 2:
            debt_token = vToken
        
        debt_bal = tok_bal(debt_token, account.address, True)
        
        collateralAcc   = EXPLORaccount
        debtResAddr     = lending_pool.address
        borrowerAddr    = account.address
        debtToCover     = debt_bal*0.2
        receiveAToken   = True

        # approve lending pool
        approve_tx = approve_erc20(collateralAcc, debtToCover, lending_pool.address, Token)

        print(f'    liquidating {debtToCover*1e-18} {debt_token.symbol()}')
        lending_pool.liquidationCall(collateralAcc.address, debtResAddr, borrowerAddr, 
                        debtToCover, receiveAToken, {"from": collateralAcc.address})

def main():
    if NETWORK in LIVE_ENVS:
        input('\n on LIVE netowrk. Proceed with transactions?')
        network.disconnect()
    getTokens()
    print('\n===========================================\n')
