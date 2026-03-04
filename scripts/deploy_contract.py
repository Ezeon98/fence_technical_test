"""Compile and deploy CovenantRegistry to local Anvil."""

import json
from pathlib import Path

from solcx import compile_source, install_solc
from web3 import Web3

from app.infrastructure.settings import get_settings


def deploy() -> None:
    """Compile and deploy contract, then persist ABI and address files."""
    settings = get_settings()
    project_root = Path(__file__).resolve().parents[1]
    contract_path = project_root / "contracts" / "CovenantRegistry.sol"

    source = contract_path.read_text(encoding="utf-8")
    install_solc("0.8.24")
    compiled = compile_source(
        source,
        output_values=["abi", "bin"],
        solc_version="0.8.24",
    )
    _, contract_interface = compiled.popitem()

    web3 = Web3(Web3.HTTPProvider(settings.rpc_url))
    account = web3.eth.account.from_key(settings.deployer_private_key)

    contract = web3.eth.contract(
        abi=contract_interface["abi"],
        bytecode=contract_interface["bin"],
    )

    nonce = web3.eth.get_transaction_count(account.address)
    tx = contract.constructor().build_transaction(
        {
            "from": account.address,
            "nonce": nonce,
            "chainId": settings.chain_id,
        }
    )
    signed_tx = web3.eth.account.sign_transaction(
        tx,
        private_key=settings.deployer_private_key,
    )
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    address_file = project_root / "contracts" / "CovenantRegistry.address"
    address_file.write_text(receipt.contractAddress, encoding="utf-8")

    abi_file = project_root / "contracts" / "CovenantRegistry.abi.json"
    abi_file.write_text(
        json.dumps(contract_interface["abi"], indent=2),
        encoding="utf-8",
    )

    print("Contract deployed at:", receipt.contractAddress)


if __name__ == "__main__":
    deploy()
