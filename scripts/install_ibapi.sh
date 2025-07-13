#!/bin/bash
# Install latest ibapi from Interactive Brokers source
# This script downloads and installs the same version used in CI/CD

set -e

echo "🔄 Installing latest ibapi from Interactive Brokers source..."

# Check if we're on macOS/Linux or Windows
if [[ "$OSTYPE" == "linux-gnu"* ]] || [[ "$OSTYPE" == "darwin"* ]]; then
    # Linux/macOS
    DOWNLOAD_URL="https://interactivebrokers.github.io/downloads/twsapi_macunix.1030.01.zip"
    ARCHIVE_NAME="twsapi_macunix.1030.01.zip"
else
    echo "❌ This script is designed for Linux/macOS. For Windows, download manually from:"
    echo "   https://interactivebrokers.github.io/downloads/twsapi_windows.1030.01.msi"
    exit 1
fi

# Download and install
echo "📥 Downloading TWS API package..."
wget -q "$DOWNLOAD_URL"

echo "📦 Extracting package..."
unzip -q "$ARCHIVE_NAME"

echo "🔧 Installing ibapi..."
cd IBJts/source/pythonclient
python setup.py install

echo "🧹 Cleaning up..."
cd ../../..
rm -rf IBJts "$ARCHIVE_NAME"

echo "✅ Verifying installation..."
python -c "import ibapi; print('✅ ibapi installed successfully')"
python -c "from ibapi.client import EClient; from ibapi.wrapper import EWrapper; print('✅ ibapi classes imported successfully')"

echo "🎉 ibapi installation complete!"
