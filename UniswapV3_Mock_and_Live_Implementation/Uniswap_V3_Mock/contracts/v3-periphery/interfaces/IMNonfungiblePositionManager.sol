// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity >=0.7.5;
pragma abicoder v2;

import '@v3PeripheryMOCKS/interfaces/IStructs.sol'; 
import '@openzeppelin/contracts/token/ERC721/IERC721Metadata.sol';
import '@openzeppelin/contracts/token/ERC721/IERC721Enumerable.sol';


import '@uniswap/v3-periphery/contracts/interfaces/IERC721Permit.sol'; 
import '@uniswap/v3-periphery/contracts/interfaces/IPeripheryPayments.sol';
//import '@uniswap/v3-periphery/contracts/interfaces/IPeripheryImmutableState.sol';

/// @title Non-fungible token for positions
/// @notice Wraps Uniswap V3 positions in a non-fungible token interface which allows for them to be transferred
/// and authorized.
interface IMNonfungiblePositionManager is
    IERC721Metadata,
    IERC721Enumerable,
    IERC721Permit,
    IStructs
{

    function mint(MintParams calldata params, int8 revert_option)
        external
        payable
        returns (
            uint256 tokenId,
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1
        );

    //
    function burn(uint256 tokenId) external payable;

    // *not implemented :: see IPeripheryPayments


}