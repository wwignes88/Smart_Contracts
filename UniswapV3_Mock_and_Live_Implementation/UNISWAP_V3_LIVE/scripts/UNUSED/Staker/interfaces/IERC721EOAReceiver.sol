// SPDX-License-Identifier: MIT

pragma solidity ^0.7.0;

/**
 * @title ERC721 token receiver interface
 * @dev Interface for any contract that wants to support safeTransfers
 * from ERC721 asset contracts.
 */
interface IERC721EOAReceiver {
    /**
     * @dev Whenever an {IERC721} `tokenId` token is transferred to this contract via 
     * {IERC721-safeTransferFrom}
     * by `operator` from `from`, this function is called.
     *
     * It must return its Solidity selector to confirm the token transfer.
     * If any other value is returned or the interface is not implemented by the recipient, 
     * the transfer will be reverted.
     *
     * The selector can be obtained in Solidity with `IERC721.onERC721Received_to_EOA.selector`.
     */
     
    /// @notice  use for transfering tokens to to an EOA account, but will trigger
    // callback in some third-party contract who has implemented IERC721EOAReceiver
    // onERC721Received_to_EOA function.

    /// @param mediator The third-party contract who has implemented IERC721EOAReceiver 
    /// @param from current ERC721 token owner
    /// @param to EOA account to send token to
    function onERC721Received_to_EOA( 
            address from,
            address to,
            address mediator,
            uint256 tokenId,
            bytes memory _data
        ) external returns (bool);
}
