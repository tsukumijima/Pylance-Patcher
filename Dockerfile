# Use Base devcontainer for development
FROM mcr.microsoft.com/devcontainers/base:latest

# Install uv for Python interpreter and dependency management
COPY --from=ghcr.io/astral-sh/uv /uv /uvx /usr/local/bin/

# Install ruff for formatting and linting
COPY --from=ghcr.io/astral-sh/ruff /ruff /usr/local/bin/

# Use /usr/local for Python installation
ENV PYTHON_PATH=/usr/local
ENV UV_PROJECT_ENVIRONMENT="${PYTHON_PATH}"
ENV UV_PYTHON_PREFERENCE=only-system

# Prevent version check in Pyright
ENV PYRIGHT_PYTHON_IGNORE_WARNINGS=1

# Set LC_CTYPE to fix "character ghosting" issue in terminal
# https://github.com/ohmyzsh/ohmyzsh/wiki/FAQ#i-see-duplicate-typed-characters-after-i-complete-a-command
ENV LC_CTYPE=en_US.UTF-8

# Switch to the vscode user
USER vscode

# Key apt cache mounts by target architecture
ARG TARGETPLATFORM

RUN --mount=type=bind,source=.,target=/workspaces/pylance-patcher \
	--mount=type=cache,target=/home/vscode/.cache/uv,uid=1000 \
	--mount=type=cache,target=/var/lib/apt,sharing=locked,id=apt-lib-${TARGETPLATFORM} \
	--mount=type=cache,target=/var/cache/apt,sharing=locked,id=apt-cache-${TARGETPLATFORM} \
	<<EOF
	
	set -Eeux
	
	# Take over ownership of /usr/local for Python installation
	sudo chown -R vscode:vscode /usr/local
	
	# Take ownership of the .cache directory
	sudo chown -R vscode:vscode /home/vscode/.cache

	# Install specific Python version from .python-version
	uv python install --project=/workspaces/pylance-patcher --install-dir=/tmp/python 
	
	# Move Python into /usr/local
	(cd /tmp/python/* && tar -cf- .) | (cd /usr/local && tar -xf-)
	rm -r /tmp/python
	
	# Switch default shell to zsh
	sudo chsh -s "$(which zsh)" "$(whoami)"
	
	# Disable OMZ auto-update check
	sed -i "/^# zstyle ':omz:update' mode disabled/s/^# //" "${HOME}/.zshrc"
	
	# Persist downloaded .deb packages in the cache
	# Ref: https://docs.docker.com/reference/dockerfile/#example-cache-apt-packages
	sudo rm /etc/apt/apt.conf.d/docker-clean
	echo 'Binary::apt::APT::Keep-Downloaded-Packages "true";' | sudo tee /etc/apt/apt.conf.d/keep-cache >/dev/null
	
	# Drop system python3 to avoid conflicting with /usr/local/bin/python
	sudo apt-get remove -y --purge python3
		
	# Update package lists
	sudo apt-get update
	# Upgrade all packages to the latest version
	export DEBIAN_FRONTEND=noninteractive
	export DEBIAN_PRIORITY=critical
	sudo --preserve-env=DEBIAN_FRONTEND,DEBIAN_PRIORITY \
		apt-get upgrade -y --no-install-recommends \
		-o Dpkg::Options::="--force-confdef" \
		-o Dpkg::Options::="--force-confnew"
	# Remove unneeded packages
	sudo apt-get autoremove -y --purge
	
	# Bind-mounted repository could have a different user ID.
	# We need to mark the directory as safe for git to resolve the
	# "fatal: detected dubious ownership in repository" error.
	git config --global --add safe.directory /workspaces/pylance-patcher
	
	# Install dependencies and package
	uv sync --all-groups --project /workspaces/pylance-patcher --locked --compile-bytecode --link-mode=copy

	# Add command completions
	# Shell detection fails under qemu, using "|| true" to suppress hard failures
	echo 'pylance-patcher --install-completion' | zsh -s || true
	echo 'pylance-patcher --install-completion' | bash -s || true
	
	# Invoke --help as a sanity check to make sure the installed package is runnable
	pylance-patcher --help
EOF

# Default container to the workspace root
WORKDIR /workspaces/pylance-patcher
