// SPDX-License-Identifier: GPL-2.0-or-later
pragma solidity 0.7.6;
pragma abicoder v2;

/*   see ComputeAddress.sol.
    this contract is used to calculate the value of POOL_INIT_CODE_HASH.  */
import "@v3CoreMOCKS/MUniswapV3PoolII.sol";

library PoolIIHashGenerator { 

   function getPoolCreationCodeII() public view returns (bytes memory) {
    return type(MUniswapV3PoolII).creationCode;
   }

    function hashPoolCodeII() public view returns (bytes32 pool_hash){
        bytes memory creation_code = getPoolCreationCodeII();
        pool_hash = keccak256(creation_code);
    }


}