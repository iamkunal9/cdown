# cdown ~ Smart Contract Source Code Downloader

A Python tool for downloading verified smart contract source code from Etherscan API. This tool can download single contracts or recursively download proxy contracts and their implementations.

## Features

- 📥 Download verified smart contract source code from Etherscan
- 🔄 Recursive proxy contract detection and implementation downloading
- 📄 Save ABI (Application Binary Interface) files
- 📊 Save contract metadata with filtering options
- 🌐 Support for multiple EVM chains via chain ID
- 🚫 Cycle detection to prevent infinite loops when downloading proxy chains
- 📁 Organized output with contract-specific folders

## Installation

### Prerequisites

- Python 3.7+
- Etherscan API key

### Setup

1. Clone or download this repository
2. Install required dependencies:
   ```bash
   pip install requests
   ```

3. Get your Etherscan API key:
   - Visit [Etherscan.io](https://etherscan.io/)
   - Create an account and generate an API key
   - Copy your API key

4. Configure your API key:
   - Open `main.py`
   - Replace the empty string on line 10 with your API key:
   ```python
   API_KEY = "your_etherscan_api_key_here"
   ```

## Usage

### Command Line Interface

The main script provides a comprehensive CLI for downloading contract source code:

```bash
python main.py -a <CONTRACT_ADDRESS> -c <CHAIN_ID> [OPTIONS]
```

#### Required Arguments

- `-a, --address`: Contract address (0x...)
- `-c, --chain`: EVM chain ID (e.g., 1 for Ethereum mainnet, 8453 for Base)

#### Optional Arguments

- `-o, --out`: Output directory (default: current directory)
- `-r, --recursive`: Download proxy implementation contracts recursively
- `-b, --download-abi`: Save ABI JSON file
- `-m, --download-metadata`: Save full contract metadata JSON
- `--include-metadata-keys`: Comma-separated keys to include in metadata
- `--exclude-metadata-keys`: Comma-separated keys to exclude from metadata

#### Examples

**Download a single contract:**
```bash
python main.py -a 0xA0b86a33E6441b8C4C8C0d4b0c8b0c8b0c8b0c8b0 -c 1
```

**Download with ABI and metadata:**
```bash
python main.py -a 0xA0b86a33E6441b8C4C8C0d4b0c8b0c8b0c8b0c8b0 -c 1 -b -m
```

**Recursively download proxy contracts:**
```bash
python main.py -a 0xA0b86a33E6441b8C4C8C0d4b0c8b0c8b0c8b0c8b0 -c 1 -r -b -m
```

**Download with filtered metadata:**
```bash
python main.py -a 0xA0b86a33E6441b8C4C8C0d4b0c8b0c8b0c8b0c8b0 -c 1 -m --exclude-metadata-keys "SourceCode,ABI"
```

### Programmatic Usage

You can also use the functions directly in your Python code:

```python
from main import download_contract_source, download_contract_source_recursive

# Download single contract
download_contract_source(
    address="0xA0b86a33E6441b8C4C8C0d4b0c8b0c8b0c8b0c8b0",
    chainid=1,  # Ethereum mainnet
    outdir="contracts",
    save_abi=True,
    save_metadata=True
)

# Download with recursive proxy detection
download_contract_source_recursive(
    address="0xA0b86a33E6441b8C4C8C0d4b0c8b0c8b0c8b0c8b0",
    chainid=1,
    outdir="contracts",
    save_abi=True,
    save_metadata=True,
    exclude_metadata_keys={"SourceCode"}
)
```

### Batch Processing

The `test.py` file demonstrates how to download multiple contracts in batch:

```python
from main import download_contract_source_recursive
import time

contractAddresses = [
    "0xContractAddress1",
    "0xContractAddress2",
    # Add more addresses...
]

for address in contractAddresses:
    download_contract_source_recursive(
        address=address,
        chainid=8453,  # Base chain
        outdir="output",
        save_metadata=True,
        exclude_metadata_keys={"SourceCode"}
    )
    print(f"Downloaded source code for contract: {address}")
    time.sleep(2)  # Rate limiting
```

## Output Structure

The tool creates organized folders for each downloaded contract:

```
output/
├── ContractName-0xaddress/
│   ├── ContractName.sol          # Main contract file
│   ├── abi.json                  # ABI file (if -b flag used)
│   └── contract_metadata.json    # Metadata file (if -m flag used)
└── Implementation-0ximplementation/
    ├── Implementation.sol
    ├── abi.json
    └── contract_metadata.json
```

## Supported Chains

The tool supports any EVM-compatible chain with an Etherscan-compatible API. Common chain IDs:

- **1**: Ethereum Mainnet
- **8453**: Base
- **10**: Optimism
- **42161**: Arbitrum One
- **137**: Polygon
- **56**: BSC (Binance Smart Chain)

## API Rate Limits

- Etherscan has rate limits for API calls
- The tool includes a 2-second delay in the batch example to respect rate limits
- Consider upgrading to a paid Etherscan plan for higher rate limits

## Error Handling

The tool handles various error conditions:

- Invalid API keys
- Non-verified contracts
- Network timeouts
- Invalid contract addresses
- Circular proxy references

## Dependencies

- `requests`: HTTP library for API calls
- `pathlib`: File system operations
- `argparse`: Command-line argument parsing
- `json`: JSON processing
- `typing`: Type hints

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is open source. Please check the license file for details.

## Disclaimer

This tool is for educational and research purposes. Always verify downloaded source code and respect the terms of service of Etherscan and other blockchain explorers.

## Troubleshooting

### Common Issues

1. **"API key not set" error**: Make sure you've set your Etherscan API key in `main.py`
2. **"Contract is not verified" error**: The contract address may not be verified on Etherscan
3. **Rate limit errors**: Add delays between requests or upgrade your Etherscan plan
4. **Network errors**: Check your internet connection and try again

### Getting Help

If you encounter issues:

1. Check that your API key is valid and has sufficient quota
2. Verify the contract address is correct and verified
3. Ensure the chain ID corresponds to the correct network
4. Check the Etherscan API status
