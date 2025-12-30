#!/usr/bin/env bash
set -e

TOOL_NAME="ai-rename-images"
INSTALL_DIR="$HOME/.local/$TOOL_NAME"
BIN_DIR="$HOME/.local/bin"

echo "Installing $TOOL_NAME..."

# Ensure directories exist
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"

# Create virtual environment
python3 -m venv "$INSTALL_DIR/venv"

# Activate and install deps
source "$INSTALL_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt

# Copy script
cp yourtool.py "$INSTALL_DIR/$TOOL_NAME"

# Create launcher
cat > "$BIN_DIR/$TOOL_NAME" <<EOF
#!/usr/bin/env bash
source "$INSTALL_DIR/venv/bin/activate"
exec python "$INSTALL_DIR/$TOOL_NAME" "\$@"
EOF

chmod +x "$BIN_DIR/$TOOL_NAME"

echo "Installed successfully!"
echo "Make sure ~/.local/bin is in your PATH"
