from brownie import network, config

myAccount = "0x6dFa1b0235f1150008B23B2D918F87D4775fBba9"
# list of token addresses
contractList = [config["networks"][network.show_active()]['weth'],
             config["networks"][network.show_active()]['sand'],
             config["networks"][network.show_active()]['link'],
             config["networks"][network.show_active()]['MNonfungiblePositionManager'],
             config["networks"][network.show_active()]['MNonfungiblePositionManagerII'],
             config["networks"][network.show_active()]['MSwapRouter'],
             config["networks"][network.show_active()]['MliquidityMiner'],
             config["networks"][network.show_active()]['MSwapper'],
             myAccount
             ]
# map addresses to token symbol (see BronieFuncs.py :: callbackFunc)
# this is used for event watching callbacks in which calling token.symbol()
# does not work well.
contractToSym = {
            contractList[0]: 'WETH',
            contractList[1]: "SAND",
            contractList[2]: "LINK",
            contractList[3]: "ERC721 Manager",
            contractList[4]: "ERC721 Manager II",
            contractList[5]: "ROUTER",
            contractList[6]: "L MINER",
            contractList[7]: "SWAPPER",
            contractList[8]: "ME"
            }

TICK_SPACINGS = {
    500 : 10,
    3000 : 60
}

LIVE_ENVS = ['avax-main', 'polygon-main', 'mainnet', 'etc' ]
TEST_ENVS = ['avax-test', 'polygon-test']

#===================== PRICE FEED ADDRESSES

AMOY =  {'symb'           : 'matic',
           'network_folder' : 'Polygon',
           # chainlink rates. from: https://docs.chain.link/data-feeds/price-feeds/addresses
           'native_usd': '0x001382149eBa3441043c1c66972b4772963f5D43', # matic_usd
           'btc_usd'   : '0xe7656e23fE8077D438aEfbec2fAbDf2D8e070C4f',
           'dai_usd'   : '0x1896522f28bF5912dbA483AC38D7eE4c920fDB6E',
           'WETH_usd'  : '0xF0d50568e3A7e8259E16663972b11910F89BD8e7',
           'eur_usd'   : '0xa73B1C149CB4a0bf27e36dE347CBcfbe88F65DB2',
           'link_matic': '0x408D97c89c141e60872C0835e18Dd1E670CD8781',
           'LINK_usd'  : '0xc2e2848e28B9fE430Ab44F55a8437a33802a219C',
           'SAND_usd'  : '0xeA8C8E97681863FF3cbb685e3854461976EBd895',
           'sol_usd'   : '0xF8e2648F3F157D972198479D5C7f0D721657Af67',
           'usdc_usd'  : '0x1b8739bB4CdF0089d07097A9Ae5Bd274b29C6F16',
           'usdt_usd'  : '0x3aC23DcB4eCfcBd24579e1f34542524d0E4eDeA8'
           }

NETWORK_TO_RATE_DICT = {'polygon-amoy': AMOY}