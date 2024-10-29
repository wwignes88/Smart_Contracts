
LIVE_ENVS = ['avax-main', 'polygon-main', 'mainnet', 'etc' ]
TEST_ENVS = ['avax-test', 'polygon-test']
NETWORK_NAMES = {'avax-main': 'Avalanche',
                 'avax-test': 'Avalanche', 
                 'polygon-main': 'Polygon',
                 'polygon-test': 'Polygon',
                 'mainnet' : 'Ethereum'}
aTOKEN_ENVS = ['polygon-test', 'polygon-main','avax-main']
NETWORK_SYMS = {'avax-main': 'avax_usd',
                'avax-test': 'avax_usd',
                'polygon-main': 'matic_usd',
                'polygon-test': 'matic_usd'}
AAVE_TOKEN = {0 : 'aToken',
              1 : 'sToken',
              2 : 'aWeth',
              3 : 'sWeth'}


def getNetworksFolders():
    return ['Avalanche', 'Polygon']

import datetime as D
def START_TIMES(str_):
    # returns step size h for roundID (see getRoundData in helpful_scripts.py)
    # and dateTime of selected start-date, e.g. 3 days ago, etc.
    now = D.datetime.now()
    startTimes =   {'1_day'  : [1,    now - D.timedelta(days   =  1)],
                    '3_day'  : [2,    now - D.timedelta(days   =  3)],
                    '1_week' : [3,    now - D.timedelta(weeks  =  1)],
                    '3_week' : [15,   now - D.timedelta(weeks  =  4)],
                    '12_week': [25,   now - D.timedelta(weeks  = 12)],
                    '26_week': [100,  now - D.timedelta(weeks  = 26)],
                    '52_week': [250,  now - D.timedelta(weeks  = 52)]}
    if str_ != None:
        return startTimes[str_]
    if str_ == None:
        return startTimes


# *see https://data.chain.link/

#      =====================
#            AVALANCHE 
#      =====================

AVAX      = {'symb': 'avax',
             'network' : 'Avalanche',
             'btc_usd' : '0x2779d32d5166baaa2b2b658333ba7e6ec0c65743',
             'avax_usd': '0x0a77230d17318075983913bc2145db16c7366156',
             "link_usd": '0x49ccd9ca821efeab2b98c60dc60f518e765ede9a',
             "eth_usd" : '0x976b3d034e162d8bd72d6b9c989d545b839003b0',
             "dai_usd" : '0x51d7180eda2260cc4f6e4eebb82fef5c3c2b8300',
             "aave_usd": '0x3ca13391e9fb38a75330fb28f8cc2eb3d9ceceed',
             "frax_usd": '0xbba56ef1565354217a3353a466edb82e8f25b08e',
             "sushi_usd":'0x449a373a090d8a1e5f74c63ef831ceff39e94563',
             # available on Metamask:
             "avax_usd": '0x0a77230d17318075983913bc2145db16c7366156',
             "usdc_usd": "0xf096872672f44d6eba71458d74fe67f9a77a23b9"}



#      =====================
#            POLYGON 
#      =====================



POLYGON = {'symb'     : 'matic',
           'network'  : 'Polygon',
           'btc_usd'  : '0xc907e116054ad103354f2d350fd2514433d57f6f',
           'eth_usd'  : '0xf9680d99d6c9589e2a93a78a04a279e509205945',
           'link_usd' : '0xd9ffdb71ebe7496cc440152d43986aae0ab76665',
           'matic_usd': '0xab594600376ec9fd91f8e885dadf0ce036862de0',
           'aave_usd' : '0x72484b12719e23115761d5da1646945632979bb6',
           'ape_usd'  : '0x2ac3f3bfac8fc9094bc3f0f9041a51375235b992',
           'bat_usd'  : '0x2346ce62bd732c62618944e51cbfa09d985d86d2',
           'bnb_usd'  : '0x82a6c4af830caa6c97bb504425f6a66165c2c26e',
           'dai_usd'  : '0x4746dec9e833a82ec7c2c1356372ccf2cfcd2f3d',
           # available on Metamask:
           "mana_usd" : '0xa1cbf3fe43bc3501e3fc4b573e822c70e76a7512',
           "matic_usd": '0xab594600376ec9fd91f8e885dadf0ce036862de0',
           "usdc_usd" : '0xfe4a8cc5b5b2366c1b58bea3858e81843581b2f7'
           }





#!!!!!! problem with v3 aggregator
# mainnet [Ethereum] network
ETH      = {'symb'    : 'eth',
            'network' : 'Ethereum',
            'avax_usd': '0xff3eeb22b5e3de6e705b44749c2559d704923fd7',
            'btc_usd' : '0xf4030086522a5beea4988f8ca5b36dbc97bee88c',
            'eth_usd' : '0x5f4ec3df9cbd43714fe2740f5e3616155c5b8419',
            # available on Metamask:
            'aave_usd' : '',
            'ape_uad'  : '',
            'bat_usd'  : '',
            #'busd_usd'  : '',
            'link_usd': '0x2c1d072e956affc0d435cb7ac38ef18d24d9127c'}

