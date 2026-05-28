#!/bin/bash
# Setup script for Shred-CLI
# Detects platform and installs dependencies

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== Shred-CLI Setup ==="
echo ""

# Detect OS
OS="unknown"
case "$(uname -s)" in
    Linux*)     OS=Linux;;
    Darwin*)    OS=Mac;;
    CYGWIN*)    OS=Cygwin;;
    MINGW*)     OS=MinGw;;
    MSYS*)      OS=Windows;;
esac

echo "Detected OS: $OS"
echo ""

# Check Python version
echo "Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+' | head -1)
REQUIRED_VERSION="3.10"

if [ -z "$PYTHON_VERSION" ]; then
    echo -e "${RED}Error: Python 3 not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "Found Python $PYTHON_VERSION"

# Platform-specific setup
case $OS in
    Linux)
        echo ""
        echo -e "${YELLOW}Linux Setup${NC}"
        echo "Installing ALSA development libraries..."
        
        if command -v apt-get &> /dev/null; then
            # Debian/Ubuntu
            sudo apt-get update
            sudo apt-get install -y libasound2-dev || {
                echo -e "${YELLOW}Warning: Could not install libasound2-dev${NC}"
                echo "You may need to install it manually"
            }
        elif command -v dnf &> /dev/null; then
            # Fedora
            sudo dnf install -y alsa-lib-devel || {
                echo -e "${YELLOW}Warning: Could not install alsa-lib-devel${NC}"
            }
        elif command -v pacman &> /dev/null; then
            # Arch
            sudo pacman -S --needed alsa-lib || {
                echo -e "${YELLOW}Warning: Could not install alsa-lib${NC}"
            }
        fi
        
        echo ""
        echo -e "${YELLOW}Important: Add your user to the 'input' group for keyboard access:${NC}"
        echo "  sudo usermod -a -G input \$USER"
        echo "  Then log out and back in"
        ;;
        
    Mac)
        echo ""
        echo -e "${YELLOW}macOS Setup${NC}"
        echo "No additional packages required"
        echo ""
        echo -e "${YELLOW}Important: Grant Accessibility permissions for keyboard access:${NC}"
        echo "  1. Open System Preferences → Privacy & Security → Accessibility"
        echo "  2. Add your terminal application (Terminal.app or iTerm)"
        echo ""
        echo -e "${YELLOW}For MIDI output, enable IAC Driver:${NC}"
        echo "  1. Open Audio MIDI Setup"
        echo "  2. Window → Show MIDI Studio"
        echo "  3. Double-click 'IAC Driver'"
        echo "  4. Check 'Device is online'"
        ;;
        
    Windows)
        echo ""
        echo -e "${YELLOW}Windows Setup${NC}"
        echo "No additional setup required"
        echo ""
        echo -e "${YELLOW}Note: Install a virtual MIDI driver like LoopBe1 for DAW integration${NC}"
        ;;
esac

echo ""
echo "Installing Shred-CLI..."
pip install -e . || {
    echo -e "${YELLOW}pip install failed, trying with --user${NC}"
    pip install --user -e .
}

echo ""
echo -e "${GREEN}=== Setup Complete ===${NC}"
echo ""
echo "Quick start:"
echo "  shred start --no-daemon  # Run in foreground for testing"
echo "  shred start              # Run as background daemon"
echo "  shred status             # Check status"
echo "  shred stop               # Stop daemon"
echo ""
echo "For more help: shred --help"
