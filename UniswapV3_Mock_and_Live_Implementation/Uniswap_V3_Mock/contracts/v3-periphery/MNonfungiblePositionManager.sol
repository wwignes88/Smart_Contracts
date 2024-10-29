// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

 
// my contracts
import '@v3PeripheryMOCKS/base/MLiquidityManager.sol'; 
import '@v3CoreMOCKS/MUniswapV3Pool.sol';
import '@v3PeripheryMOCKS/MNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/interfaces/IMNonfungiblePositionManager.sol';
import '@v3PeripheryMOCKS/interfaces/IMNonfungiblePositionManagerII.sol';
import '@v3PeripheryMOCKS/libraries/MTransferHelper.sol';

// uniswap
import '@uniswap/v3-core/contracts/libraries/FixedPoint128.sol';
import '@uniswap/v3-core/contracts/libraries/FullMath.sol';
import '@uniswap/v3-periphery/contracts/interfaces/INonfungibleTokenPositionDescriptor.sol';
import '@uniswap/v3-periphery/contracts/libraries/PositionKey.sol';
// [LiquidityManagement mocked]
//import '@uniswap/v3-periphery/contracts/base/PeripheryImmutableState.sol'; 
import '@uniswap/v3-periphery/contracts/base/Multicall.sol'; 
import '@uniswap/v3-periphery/contracts/base/ERC721Permit.sol';
import '@uniswap/v3-periphery/contracts/base/PeripheryValidation.sol';
import '@uniswap/v3-periphery/contracts/base/SelfPermit.sol';

/// @title NFT positions
/// @notice Wraps Uniswap V3 positions in the ERC721 non-fungible token interface
contract MNonfungiblePositionManager is
    IMNonfungiblePositionManager, 
    Multicall,
    ERC721Permit,
    PeripheryValidation,
    SelfPermit
{

    // VARIABLES
        uint176 private _nextId = 1;
        /// @dev The ID of the next pool that is used for the first time. Skips 0
        address private immutable _tokenDescriptor;

    // constructor
    IMNonfungiblePositionManagerII public immutable NPManagerII;  
    constructor(
        IMNonfungiblePositionManagerII _NPManagerII,
        address _tokenDescriptor_
    ) ERC721Permit('Uniswap V3 Positions NFT-V1', 'UNI-V3-POS', '1') 

      {
        _tokenDescriptor = _tokenDescriptor_;
        NPManagerII = _NPManagerII;
    }
    struct MintCallbackData_ {
        MPoolAddress.PoolKey poolKey;
        address payer;
    }

    //* ommitted: checkDeadline(params.deadline)
    function mint(MintParams calldata params, int8 option)
        external
        payable
        override
        returns (
            uint256 tokenId,
            uint128 liquidity,
            uint256 amount0,
            uint256 amount1
        )
     {
        IUniswapV3Pool pool;
        // *recipient of liquidity is NPManagerII so that it can increase/decrease/collect liquidity positions 
        // once they are minted.
        (liquidity, amount0, amount1, pool) = NPManagerII.ERC721Manager_Add_Liquidity(
            AddLiquidityParams({
                token0: params.token0,
                token1: params.token1,
                fee   : params.fee,
                recipient: address(NPManagerII),
                tickLower: params.tickLower,
                tickUpper: params.tickUpper,
                amount0Desired: params.amount0Desired,
                amount1Desired: params.amount1Desired,
                Payer         : msg.sender
            }), 
            option
        );
        
        if (option < 50){
            tokenId = _nextId++;
            // recipient = MLMiner
            _mint(params.recipient, (tokenId )); 
            if (option == 10){ revert("[Nonfung] mapping key..");}
            require(tokenId != 0, '[Nonfung :: pos] Invalid token ID');
            NPManagerII.mapPoolKey(params, tokenId, liquidity, option, pool);
        }
    }

    modifier isAuthorizedForToken(uint256 tokenId) {
        require(_isApprovedOrOwner(msg.sender, tokenId), 'Not approved');
        _;
    }
    
    function burn(uint256 tokenId) external payable override isAuthorizedForToken(tokenId)  {
        (, , , , , , , uint128 liquidity, , , uint128 tokensOwed0, uint128 tokensOwed1) =
            NPManagerII.positions(tokenId);
        require(liquidity == 0 && tokensOwed0 == 0 && tokensOwed1 == 0, 'Not cleared');
        NPManagerII.deletePosition(tokenId);
        _burn(tokenId);
    }

    function _getAndIncrementNonce(uint256 tokenId) internal override returns (uint256) {
        return NPManagerII._getAndIncrementNonceII( tokenId);
    }
    
    /* not implemented :: see IPeripheryPayments
        function unwrapWETH9(uint256 amountMinimum, address recipient) external override payable{
        }
        function refundETH() external override payable;
        function sweepToken(
            address token,
            uint256 amountMinimum,
            address recipient
        ) external override payable;
    */
}