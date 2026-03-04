// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

contract CovenantRegistry {
    struct Publication {
        string facilityId;
        uint16 effectiveRateBps;
        bytes32 reportHash;
        uint256 timestamp;
    }

    mapping(bytes32 => Publication) public publications;

    event CovenantPublished(
        string facilityId,
        uint16 effectiveRateBps,
        bytes32 reportHash,
        uint256 timestamp
    );

    function publishCovenant(
        string calldata facilityId,
        uint16 effectiveRateBps,
        bytes32 reportHash
    ) external {
        require(publications[reportHash].timestamp == 0, "Already published");

        publications[reportHash] = Publication({
            facilityId: facilityId,
            effectiveRateBps: effectiveRateBps,
            reportHash: reportHash,
            timestamp: block.timestamp
        });

        emit CovenantPublished(
            facilityId,
            effectiveRateBps,
            reportHash,
            block.timestamp
        );
    }
}
