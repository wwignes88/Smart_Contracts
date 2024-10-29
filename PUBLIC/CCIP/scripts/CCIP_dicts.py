


chain_selectors  = {"polygon-test": 12532609583862916517,
                    "sepolia": 16015286601757825753}
chain_to_network = {12532609583862916517: "polygon-test",
                    16015286601757825753: "sepolia"}

price_feeds = {'link_eth': '0x42585eD362B3f1BCa95c640FdFf35Ef899212734',
               'eth_usd' : '0x694AA1769357215DE4FAC081bf1f309aDC325306'}

Fee_Options = {0: "Native payment",
               1: "LINK payment"}

def get_chain(chain_id):
    return chain_to_network[chain_id]

def price_feed_address(str_):
    return price_feeds[str_]





