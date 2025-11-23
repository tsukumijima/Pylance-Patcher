# Pylance-Patcher

A tool to patch the Pylance extension for compatibility with Cursor and other VS Code forks.  
(Forked from https://gist.github.com/realdimas/c025cdba50cc05e0f644eb71bf7efbb9)

Jump to the main script: [pylance_patcher/__init__.py](pylance_patcher/__init__.py)

Run as a standalone Python script using [uv](https://docs.astral.sh/uv/):

`uvx --from git+https://github.com/tsukumijima/Pylance-Patcher pylance-patcher --help`

## Usage

```plain
$ uvx --from . pylance-patcher --help

 Usage: pylance-patcher [OPTIONS] [VERSION]

 Download and patch Pylance VS Code extension.

 Supported versions: 2025.4.1, 2025.6.2, 2025.6.101, 2025.7.1
 The --vscode-version option clamps the required VS Code version if the extension requires a newer  
 version. For example, use --vscode-version 1.96 to declare the extension compatible with VS Code   
 1.96.
The --override-version option allows you to override the extension version to prevent Cursor from  
 automatically reverting to an older version. By default, the version is overridden to 2024.8.1.

╭─ Arguments ──────────────────────────────────────────────────────────────────────────────────────╮
│   version      [VERSION]  Pylance version to patch [default: 2025.7.1]                           │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
╭─ Options ────────────────────────────────────────────────────────────────────────────────────────╮
│ --output              -o      PATH  Output directory [default: .]                                │
│ --keep-temp                         Keep temporary files                                         │
│ --vscode-version              TEXT  Maximum VS Code version to require (e.g., '1.96')            │
│                                     [default: 1.99]                                              │
│ --override-version            TEXT  Override version to use instead of the original version      │
│                                     (default: 2024.8.1)                                          │
│                                     [default: 2024.8.1]                                          │
│ --install-completion                Install completion for the current shell.                    │
│ --show-completion                   Show completion for the current shell, to copy it or         │
│                                     customize the installation.                                  │
│ --help                -h            Show this message and exit.                                  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────╯
```
