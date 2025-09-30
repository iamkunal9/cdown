from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Dict, Mapping, Optional, Set, Union
import requests

# === EDIT YOUR API KEY HERE ===
API_KEY = ""
# ==============================

_API_URL_TMPL = (
    "https://api.etherscan.io/v2/api"
    "?chainid={chainid}&module=contract&action=getsourcecode"
    "&address={address}&apikey={apikey}"
)

def is_single_file_contract(src: str) -> bool:
    txt = src.lstrip()
    return txt.startswith(("pragma", "//", "/*")) or txt.startswith("\r\n")

def _double_curly_wrapped(txt: str) -> bool:
    return txt.lstrip().startswith("{{") and txt.rstrip().endswith("}}")

def _json_or_none(txt: str) -> Optional[Union[dict, list]]:
    try:
        return json.loads(txt)
    except json.JSONDecodeError:
        return None

def _parse_source_code_object(blob: str) -> Union[dict, list]:
    txt = blob.strip()
    if _double_curly_wrapped(txt):
        txt = txt[1:-1].strip()
    parsed = _json_or_none(txt) or _json_or_none(txt[1:-1])
    if not parsed:
        raise RuntimeError("Could not decode SourceCode JSON bundle")
    if isinstance(parsed, dict) and "sources" in parsed:
        return parsed["sources"]
    return parsed

def _sources_to_map(parsed: Union[dict, list]) -> Dict[str, str]:
    if isinstance(parsed, dict):
        return {
            name: (meta["content"] if isinstance(meta, dict) and "content" in meta else meta)
            for name, meta in parsed.items()
        }
    if isinstance(parsed, list):
        out: Dict[str, str] = {}
        for name, meta in parsed:
            out[name] = meta["content"] if isinstance(meta, dict) else meta
        return out
    raise RuntimeError("Unexpected JSON structure inside SourceCode bundle")

def _write_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    try:
        shown = path.relative_to(Path.cwd())
    except ValueError:
        shown = path
    print(f"[+] {shown}")

def fetch_source(address: str, chainid: int, *, apikey: str = API_KEY) -> Mapping[str, str]:
    if not apikey or apikey == "YOUR_ETHERSCAN_V2_API_KEY":
        raise ValueError("API key not set at top of file")
    url = _API_URL_TMPL.format(chainid=chainid, address=address, apikey=apikey)
    try:
        resp = requests.get(url, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e
    data = resp.json()
    if data.get("status") != "1":
        raise RuntimeError(f"Etherscan error for {address}: {data.get('result', 'unknown')}")
    return data["result"][0]


def filter_metadata(
    metadata: Dict[str, Union[str, dict]],
    include_keys: Optional[Set[str]] = None,
    exclude_keys: Optional[Set[str]] = None,
) -> Dict[str, Union[str, dict]]:
    if include_keys is not None:
        return {k: v for k, v in metadata.items() if k in include_keys}
    if exclude_keys is not None:
        return {k: v for k, v in metadata.items() if k not in exclude_keys}
    return dict(metadata)


def write_sources(
    result: Mapping[str, str],
    outdir: Path,
    *,
    save_abi: bool = False,
    save_metadata: bool = False,
    include_metadata_keys: Optional[Set[str]] = None,
    exclude_metadata_keys: Optional[Set[str]] = None,
) -> None:
    src_blob = result.get("SourceCode", "")
    if not src_blob:
        raise RuntimeError("Contract is not verified or has no source")

    if is_single_file_contract(src_blob):
        fname = f"{result.get('ContractName') or 'Contract'}.sol"
        _write_file(outdir / fname, src_blob)
    else:
        parsed = _parse_source_code_object(src_blob)
        for i, (name, code) in enumerate(_sources_to_map(parsed).items(), 1):
            _write_file(outdir / (name or f"Contract_{i}.sol"), code)

    if save_abi:
        _write_file(outdir / "abi.json", result.get("ABI", ""))

    if save_metadata:
        filtered_metadata = filter_metadata(
            result,
            include_keys=include_metadata_keys,
            exclude_keys=exclude_metadata_keys,
        )
        _write_file(outdir / "contract_metadata.json", json.dumps(filtered_metadata, indent=2))


def download_contract_source(
    address: str,
    chainid: int,
    outdir: str | Path = ".",
    *,
    apikey: str = API_KEY,
    save_abi: bool = False,
    save_metadata: bool = False,
    include_metadata_keys: Optional[Set[str]] = None,
    exclude_metadata_keys: Optional[Set[str]] = None,
) -> None:
    result = fetch_source(address, chainid, apikey=apikey)
    address_folder = Path(outdir) / f"{result.get('ContractName', 'Contract')}-{address.lower()}"
    write_sources(
        result,
        address_folder,
        save_abi=save_abi,
        save_metadata=save_metadata,
        include_metadata_keys=include_metadata_keys,
        exclude_metadata_keys=exclude_metadata_keys,
    )


def download_contract_source_recursive(
    address: str,
    chainid: int,
    outdir: str | Path = ".",
    *,
    apikey: str = API_KEY,
    save_abi: bool = False,
    save_metadata: bool = False,
    include_metadata_keys: Optional[Set[str]] = None,
    exclude_metadata_keys: Optional[Set[str]] = None,
    _visited: Optional[Set[str]] = None,
) -> None:
    if _visited is None:
        _visited = set()

    address = address.lower()
    if address in _visited:
        print(f"[!] Already downloaded {address}, skipping to avoid cycle")
        return
    _visited.add(address)

    print(f"[=] Downloading contract {address} (chain {chainid})")

    result = fetch_source(address, chainid, apikey=apikey)
    base_dir = Path(outdir) / f"{result.get('ContractName', 'Contract')}-{address.lower()}"
    write_sources(
        result,
        base_dir,
        save_abi=save_abi,
        save_metadata=save_metadata,
        include_metadata_keys=include_metadata_keys,
        exclude_metadata_keys=exclude_metadata_keys,
    )

    is_proxy = result.get("Proxy") == "1"
    implementation = result.get("Implementation", "").lower()

    if (
        is_proxy
        and implementation
        and implementation != "0x0000000000000000000000000000000000000000"
    ):
        impl_dir = base_dir / f"implementation-{implementation}"
        print(f"[=] Detected proxy contract. Downloading implementation at {implementation}")
        download_contract_source_recursive(
            implementation,
            chainid,
            impl_dir,
            apikey=apikey,
            save_abi=save_abi,
            save_metadata=save_metadata,
            include_metadata_keys=include_metadata_keys,
            exclude_metadata_keys=exclude_metadata_keys,
            _visited=_visited,
        )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Download verified contract source; optionally recurse proxies and save ABI/metadata with metadata key filtering.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("-a", "--address", required=True, help="Contract address (0x...)")
    p.add_argument("-c", "--chain", dest="chainid", type=int, required=True, help="EVM chain ID")
    p.add_argument("-o", "--out", dest="outdir", default=".", help="Base output directory")
    p.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help="Download proxy implementation contracts recursively",
        default=False,
    )
    p.add_argument(
        "-b",
        "--download-abi",
        action="store_true",
        help="Save ABI JSON file (abi.json)",
        default=False,
    )
    p.add_argument(
        "-m",
        "--download-metadata",
        action="store_true",
        help="Save full contract metadata JSON (contract_metadata.json)",
        default=False,
    )
    group = p.add_mutually_exclusive_group()
    group.add_argument(
        "--include-metadata-keys",
        type=str,
        help="Comma-separated keys to include in metadata JSON (cannot combine with --exclude-metadata-keys)",
    )
    group.add_argument(
        "--exclude-metadata-keys",
        type=str,
        help="Comma-separated keys to exclude from metadata JSON (cannot combine with --include-metadata-keys)",
    )
    return p.parse_args(argv)


def _cli() -> None:
    args = _parse_args()
    include_keys: Optional[Set[str]] = None
    exclude_keys: Optional[Set[str]] = None

    if args.include_metadata_keys:
        include_keys = {k.strip() for k in args.include_metadata_keys.split(",") if k.strip()}
    if args.exclude_metadata_keys:
        exclude_keys = {k.strip() for k in args.exclude_metadata_keys.split(",") if k.strip()}

    try:
        if args.recursive:
            download_contract_source_recursive(
                args.address,
                args.chainid,
                args.outdir,
                save_abi=args.download_abi,
                save_metadata=args.download_metadata,
                include_metadata_keys=include_keys,
                exclude_metadata_keys=exclude_keys,
            )
        else:
            download_contract_source(
                args.address,
                args.chainid,
                args.outdir,
                save_abi=args.download_abi,
                save_metadata=args.download_metadata,
                include_metadata_keys=include_keys,
                exclude_metadata_keys=exclude_keys,
            )
    except Exception as e:
        sys.exit(f"[ERROR] {e}")


if __name__ == "__main__":
    _cli()
