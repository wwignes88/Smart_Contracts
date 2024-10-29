// SPDX-License-Identifier: MIT
pragma solidity ^0.8.4;


contract VRFI{  

  struct Proof {
    bytes32 keyHash;
    uint256[2] pk;
    uint256[2] gamma;
    uint256 seed;
  } 
  uint256 internal constant VRF_RANDOM_OUTPUT_HASH_PREFIX = 3;

  constructor(){}
  function randomValueFromVRFProof(Proof memory proof, uint256 seed) internal pure returns (uint256 output) {
      verifyVRFProof(
        proof.pk,
        proof.gamma,
        seed
      );
      output = uint256(keccak256(abi.encode(VRF_RANDOM_OUTPUT_HASH_PREFIX, proof.gamma)));
    }

  function verifyVRFProof(
    uint256[2] memory pk,
    uint256[2] memory gamma,
    uint256 seed
  ) internal pure {
    unchecked {
      require(pk[0] == 0    , "pk == 0");
      require(gamma[0] == 0, "gamma == 0");
      require(seed == 0, "seed == 0");
    }
  }

  function implement() public pure returns(uint256 implementedNum){
    implementedNum = 44;
  }
}
