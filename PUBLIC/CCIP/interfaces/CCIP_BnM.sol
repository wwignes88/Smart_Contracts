// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

interface CCIPBnM_Interface {
    // Events
    event Approval(address indexed owner, address indexed spender, uint256 value);
    event BurnAccessGranted(address indexed burner);
    event BurnAccessRevoked(address indexed burner);
    event MintAccessGranted(address indexed minter);
    event MintAccessRevoked(address indexed minter);
    event OwnershipTransferRequested(address indexed from, address indexed to);
    event OwnershipTransferred(address indexed from, address indexed to);
    event Transfer(address indexed from, address indexed to, uint256 value);
    event Transfer(address indexed from, address indexed to, uint256 value, bytes data);

    // Functions
    function acceptOwnership() external;
    function allowance(address owner, address spender) external view returns (uint256);
    function approve(address spender, uint256 amount) external returns (bool);
    function balanceOf(address account) external view returns (uint256);
    function burn(uint256 amount) external;
    function burnFrom(address account, uint256 amount) external;
    function decimals() external view returns (uint8);
    function decreaseAllowance(address spender, uint256 subtractedValue) external returns (bool);
    function decreaseApproval(address spender, uint256 subtractedValue) external returns (bool success);
    function drip(address to) external;
    function getBurners() external view returns (address[] memory);
    function getMinters() external view returns (address[] memory);
    function grantBurnRole(address burner) external;
    function grantMintAndBurnRoles(address burnAndMinter) external;
    function grantMintRole(address minter) external;
    function increaseAllowance(address spender, uint256 addedValue) external returns (bool);
    function increaseApproval(address spender, uint256 addedValue) external;
    function isBurner(address burner) external view returns (bool);
    function isMinter(address minter) external view returns (bool);
    function maxSupply() external view returns (uint256);
    function mint(address account, uint256 amount) external;
    function name() external view returns (string memory);
    function owner() external view returns (address);
    function revokeBurnRole(address burner) external;
    function revokeMintRole(address minter) external;
    function symbol() external view returns (string memory);
    function totalSupply() external view returns (uint256);
    function transfer(address to, uint256 amount) external returns (bool);
    function transferAndCall(address to, uint256 amount, bytes calldata data) external returns (bool success);
    function transferFrom(address from, address to, uint256 amount) external returns (bool);
}