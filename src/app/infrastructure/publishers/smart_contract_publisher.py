"""Smart contract publisher implementation."""

import json
from pathlib import Path

from web3 import Web3

from app.domain.ports.publisher import PublicationResult, Publisher
from app.domain.value_objects.covenant_report import CovenantReport
from app.infrastructure.hash.canonical_hash import effective_rate_to_bps
from app.infrastructure.settings import get_settings


class SmartContractPublisher(Publisher):
    """Publisher that writes immutable covenant evidence on-chain."""

    def __init__(self) -> None:
        """Initialize smart contract client from settings and ABI."""
        settings = get_settings()
        self._rpc_url = settings.rpc_url
        self._chain_id = settings.chain_id
        self._private_key = settings.deployer_private_key
        self._contract_address = settings.contract_address
        abi_path = Path("contracts/CovenantRegistry.abi.json")
        self._abi = json.loads(abi_path.read_text(encoding="utf-8"))

    def publish(self, report: CovenantReport) -> PublicationResult:
        """Publish covenant hash and key metrics to smart contract."""
        try:
            if not self._contract_address:
                return PublicationResult(
                    success=False,
                    reference=None,
                    error_message="Missing CONTRACT_ADDRESS.",
                )

            web3 = Web3(Web3.HTTPProvider(self._rpc_url))
            account = web3.eth.account.from_key(self._private_key)
            contract = web3.eth.contract(
                address=Web3.to_checksum_address(self._contract_address),
                abi=self._abi,
            )

            effective_rate_bps = effective_rate_to_bps(report.effective_rate)
            report_hash_bytes = Web3.to_bytes(hexstr=f"0x{report.report_hash}")

            nonce = web3.eth.get_transaction_count(account.address)
            transaction = contract.functions.publishCovenant(
                report.facility_id,
                effective_rate_bps,
                report_hash_bytes,
            ).build_transaction(
                {
                    "from": account.address,
                    "nonce": nonce,
                    "chainId": self._chain_id,
                }
            )
            signed = web3.eth.account.sign_transaction(
                transaction,
                private_key=self._private_key,
            )
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
            return PublicationResult(
                success=True,
                reference=receipt.transactionHash.hex(),
            )
        except Exception as error:
            return PublicationResult(
                success=False,
                reference=None,
                error_message=str(error),
            )
