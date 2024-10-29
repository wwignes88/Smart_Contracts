// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

/*   see ComputeAddress.sol.
    this contract is used to calculate the value of POOL_INIT_CODE_HASH.  */
import "@v3CoreMOCKS/MUniswapV3Pool.sol";

library PoolHashGenerator { 

   function getPoolCreationCode() public view returns (bytes memory) {
    return type(MUniswapV3Pool).creationCode;
   }

    function hashPoolCode() public view returns (bytes32 pool_hash){
        bytes memory creation_code = getPoolCreationCode();
        pool_hash = keccak256(creation_code);
    }


}