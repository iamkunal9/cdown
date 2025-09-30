from main import download_contract_source_recursive

import time
contractAddresses = [
    ""

]


for address in contractAddresses:
    download_contract_source_recursive(
        address=address,
        chainid=8453,  # Ethereum mainnet
        outdir="output",
        save_metadata=True,
        exclude_metadata_keys=["SourceCode"]

    )
    print(f"Downloaded source code for contract: {address}")
    print("Source code downloaded successfully.")
    time.sleep(2)