#!/usr/bin/env bash

function error_handler() {
  >&2 echo "Exited with BAD EXIT CODE '${2}' in ${0} script at line: ${1}."
  exit "$2"
}
trap 'error_handler ${LINENO} $?' ERR
set -o errtrace -o errexit -o nounset -o pipefail

# Target installation directory
INSTALL_DIR="$HOME/.local/bin"
SCRIPT_NAME="config_aider.py"
COMMAND_NAME="ca"

# Create target directory if it doesn't exist
mkdir -p "$INSTALL_DIR"

# Check if ca command already exists and isn't our script
if command -v "$COMMAND_NAME" >/dev/null 2>&1; then
  existing_path=$(command -v "$COMMAND_NAME")
  if [ "$(readlink -f "$existing_path")" != "$INSTALL_DIR/$SCRIPT_NAME" ]; then
    echo "Error: '$COMMAND_NAME' command already exists at $existing_path"
    exit 1
  fi
fi

script_dir="$(
  cd -- "$(dirname "$0")" >/dev/null 2>&1
  pwd -P
)"

if [[ -n "$script_dir" ]] && [[ -d "${script_dir}/sample_config" ]]; then
  source_dir="$script_dir"
else
  # sample_config not found - clone to ~/.local/share/config-aider
  LOCAL_SHARE="$HOME/.local/share/config-aider"
  echo "sample_config directory not found - cloning to $LOCAL_SHARE"
  mkdir -p "$LOCAL_SHARE"
  git clone https://github.com/burnettk/config-aider.git "$LOCAL_SHARE"
  source_dir="$LOCAL_SHARE"
fi

ln -sf "$source_dir/$SCRIPT_NAME" "$INSTALL_DIR/$COMMAND_NAME"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
  echo "Adding $INSTALL_DIR to PATH in ~/.bashrc and ~/.zshrc"
  echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >>~/.bashrc
  echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >>~/.zshrc
  echo "You may need to restart your shell or run: source ~/.bashrc"
fi

echo "Installation complete! You can now use '$COMMAND_NAME' command"
echo "Run 'ca --init' to create example configurations."
