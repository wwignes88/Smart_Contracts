1) These are not production ready codes, least not in the sense that they've been analyzed for seurity purposes.

2) Chainlinks newly released CCIP protocol is, at the time of posting, only available on testnets.

3) The VRF_Mock_with_Oracle project has a readme pdf file which should be consulted for those who are new to eth-brownie. This project makes use of 'EventWatcher' which listens for emitted events. 

For an implementation of the live VRFCoordinatorV2.sol contract see 'LIve Requests' folder. Like the mock events are listened for, but here we get more precise in the sense we calculate the requestId then filer emitted events according to this requestId so that we can see when our requests are fulfilled. The cost of requesting randomness is also calculated.

* something I failed to mention in the aforementioned readme pdf file (for the mock project) is that EventWatcher works on alchemy but you may have problems using it with infura. This I believe relates to https vs. wss (websocket) node provider addresses. Alchemy supports testing on sepolia for free, but it will require an upgraded membership to test on the polygon-mumbai network. The second project 'AAVETrades' attempts to make use of EventWatcher to listen for emitted events during a flashLoan, but I ran into problems here and opted not to troubleshoot for the time-being. See notes in AAVETrades/scripts/FlashLoan/flashLoan.py file for a detailed explanation.
