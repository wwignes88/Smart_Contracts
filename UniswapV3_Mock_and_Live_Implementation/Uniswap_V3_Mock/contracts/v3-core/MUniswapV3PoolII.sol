// SPDX-License-Identifier: BUSL-1.1
pragma solidity 0.7.6; 
pragma abicoder v2;

//import '@v3PeripheryMOCKS/libraries/MPoolAddress.sol';
// 
import '@v3CoreMOCKS/interfaces/IUniswapV3Pool.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3PoolII.sol';
import '@v3CoreMOCKS/interfaces/IUniswapV3PoolIIDeployer.sol';

import '@uniswap/v3-core/contracts/libraries/Position.sol';
import '@uniswap/v3-core/contracts/libraries/TransferHelper.sol';
import '@uniswap/v3-core/contracts/libraries/LowGasSafeMath.sol';
import '@uniswap/v3-core/contracts/libraries/SafeCast.sol';
import '@uniswap/v3-core/contracts/interfaces/callback/IUniswapV3MintCallback.sol';
import '@uniswap/v3-core/contracts/interfaces/IERC20Minimal.sol';

contract MUniswapV3PoolII is IUniswapV3PoolII{
        using LowGasSafeMath for uint256;
        using LowGasSafeMath for int256;
        using SafeCast for uint256;
        using SafeCast for int256;


        address public immutable  factoryII;
        address public immutable  token0II;
        address public immutable  token1II;
        uint24 public immutable  feeII;
        int24 public immutable  tickSpacingII;

    constructor() {
        int24 _tickSpacingII;
        (factoryII, token0II, token1II, feeII, _tickSpacingII) = IUniswapV3PoolIIDeployer(msg.sender).parametersII();
        tickSpacingII = _tickSpacingII;
    }

    function toInt128(int256 y) internal pure returns (int128 z) {
        require((z = int128(y)) == y);
    }

    function Tokenbalance(address token, address pool) internal view returns (uint256) {
        (bool success, bytes memory data) =
            token.staticcall(abi.encodeWithSelector(IERC20Minimal.balanceOf.selector, pool));
        require(success, "Stat");
        require(data.length >= 32, "bal :: d");
        return abi.decode(data, (uint256));
    }

    struct ModifyPositionParams {
        // the address that owns the position
        address owner;
        // the lower and upper tick of the position
        int24 tickLower;
        int24 tickUpper;
        // any change in liquidity
        int128 liquidityDelta;
    }
    
    /// @dev noDelegateCall is applied indirectly via _modifyPosition
    function mintII(
        IUniswapV3Pool pool,
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount,
        bytes memory data,
        int8 option
    ) external override returns (uint256 amount0, uint256 amount1) {
        require(amount > 0, " --- mint L = 0 --- ");
        (, int256 amount0Int, int256 amount1Int) =
            pool._modifyPosition(
                    recipient,
                    tickLower,
                    tickUpper,
                    toInt128(int256(amount)),
                    option
            );

        address pool_address = address(pool);
        amount0 = uint256(amount0Int);
        amount1 = uint256(amount1Int);

        address tok0 = pool.token0();
        address tok1 = pool.token1();

        uint256 balance0Before;
        uint256 balance1Before;
        if (amount0 > 0) balance0Before = Tokenbalance(tok0, pool_address);
        if (amount1 > 0) balance1Before = Tokenbalance(tok1, pool_address);
        if (option == 7){revert("entering mint callback...");}
        // * msg.sender  _changed to address(this) =  NonfungiblePositionManager for callback
        IUniswapV3MintCallback(msg.sender).uniswapV3MintCallback(amount0, amount1, data);
        //  address(this) = MNonfungiblePoitionManager
        if (option<50){ 
            if (amount0 > 0) require(balance0Before.add(amount0) <= Tokenbalance(tok0, pool_address), 'M0');
            if (amount1 > 0) require(balance1Before.add(amount1) <= Tokenbalance(tok1, pool_address), 'M1');
        }
        
    }

    // lock missing
    /// @dev noDelegateCall is applied indirectly via _modifyPosition
    function burnII(
        IUniswapV3Pool pool,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount,
        int8 option
    ) external override returns ( uint256 amount0, uint256 amount1) {
        // *note that MNonfungiblePPositionManager.sol minted with this contract address as the owner.
        // so we can here use owner=msg.sender.
        (Position.Info memory position, int256 amount0Int, int256 amount1Int) =
            pool._modifyPosition(
                    msg.sender, 
                    tickLower,
                    tickUpper,
                    -int256(amount).toInt128(),
                    option
            );
        amount0 = uint256(-amount0Int);
        amount1 = uint256(-amount1Int);

        if (amount0 > 0 || amount1 > 0) {
                pool.modifyTokensOwed(
                    msg.sender,
                    tickLower,
                    tickUpper,
                    uint128(amount0),
                    uint128(amount1)
            );
        }

        emit Burn(msg.sender, tickLower, tickUpper, amount, amount0, amount1);
    }

    // lock missing
    function collectII(
        IUniswapV3Pool pool,
        address recipient,
        int24 tickLower,
        int24 tickUpper,
        uint128 amount0Requested,
        uint128 amount1Requested
    ) external override  returns (uint128 amount0, uint128 amount1) {
        // we don't need to checkTicks here, because invalid positions will never have non-zero tokensOwed{0,1}
        Position.Info memory position = pool.getPoolPosition(msg.sender, tickLower, tickUpper);


        amount0 = amount0Requested > position.tokensOwed0 ? position.tokensOwed0 : amount0Requested;
        amount1 = amount1Requested > position.tokensOwed1 ? position.tokensOwed1 : amount1Requested;

        if (amount0 > 0) {
            pool.modifyTokensOwed(
                msg.sender,
                tickLower,
                tickUpper,
                -amount0,
                0
            );
            pool.poolII_transfer(true, recipient, amount0);
        }
        if (amount1 > 0) {
            pool.modifyTokensOwed(
                msg.sender,
                tickLower,
                tickUpper,
                0,
                -amount1
            );
            pool.poolII_transfer(false, recipient, amount1);
        }

        emit Collect(msg.sender, recipient, tickLower, tickUpper, amount0, amount1);
    }




}