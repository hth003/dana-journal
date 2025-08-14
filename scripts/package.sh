#!/bin/bash
#
# DANA Journal Package Management Script
#
# Comprehensive packaging workflow automation
#

set -e

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

show_usage() {
    echo -e "${BLUE}DANA Journal Package Management${NC}"
    echo -e "\nComplete packaging workflow automation\n"
    
    echo -e "${GREEN}Release Management:${NC}"
    echo -e "  release-patch     Bump patch version and create release"
    echo -e "  release-minor     Bump minor version and create release"  
    echo -e "  release-major     Bump major version and create release"
    echo -e "  tag-current       Create git tag for current version"
    
    echo -e "\n${GREEN}Build Management:${NC}"
    echo -e "  build-all         Build for all desktop platforms"
    echo -e "  build-desktop     Build for current desktop platform"
    echo -e "  build-web         Build web/PWA version"
    echo -e "  test-build        Validate build configuration"
    
    echo -e "\n${GREEN}Distribution:${NC}"
    echo -e "  package-release   Create distribution packages"
    echo -e "  generate-checksums Generate SHA256 checksums"
    echo -e "  prepare-github    Prepare GitHub release artifacts"
    
    echo -e "\n${GREEN}Maintenance:${NC}"
    echo -e "  clean-all         Clean all build artifacts"
    echo -e "  update-deps       Update all dependencies"
    echo -e "  check-health      Health check for build environment"
}

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

check_git_clean() {
    if [[ -n $(git status --porcelain) ]]; then
        log_error "Working directory is not clean. Commit or stash changes first."
        git status --short
        exit 1
    fi
    log_success "Working directory is clean"
}

check_git_main() {
    local current_branch=$(git branch --show-current)
    if [[ "$current_branch" != "main" ]]; then
        log_warning "Not on main branch (currently on: $current_branch)"
        read -p "Continue anyway? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
    fi
}

get_current_version() {
    python scripts/version.py current | head -n 1 | cut -d' ' -f3
}

create_release() {
    local bump_type=$1
    
    log_info "Creating $bump_type release..."
    
    # Verify git state
    check_git_clean
    check_git_main
    
    # Update version and create tag
    log_info "Bumping version ($bump_type)"
    python scripts/version.py release $bump_type
    
    local new_version=$(get_current_version)
    log_success "Release v$new_version created"
    
    # Build packages
    log_info "Building packages for release..."
    build_all_platforms
    
    # Generate checksums
    generate_checksums
    
    # Show next steps
    echo
    log_success "Release v$new_version is ready!"
    echo -e "${PURPLE}Next steps:${NC}"
    echo "  1. Review the changes and packages in dist/"
    echo "  2. Push changes: git push && git push origin --tags"
    echo "  3. Create GitHub release: gh release create v$new_version dist/* --generate-notes"
    echo "  4. Update documentation if needed"
}

build_all_platforms() {
    log_info "Building for all desktop platforms..."
    
    # Detect current OS for realistic builds
    if [[ "$OSTYPE" == "darwin"* ]]; then
        platforms=("macos" "web")
        log_info "Building on macOS: macOS and Web builds"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        platforms=("linux" "web") 
        log_info "Building on Linux: Linux and Web builds"
    else
        platforms=("web")
        log_info "Building on $OSTYPE: Web build only"
    fi
    
    for platform in "${platforms[@]}"; do
        log_info "Building for $platform..."
        if ./scripts/build.sh $platform --prod; then
            log_success "✓ $platform build completed"
        else
            log_error "✗ $platform build failed"
            exit 1
        fi
    done
    
    log_success "All platform builds completed"
}

test_build_config() {
    log_info "Testing build configuration..."
    
    # Check syntax
    if ./scripts/build.sh test; then
        log_success "Build configuration is valid"
    else
        log_error "Build configuration test failed"
        exit 1
    fi
    
    # Check version script
    local current_version=$(python scripts/version.py current 2>/dev/null | head -n 1)
    if [[ -n "$current_version" ]]; then
        log_success "Version management is working: $current_version"
    else
        log_error "Version script failed"
        exit 1
    fi
    
    # Check dependencies
    log_info "Checking dependencies..."
    if uv sync --dry-run >/dev/null 2>&1; then
        log_success "Dependencies are valid"
    else
        log_error "Dependency issues detected"
        exit 1
    fi
}

generate_checksums() {
    log_info "Generating checksums..."
    
    cd "$PROJECT_ROOT/dist"
    
    if [[ ! -d . ]] || [[ -z "$(ls -A . 2>/dev/null)" ]]; then
        log_warning "No build artifacts found in dist/"
        return
    fi
    
    # Generate SHA256 checksums
    if command -v shasum >/dev/null; then
        shasum -a 256 * > checksums.sha256
    elif command -v sha256sum >/dev/null; then
        sha256sum * > checksums.sha256
    else
        log_error "No checksum utility found (shasum or sha256sum)"
        exit 1
    fi
    
    log_success "Checksums generated: dist/checksums.sha256"
    
    cd "$PROJECT_ROOT"
}

prepare_github_release() {
    local version=$(get_current_version)
    
    log_info "Preparing GitHub release for v$version..."
    
    # Check if gh CLI is available
    if ! command -v gh >/dev/null; then
        log_warning "GitHub CLI not found. Install 'gh' for automated release creation."
        log_info "Manual steps:"
        echo "  1. Go to: https://github.com/YOUR_REPO/releases/new"
        echo "  2. Tag: v$version"
        echo "  3. Upload files from dist/ directory"
        return
    fi
    
    # Generate release notes
    log_info "Generating release notes..."
    
    # Create release
    if gh release create "v$version" dist/* --generate-notes --draft; then
        log_success "Draft GitHub release created for v$version"
        log_info "Review and publish at: $(gh repo view --web)/releases"
    else
        log_error "Failed to create GitHub release"
        exit 1
    fi
}

clean_all_artifacts() {
    log_info "Cleaning all build artifacts..."
    
    # Clean build directories
    rm -rf "$PROJECT_ROOT/build" "$PROJECT_ROOT/dist"
    log_success "Build directories cleaned"
    
    # Clean Python cache
    find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find "$PROJECT_ROOT" -type f -name "*.pyc" -delete 2>/dev/null || true
    log_success "Python cache cleaned"
    
    # Clean uv cache (optional)
    read -p "Clean uv cache? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        uv cache clean
        log_success "UV cache cleaned"
    fi
}

update_dependencies() {
    log_info "Updating dependencies..."
    
    # Update lock file
    uv sync --upgrade
    log_success "Dependencies updated"
    
    # Check for security vulnerabilities (if available)
    if uv pip audit >/dev/null 2>&1; then
        log_info "Running security audit..."
        if uv pip audit; then
            log_success "No security vulnerabilities found"
        else
            log_warning "Security vulnerabilities detected - review above"
        fi
    fi
}

health_check() {
    log_info "Performing build environment health check..."
    
    # Check Python version
    python_version=$(python --version 2>&1)
    log_info "Python: $python_version"
    
    # Check uv
    if command -v uv >/dev/null; then
        uv_version=$(uv --version)
        log_success "UV: $uv_version"
    else
        log_error "UV not found - install from https://docs.astral.sh/uv/"
        exit 1
    fi
    
    # Check git
    if command -v git >/dev/null; then
        git_version=$(git --version)
        log_success "$git_version"
    else
        log_error "Git not found"
        exit 1
    fi
    
    # Test build config
    test_build_config
    
    # Platform-specific checks
    if [[ "$OSTYPE" == "darwin"* ]]; then
        if command -v xcodebuild >/dev/null; then
            log_success "Xcode build tools available"
        else
            log_warning "Xcode not found - needed for macOS builds"
        fi
        
        if command -v pod >/dev/null; then
            log_success "CocoaPods available"
        else
            log_warning "CocoaPods not found - needed for macOS builds"
        fi
    fi
    
    log_success "Health check completed"
}

# Main command processing
cd "$PROJECT_ROOT"

case "${1:-help}" in
    "release-patch")
        create_release "patch"
        ;;
    "release-minor") 
        create_release "minor"
        ;;
    "release-major")
        create_release "major"
        ;;
    "tag-current")
        check_git_clean
        local version=$(get_current_version)
        python scripts/version.py tag
        log_success "Tagged current version: v$version"
        ;;
    "build-all")
        build_all_platforms
        ;;
    "build-desktop")
        ./scripts/build.sh dev
        ;;
    "build-web")
        ./scripts/build.sh web --prod
        ;;
    "test-build")
        test_build_config
        ;;
    "package-release")
        build_all_platforms
        generate_checksums
        log_success "Release packages ready in dist/"
        ;;
    "generate-checksums")
        generate_checksums
        ;;
    "prepare-github")
        prepare_github_release
        ;;
    "clean-all")
        clean_all_artifacts
        ;;
    "update-deps")
        update_dependencies
        ;;
    "check-health")
        health_check
        ;;
    "help"|"--help"|"-h"|*)
        show_usage
        exit 0
        ;;
esac