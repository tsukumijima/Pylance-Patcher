#!/usr/bin/env -S uv run --script
# /// script
# requires-python = "~=3.13.0"
# dependencies = ["typer>=0.12.0", "rich>=14.0.0"]
# ///
"""A tool to patch the Pylance extension for compatibility with Cursor and other VS Code forks."""

import gzip
import json
import shutil
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Annotated, TypedDict

import typer
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()
app = typer.Typer(context_settings={"help_option_names": ["-h", "--help"]})


def _exit_with_error(message: str) -> None:
    """Print error message and exit with status 1."""
    console.print(f"[red]✗[/red] {message}")
    raise typer.Exit(1)


class PatchInfo(TypedDict):
    """Type definition for version-specific patch data."""

    search: str
    replace: str | None


# Version-specific patch data
PATCH_DATA: dict[str, PatchInfo] = {
    "2025.4.1": {
        # via @caenrige
        # https://github.com/VSCodium/vscodium/discussions/1641#discussioncomment-12603240
        "search": (
            "return(0x0,_0x302dc7[_0x1e5d1c(0x69a)])(_0x17bc9b[_0x1e5d1c(0x120)]),"
            "{'client':_0x5d8ccf,'start':()=>{const _0x751a33=_0x1e5d1c;"
            "return _0x2bfc9a['sendTelemetryEvent'](_0x1d90e3['EventName'][_0x751a33(0x48e)]),"
            "Promise[_0x751a33(0x60e)]();},'stop':()=>Promise[_0x1e5d1c(0x60e)](),"
            "'disposables':_0x22650a};"
        ),
        "replace": None,  # Will be replaced with spaces
    },
    "2025.6.2": {
        # via @jamesst20
        # https://github.com/VSCodium/vscodium/discussions/1641#discussioncomment-13694853
        "search": "return _0x1a0cda(_0x18d153);",
        "replace": "return true;",
    },
    "2025.6.101": {
        # via @jamesst20
        # https://github.com/VSCodium/vscodium/discussions/1641#discussioncomment-13694853
        "search": "return _0x4ecf62(_0x4bc45e);",
        "replace": "return true;",
    },
    "2025.7.1": {
        # via @jamesst20
        # https://github.com/VSCodium/vscodium/discussions/1641#discussioncomment-13694853
        "search": "return _0x1d2169(_0x1e7a73);",
        "replace": "return true;",
    },
}

# Supported versions
SUPPORTED_VERSIONS = list(PATCH_DATA.keys())


def get_latest_version() -> str:
    """Get the latest version from PATCH_DATA based on semantic versioning."""
    versions = list(PATCH_DATA.keys())

    def parse_version(v: str) -> tuple[int, int, int]:
        """Parse a version string into a tuple of integers."""
        parts = v.split(".")
        return tuple(int(p) for p in parts)  # type: ignore[return-value]

    # Sort versions and get the latest
    sorted_versions = sorted(versions, key=parse_version, reverse=True)
    return sorted_versions[0]


def download_file(url: str, dest: Path) -> None:
    """Download a file with progress indicator."""
    # Validate URL scheme for security
    if not url.startswith(("http://", "https://")):
        msg = "Only HTTP(S) URLs are allowed"
        raise ValueError(msg)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Downloading {dest.name}...", total=None)
        urllib.request.urlretrieve(url, dest)  # noqa: S310
        progress.update(task, completed=True)


def gunzip_file(src: Path, dest: Path) -> None:
    """Decompress a gzipped file."""
    with console.status(f"Decompressing {src.name}..."), gzip.open(src, "rb") as f_in, dest.open("wb") as f_out:
        shutil.copyfileobj(f_in, f_out)
    console.print(f"[green]✓[/green] Decompressed to {dest.name}")


def extract_zip(zip_path: Path, extract_to: Path) -> None:
    """Extract a zip file to a directory."""
    with console.status(f"Extracting {zip_path.name}..."), zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(extract_to)
    console.print(f"[green]✓[/green] Extracted to {extract_to.name}")


def patch_extension_bundle(bundle_path: Path, version: str) -> None:
    """Apply version-specific patches to the extension bundle."""
    if version not in PATCH_DATA:
        _exit_with_error(f"Unsupported version: {version}")

    patch_info = PATCH_DATA[version]
    search_text = patch_info["search"]
    replace_text = patch_info["replace"]

    with console.status(f"Patching extension bundle for version {version}..."):
        # Read the file
        content = bundle_path.read_text(encoding="utf-8")

        # Count occurrences
        occurrences = content.count(search_text)

        if occurrences == 0:
            _exit_with_error(f"Pattern not found in bundle for version {version}. The extension may have changed.")

        # Replace based on version
        replacement = " " * len(search_text) if replace_text is None else replace_text

        content = content.replace(search_text, replacement)

        # Write back
        bundle_path.write_text(content, encoding="utf-8")

    console.print(f"[green]✓[/green] Patched {occurrences} occurrence(s) in extension bundle for version {version}")


def compare_vscode_versions(version1: str, version2: str) -> int:
    """Compare two VS Code version strings.

    Returns:
        -1 if version1 < version2
         0 if version1 == version2
         1 if version1 > version2

    """
    # Extract version numbers, ignoring ^ or ~ prefixes
    v1 = version1.lstrip("^~").split(".")
    v2 = version2.lstrip("^~").split(".")

    # Compare major, minor, patch
    for i in range(3):
        n1 = int(v1[i]) if i < len(v1) else 0
        n2 = int(v2[i]) if i < len(v2) else 0
        if n1 < n2:
            return -1
        if n1 > n2:
            return 1
    return 0


def create_vsix(source_dir: Path, output_file: Path) -> None:
    """Create a .vsix file from a directory."""
    with (
        console.status(f"Creating {output_file.name}..."),
        zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zipf,
    ):
        for file_path in source_dir.rglob("*"):
            if file_path.is_file():
                arcname = file_path.relative_to(source_dir)
                zipf.write(file_path, arcname)
    console.print(f"[green]✓[/green] Created {output_file.name}")


def update_extension_version(extract_dir: Path, version: str) -> None:
    """Update version to include +patched suffix in package.json and manifest."""
    # Update version in package.json
    package_json_path = extract_dir / "extension" / "package.json"
    if package_json_path.exists():
        package_content = package_json_path.read_text(encoding="utf-8")
        package_content = package_content.replace(f'"version": "{version}"', f'"version": "{version}+patched"')
        package_json_path.write_text(package_content, encoding="utf-8")
        console.print(f"[green]✓[/green] Updated version in package.json to {version}+patched")

    # Update version in extension.vsixmanifest
    manifest_path = extract_dir / "extension.vsixmanifest"
    if manifest_path.exists():
        manifest_content = manifest_path.read_text(encoding="utf-8")
        manifest_content = manifest_content.replace(f'Version="{version}"', f'Version="{version}+patched"')
        manifest_path.write_text(manifest_content, encoding="utf-8")
        console.print(f"[green]✓[/green] Updated version in extension.vsixmanifest to {version}+patched")


def clamp_vscode_version(extract_dir: Path, vscode_version: str | None) -> None:
    """Clamp VS Code version requirement if needed."""
    if not vscode_version:
        return

    package_json_path = extract_dir / "extension" / "package.json"
    if not package_json_path.exists():
        return

    package_data = json.loads(package_json_path.read_text(encoding="utf-8"))
    current_vscode_version = package_data.get("engines", {}).get("vscode", "")

    # Normalize the user input to match VS Code format
    if not vscode_version.startswith("^"):
        vscode_target = f"^{vscode_version}"
        # Add .0 if only major.minor is provided
        if vscode_target.count(".") == 1:
            vscode_target += ".0"
    else:
        vscode_target = vscode_version

    if current_vscode_version and compare_vscode_versions(current_vscode_version, vscode_target) > 0:
        # Current version requirement is higher than our ceiling, clamp it
        package_data["engines"]["vscode"] = vscode_target
        package_json_path.write_text(json.dumps(package_data, indent=2) + "\n", encoding="utf-8")
        console.print(f"[green]✓[/green] Clamped VS Code version from {current_vscode_version} to {vscode_target}")
    else:
        console.print(f"[dim]VS Code version {current_vscode_version} is already compatible (≤ {vscode_target})[/dim]")


@app.command()
def patch(
    version: Annotated[str, typer.Argument(help="Pylance version to patch", show_choices=True)] = get_latest_version(),
    output_dir: Annotated[Path, typer.Option("--output", "-o", help="Output directory")] = Path(),
    *,
    keep_temp: Annotated[bool, typer.Option("--keep-temp", help="Keep temporary files", is_flag=True)] = False,
    vscode_version: Annotated[
        str | None,
        typer.Option("--vscode-version", help="Maximum VS Code version to require (e.g., '1.96')"),
    ] = "1.99",
) -> None:
    """Download and patch Pylance VS Code extension.

    Supported versions: 2025.4.1, 2025.6.2, 2025.6.101, 2025.7.1

    The --vscode-version option clamps the required VS Code version if the extension
    requires a newer version. For example, use --vscode-version 1.96 to declare
    the extension compatible with VS Code 1.96.
    """
    if version not in SUPPORTED_VERSIONS:
        console.print(f"[red]✗[/red] Unsupported version: {version}")
        console.print(f"Supported versions: {', '.join(SUPPORTED_VERSIONS)}")
        raise typer.Exit(1)

    console.print(f"[bold]Pylance Patcher[/bold] - Patching version {version}")
    console.print()

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Define file paths
    vsix_gz_path = output_dir / f"ms-python.vscode-pylance-{version}.vsix"
    vsix_path = output_dir / f"ms-python.vscode-pylance-{version}.zip"
    extract_dir = output_dir / f"ms-python.vscode-pylance-{version}-patched"
    patched_vsix = output_dir / f"ms-python.vscode-pylance-{version}-patched.vsix"

    try:
        # Download the extension
        url = f"https://marketplace.visualstudio.com/_apis/public/gallery/publishers/ms-python/vsextensions/vscode-pylance/{version}/vspackage"
        download_file(url, vsix_gz_path)

        # Decompress (it comes gzipped)
        gunzip_file(vsix_gz_path, vsix_path)

        # Extract the zip
        extract_zip(vsix_path, extract_dir)

        # Patch the extension bundle
        bundle_path = extract_dir / "extension" / "dist" / "extension.bundle.js"
        if not bundle_path.exists():
            _exit_with_error(f"Extension bundle not found at expected path: {bundle_path}")

        patch_extension_bundle(bundle_path, version)

        # Update version to include +patched suffix
        update_extension_version(extract_dir, version)

        # Clamp VS Code version if needed
        clamp_vscode_version(extract_dir, vscode_version)

        # Repackage as .vsix
        create_vsix(extract_dir, patched_vsix)

        # Clean up temporary files unless asked to keep them
        if not keep_temp:
            with console.status("Cleaning up temporary files..."):
                vsix_gz_path.unlink(missing_ok=True)
                vsix_path.unlink(missing_ok=True)
                shutil.rmtree(extract_dir, ignore_errors=True)
            console.print("[green]✓[/green] Cleaned up temporary files")

        console.print()
        console.print(f"[bold green]Success![/bold green] Patched Pylance {version} extension saved to: {patched_vsix}")

    except (OSError, urllib.error.URLError, zipfile.BadZipFile) as e:
        console.print(f"[red]✗[/red] Error: {e}")
        raise typer.Exit(1) from e


if __name__ == "__main__":
    app()
