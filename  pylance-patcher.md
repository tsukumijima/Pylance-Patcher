# pylance-patcher

A tool to patch the Pylance extension for compatibility with Cursor and other VS Code forks.

Jump to the main script: [pylance_patcher.py](#file-pylance_patcher-py)

Run as a standalone Python script using [uv](https://docs.astral.sh/uv/):

`uv run https://gist.github.com/realdimas/c025cdba50cc05e0f644eb71bf7efbb9 --help`

## Usage

```plain
$ uv run --script pylance_patcher.py --help

 Usage: pylance_patcher.py [OPTIONS] [VERSION]

 Download and patch Pylance VS Code extension.

 Supported versions: 2025.4.1, 2025.6.2, 2025.6.101, 2025.7.1
 The --vscode-version option clamps the required VS Code version if the extension requires a newer
 version. For example, use --vscode-version 1.96 to declare the extension compatible with VS Code
 1.96.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────╮
│   version      [VERSION]  Pylance version to patch [default: 2025.7.1]                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --output              -o      PATH  Output directory [default: .]                                │
│ --keep-temp                         Keep temporary files                                         │
│ --vscode-version              TEXT  Maximum VS Code version to require (e.g., '1.96')            │
│                                     [default: 1.99]                                              │
│ --install-completion                Install completion for the current shell.                    │
│ --show-completion                   Show completion for the current shell, to copy it or         │
│                                     customize the installation.                                  │
│ --help                -h            Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
