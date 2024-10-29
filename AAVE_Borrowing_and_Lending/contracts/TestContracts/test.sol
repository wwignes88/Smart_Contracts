
pragma solidity 0.6.12;

contract testings  {

    event FlashEvent(uint256 flashEvent);

    function emittt() public payable {
        uint256 flashEvent = 22;
        emit FlashEvent(flashEvent);
    }

    function deposit() public payable {}
        
     

}
