// An NFT Contract
// Where the tokenURI can be one of 3 different dogs
// Randomly selected

// SPDX-License-Identifier: MIT
pragma solidity 0.8.0;

import "node_modules/@chainlink/contracts/src/v0.8/interfaces/LinkTokenInterface.sol";
import "node_modules/@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "node_modules/@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "node_modules/@openzeppelin/contracts/utils/Strings.sol";



contract NFT is ERC721URIStorage{
    LinkTokenInterface internal immutable LINK;
    using Strings for uint256;
    uint256 public tokenCounter;
    string private _baseURIextended;
    mapping (uint256  => string) public _tokenURIs;
	  mapping(uint256 => address) TokenOwners;
    event requestedCollectible(uint256 TokenId_, address requester);


    constructor(address _linkToken) public 
    ERC721("Stright Jacket", "STR8")
    {
        tokenCounter = 0;
        LINK = LinkTokenInterface(_linkToken);
    }

//======================================================================
//====================== MY VRFConsumerBase funcs ======================

    receive() external payable {}
    fallback() external payable {}
    //function deposit() public payable {}

    function LINKBalance(address QueryAddress) public view returns (uint256 Balance_){
      Balance_ = LINK.balanceOf(QueryAddress);
    }

//======================================================================
//======================  NFT FUNCS   ==================================


	function createCollectible( address owner, string memory _tokenURI) public  {
        // token Id
        uint256 newTokenId = tokenCounter;
		    TokenOwners[newTokenId] = owner;
        _safeMint(owner, newTokenId);
        _setTokenURI( newTokenId, _tokenURI);
        tokenCounter = newTokenId + 1;
        requestedCollectible(newTokenId, owner);
    }
  function getTokenOwner(uint256 tokenId) public view returns (address){
    return TokenOwners[tokenId];
  }



// should have onlyOwner modifier!!
  function ChangeTokenURI(uint256 tokenId, string memory _tokenURI) public {
      _setTokenURI( tokenId, _tokenURI);
  }


  function GetTokenURI(uint256 tokenId) public view returns(string memory){
      return tokenURI( tokenId);
  }

}
