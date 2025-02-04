#!/bin/bash

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

# Determine script source
if [ -f "./$SCRIPT_NAME" ]; then
    # Use local file if available
    SCRIPT_SOURCE="./$SCRIPT_NAME"
    echo "Found local $SCRIPT_NAME, using it for installation"
else
    # Download from GitHub if local file not found
    SCRIPT_SOURCE=$(mktemp)
    echo "Downloading $SCRIPT_NAME from GitHub..."
    curl -sSf https://raw.githubusercontent.com/burnettk/config-aider/refs/heads/main/config_aider.py -o "$SCRIPT_SOURCE" || {
        echo "Error: Failed to download script"
        rm -f "$SCRIPT_SOURCE"
        exit 1
    }
fi

# If installing from local source, create symlink to source directory
if [ "$SCRIPT_SOURCE" == "./$SCRIPT_NAME" ]; then
    # Get absolute path to source directory
    SOURCE_DIR=$(dirname "$(readlink -f "$SCRIPT_SOURCE")")
    # Create symlink to source directory
    ln -sf "$SOURCE_DIR" "$INSTALL_DIR/config-aider-src"
    # Create wrapper script
    cat <<EOF > "$INSTALL_DIR/$COMMAND_NAME"
#!/bin/bash
"$SOURCE_DIR/$SCRIPT_NAME" "\$@"
EOF
    chmod +x "$INSTALL_DIR/$COMMAND_NAME"
else
    # Install the script directly if downloaded
    install -m 755 "$SCRIPT_SOURCE" "$INSTALL_DIR/$SCRIPT_NAME"
    # Create symlink
    ln -sf "$INSTALL_DIR/$SCRIPT_NAME" "$INSTALL_DIR/$COMMAND_NAME"
fi

# Clean up temp file if we downloaded
if [ "$SCRIPT_SOURCE" != "./$SCRIPT_NAME" ]; then
    rm -f "$SCRIPT_SOURCE"
fi

# Add to PATH if not already there
if [[ ":$PATH:" != *":$INSTALL_DIR:"* ]]; then
    echo "Adding $INSTALL_DIR to PATH in ~/.bashrc and ~/.zshrc"
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.bashrc
    echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.zshrc
    echo "You may need to restart your shell or run: source ~/.bashrc"
fi

echo "Installation complete! You can now use '$COMMAND_NAME' command"
echo "Run 'ca --init' to create example configurations."
