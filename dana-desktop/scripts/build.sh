#!/bin/bash
#
# DANA Journal Build Helper Script
#
# Quick build commands for common scenarios.
#

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo -e "${BLUE}DANA Journal Build Helper${NC}"
echo "Project root: $PROJECT_ROOT"

# Function to show usage
show_usage() {
    echo -e "\nUsage: $0 [command] [options]"
    echo -e "\nCommands:"
    echo -e "  ${GREEN}macos${NC}      Build for macOS (native .app bundle)"
    echo -e "  ${GREEN}windows${NC}    Build for Windows (.exe)"
    echo -e "  ${GREEN}linux${NC}      Build for Linux (AppImage/native)"
    echo -e "  ${GREEN}web${NC}        Build for Web (PWA)"
    echo -e "  ${GREEN}dev${NC}        Quick development build for current platform"
    echo -e "  ${GREEN}test${NC}       Test build (no artifacts, validation only)"
    echo -e "  ${GREEN}clean${NC}      Clean build directories"
    echo -e "  ${GREEN}all${NC}        Build for all desktop platforms"
    echo -e "\nOptions:"
    echo -e "  --verbose  Show detailed build output"
    echo -e "  --dev      Development mode (faster build)"
    echo -e "  --help     Show this help message"
}

# Function to check prerequisites  
check_prerequisites() {
    echo -e "\n${YELLOW}Checking prerequisites...${NC}"
    
    # Check if uv is installed
    if ! command -v uv &> /dev/null; then
        echo -e "${RED}Error: 'uv' is not installed. Please install it first.${NC}"
        echo "Visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    fi
    
    # Check if we're in a git repository
    if ! git rev-parse --git-dir &> /dev/null; then
        echo -e "${YELLOW}Warning: Not in a git repository. Version info may be limited.${NC}"
    fi
    
    # Check if flet is available
    if ! uv run python -c "import flet" &> /dev/null; then
        echo -e "${RED}Error: Flet is not available. Installing dependencies...${NC}"
        cd "$PROJECT_ROOT"
        uv sync
    fi
    
    echo -e "${GREEN}✓ Prerequisites satisfied${NC}"
}

# Build function
build_platform() {
    local platform=$1
    local mode=${2:-"prod"}
    local verbose=${3:-""}
    
    echo -e "\n${BLUE}Building DANA Journal for $platform...${NC}"
    
    cd "$PROJECT_ROOT"
    
    # Prepare arguments
    local args="$platform"
    if [[ $mode == "dev" ]]; then
        args="$args --dev"
    else
        args="$args --prod"  
    fi
    
    if [[ $verbose == "--verbose" ]]; then
        args="$args --verbose"
    fi
    
    # Run the build
    python scripts/build.py $args
    
    if [[ $? -eq 0 ]]; then
        echo -e "${GREEN}✅ Build completed successfully for $platform${NC}"
    else
        echo -e "${RED}❌ Build failed for $platform${NC}"
        exit 1
    fi
}

# Main execution
cd "$PROJECT_ROOT"

case "${1:-help}" in
    "macos")
        check_prerequisites
        build_platform "macos" "${2:-prod}" "$3"
        ;;
    "windows") 
        check_prerequisites
        build_platform "windows" "${2:-prod}" "$3"
        ;;
    "linux")
        check_prerequisites  
        build_platform "linux" "${2:-prod}" "$3"
        ;;
    "web")
        check_prerequisites
        build_platform "web" "${2:-prod}" "$3"
        ;;
    "dev")
        check_prerequisites
        # Detect current platform
        if [[ "$OSTYPE" == "darwin"* ]]; then
            build_platform "macos" "dev" "$2"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            build_platform "linux" "dev" "$2"
        elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
            build_platform "windows" "dev" "$2"
        else
            echo -e "${RED}Unknown platform: $OSTYPE${NC}"
            exit 1
        fi
        ;;
    "test")
        echo -e "${YELLOW}Running build validation...${NC}"
        check_prerequisites
        # Run syntax check
        uv run python -m py_compile src/dana_journal/main.py
        echo -e "${GREEN}✓ Build validation passed${NC}"
        ;;
    "clean")
        echo -e "${YELLOW}Cleaning build directories...${NC}"
        python scripts/build.py macos --clean
        echo -e "${GREEN}✓ Build directories cleaned${NC}"
        ;;
    "all")
        check_prerequisites
        echo -e "${BLUE}Building for all desktop platforms...${NC}"
        build_platform "macos" "${2:-prod}" "$3"
        build_platform "windows" "${2:-prod}" "$3" 
        build_platform "linux" "${2:-prod}" "$3"
        echo -e "${GREEN}🎉 All builds completed!${NC}"
        ;;
    "help"|"--help"|"-h")
        show_usage
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        show_usage
        exit 1
        ;;
esac