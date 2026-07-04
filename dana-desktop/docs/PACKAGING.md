# DANA Journal - Packaging, Versioning & Distribution Guide

This guide covers the complete process for building, versioning, and distributing the DANA Journal application across multiple platforms.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Versioning](#versioning)
- [Platform-Specific Building](#platform-specific-building)
- [Distribution](#distribution)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Development Environment
- **Python 3.11+** - Required for the application
- **uv** - Python package manager ([installation guide](https://docs.astral.sh/uv/getting-started/installation/))
- **Git** - For version control and tagging

### Platform-Specific Requirements

#### macOS Builds
- **Xcode** - Install from App Store or [Apple Developer](https://developer.apple.com/xcode/)
- **Xcode Command Line Tools**: `xcode-select --install`
- **CocoaPods**: `sudo gem install cocoapods`

#### Windows Builds
- **Visual Studio** with C++ build tools
- **Windows 10 SDK** 

#### Linux Builds  
- **Build essentials**: `sudo apt-get install build-essential`
- **GTK development libraries**: `sudo apt-get install libgtk-3-dev`

#### Web Builds
- No additional requirements (uses Flutter web)

## Quick Start

### 1. Install Dependencies
```bash
uv sync
```

### 2. Verify Build Environment
```bash
# Check prerequisites and validate syntax
./scripts/build.sh test
```

### 3. Development Build
```bash
# Quick development build for current platform
./scripts/build.sh dev
```

### 4. Production Build
```bash
# Build for specific platform
./scripts/build.sh macos
./scripts/build.sh windows
./scripts/build.sh linux
./scripts/build.sh web
```

## Versioning

DANA Journal uses [Semantic Versioning](https://semver.org/) (MAJOR.MINOR.PATCH).

### Version Management Commands

```bash
# Show current version information
python scripts/version.py current

# Bump version
python scripts/version.py bump patch    # 0.1.0 → 0.1.1
python scripts/version.py bump minor    # 0.1.0 → 0.2.0  
python scripts/version.py bump major    # 0.1.0 → 1.0.0

# Set specific version
python scripts/version.py set 1.2.3

# Create git tag
python scripts/version.py tag

# Complete release (bump + tag)
python scripts/version.py release patch
```

### Release Workflow

1. **Update version**: `python scripts/version.py release minor`
2. **Build packages**: `./scripts/build.sh all --prod`
3. **Push changes**: `git push && git push origin --tags`
4. **Create GitHub release** with generated packages
5. **Update documentation** and release notes

## Platform-Specific Building

### macOS Application (.app bundle)

```bash
# Development build
./scripts/build.sh dev

# Production build
./scripts/build.sh macos --prod
```

**Output**: `dist/dana-journal.app`

**Features**:
- Native macOS application bundle
- Proper app icons and metadata
- Code signing ready (configure in `pyproject.toml`)
- Minimum macOS 11.0 support

### Windows Application (.exe)

```bash
./scripts/build.sh windows --prod
```

**Output**: `dist/dana-journal.exe`

**Features**:
- Standalone executable
- Windows application metadata
- Console mode disabled
- Installer-ready format

### Linux Application

```bash
./scripts/build.sh linux --prod  
```

**Output**: `dist/dana-journal` (executable) or AppImage

**Features**:
- Native Linux executable
- Desktop integration files
- MIME type associations for .md files
- XDG compliance

### Web Application (PWA)

```bash
./scripts/build.sh web --prod
```

**Output**: `dist/web/` directory

**Features**:
- Progressive Web App
- Service worker support
- Offline functionality
- Responsive design

## Build Configuration

### Project Structure
```
pyproject.toml          # Main project configuration
├── [tool.flet]         # Flet build settings
├── [tool.flet.icons]   # Platform-specific icons
├── [tool.flet.build]   # Build configurations
└── [tool.flet.build.macos]  # Platform-specific settings
```

### Key Configuration Files

#### `pyproject.toml` - Main Configuration
- **Product metadata**: Name, description, copyright
- **Version information**: Semantic version, build numbers
- **Icon configuration**: Platform-specific icon paths
- **Build settings**: Compilation, packaging options
- **Platform configurations**: macOS bundle ID, Windows file info

#### `assets/icons/` - Application Icons
- `dana_icon_16x16.png` - Small icon (Windows, Linux)
- `dana_icon_32x32.png` - Standard icon
- `dana_icon_64x64.png` - Medium icon  
- `dana_icon_128x128.png` - Large icon
- `dana_icon_256x256.png` - High-res icon (Windows, Linux)
- `dana_icon_512x512.png` - Retina icon (macOS)
- `dana_logo.svg` - Vector logo for documentation

## Distribution

### GitHub Releases

1. **Create Release**: Use GitHub's release interface
2. **Upload Artifacts**: Attach built packages from `dist/`
3. **Write Release Notes**: Include changelog and new features
4. **Tag Version**: Should match git tag created by version script

### App Stores (Future)

#### macOS App Store
- Requires Apple Developer account
- Code signing with Developer ID
- App Store review process
- Sandboxing compliance

#### Microsoft Store  
- Windows application certification
- MSIX packaging
- Store submission process

#### Linux Package Repositories
- Debian/Ubuntu: `.deb` packages  
- Fedora/RHEL: `.rpm` packages
- Arch: AUR packages
- Flatpak/Snap universal packages

### Direct Distribution

#### Self-Hosted Downloads
- Host packages on website
- Provide checksums for verification  
- Automatic update system (future feature)

#### Enterprise Distribution
- Internal package repositories
- Custom installation scripts
- MSI installers for Windows environments

## Advanced Build Options

### Custom Build Scripts

The build system provides flexible scripting:

```bash
# Build all desktop platforms
./scripts/build.sh all

# Build with custom options
python scripts/build.py macos --dev --verbose

# Clean build directories
./scripts/build.sh clean
```

### Environment Variables

Configure builds with environment variables:

```bash
# Enable verbose output
export FLET_BUILD_VERBOSE=1

# Custom build output directory
export FLET_BUILD_OUTPUT_DIR=/custom/path

# Development mode
export DANA_DEV_BUILD=1
```

### Build Optimization

For production builds, the following optimizations are applied:

- **Python compilation**: Bytecode compilation for faster startup
- **Package optimization**: Include only necessary dependencies  
- **Asset optimization**: Compressed icons and resources
- **Dead code elimination**: Unused code removal
- **Bundle size reduction**: Minimized final package size

## Troubleshooting

### Common Build Issues

#### Xcode Not Found (macOS)
```
Error: Xcode installation is incomplete
```
**Solution**: Install Xcode from App Store, then run:
```bash
sudo xcode-select --switch /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
```

#### CocoaPods Missing (macOS)
```
Error: CocoaPods not installed
```
**Solution**: Install CocoaPods:
```bash
sudo gem install cocoapods
pod setup
```

#### Visual Studio Missing (Windows)
```
Error: Visual Studio build tools not found
```
**Solution**: Install Visual Studio with C++ build tools

#### Permission Denied
```
Error: Permission denied when accessing build directory
```
**Solution**: Check directory permissions:
```bash  
chmod -R 755 build/ dist/
```

### Build Logs

Enable verbose logging for detailed error information:
```bash
./scripts/build.sh macos --verbose
```

Logs are saved to:
- `build/logs/` - Build process logs
- `dist/build_info_*.json` - Build metadata

### Performance Issues

If builds are slow:

1. **Use development builds** for testing: `--dev` flag
2. **Clean build cache**: `./scripts/build.sh clean`
3. **Check disk space**: Ensure adequate free space
4. **Update Flutter**: May be done automatically by Flet

### Dependencies Issues

Common dependency problems:

```bash
# Update all dependencies  
uv sync

# Force reinstall
uv sync --reinstall

# Check for conflicts
uv pip check
```

## Continuous Integration

### GitHub Actions (Example)

Create `.github/workflows/build.yml`:

```yaml
name: Build DANA Journal
on:
  push:
    tags: ['v*']
  workflow_dispatch:

jobs:
  build:
    runs-on: ${{ matrix.os }}
    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
    
    steps:
    - uses: actions/checkout@v4
    - name: Install uv
      uses: astral-sh/setup-uv@v3
    - name: Install dependencies  
      run: uv sync
    - name: Build application
      run: ./scripts/build.sh ${{ matrix.platform }} --prod
    - name: Upload artifacts
      uses: actions/upload-artifact@v4
      with:
        name: dana-journal-${{ matrix.platform }}
        path: dist/
```

## Security Considerations

### Code Signing

#### macOS
Configure in `pyproject.toml`:
```toml
[tool.flet.build.macos]
codesign_identity = "Developer ID Application: Your Name"
```

#### Windows
Use Windows SDK signing tools:
```bash
signtool sign /f certificate.pfx dist/dana-journal.exe
```

### Integrity Verification

Generate checksums for releases:
```bash
# SHA256 checksums
cd dist/
shasum -a 256 * > checksums.sha256
```

### Privacy Compliance

DANA Journal is privacy-first:
- **No telemetry** by default
- **Local-only data** processing  
- **No external dependencies** for core functionality
- **User consent** for any network features

## Support

For build issues and questions:
- **Documentation**: Check this guide and `CLAUDE.md`
- **Issues**: GitHub Issues for bug reports
- **Development**: See `ARCHITECTURE.md` for codebase details

---

*Last updated: 2025-01-14*
*DANA Journal Version: 0.1.0*