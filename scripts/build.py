#!/usr/bin/env python3
"""
DANA Journal Build Script

This script provides automated building for different platforms and environments.
Usage: python scripts/build.py [platform] [--dev|--prod] [--verbose]
"""

import argparse
import subprocess
import sys
from pathlib import Path
import shutil
import json


class BuildScript:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.build_dir = self.project_root / "build"
        self.dist_dir = self.project_root / "dist"
        
    def clean_build_dirs(self):
        """Clean previous build directories"""
        for directory in [self.build_dir, self.dist_dir]:
            if directory.exists():
                try:
                    shutil.rmtree(directory)
                    print(f"Cleaned {directory}")
                except (OSError, PermissionError) as e:
                    print(f"Warning: Could not fully clean {directory}: {e}")
                    # Try to fix permissions and retry
                    try:
                        import subprocess
                        subprocess.run(['chmod', '-R', '755', str(directory)], check=False)
                        shutil.rmtree(directory)
                        print(f"Cleaned {directory} after permission fix")
                    except Exception as e2:
                        print(f"Error: Failed to clean {directory}: {e2}")
                        print("Please manually remove the directory and try again")
                        return False
            directory.mkdir(exist_ok=True)
        return True
    
    def increment_build_number(self):
        """Increment build number in pyproject.toml"""
        pyproject_path = self.project_root / "pyproject.toml"
        
        # Read current content
        with open(pyproject_path, 'r') as f:
            content = f.read()
        
        # Simple regex replacement for build number
        import re
        pattern = r'build_number = (\d+)'
        match = re.search(pattern, content)
        
        if match:
            current_build = int(match.group(1))
            new_build = current_build + 1
            new_content = re.sub(pattern, f'build_number = {new_build}', content)
            
            with open(pyproject_path, 'w') as f:
                f.write(new_content)
            
            print(f"Build number incremented from {current_build} to {new_build}")
            return new_build
        else:
            print("Warning: Could not find build_number in pyproject.toml")
            return 1
    
    def run_build(self, platform, verbose=False, production=True):
        """Run flet build command for specified platform"""
        cmd = ["uv", "run", "flet", "build", platform]
        
        if verbose:
            cmd.append("--verbose")
        
        if production:
            # Add production-specific flags
            cmd.extend(["--no-rich-output"])
        
        print(f"Running build command: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, check=True, capture_output=True, text=True)
            print("Build completed successfully!")
            if verbose and result.stdout:
                print("Build output:")
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Build failed with error code {e.returncode}")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            return False
    
    def create_build_info(self, platform, build_number, version):
        """Create build information file"""
        build_info = {
            "platform": platform,
            "version": version,
            "build_number": build_number,
            "build_timestamp": subprocess.check_output(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"]).decode().strip(),
            "git_commit": self.get_git_commit(),
            "python_version": sys.version.split()[0],
        }
        
        info_file = self.dist_dir / f"build_info_{platform}.json"
        with open(info_file, 'w') as f:
            json.dump(build_info, f, indent=2)
        
        print(f"Build info saved to {info_file}")
    
    def get_git_commit(self):
        """Get current git commit hash"""
        try:
            return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=self.project_root).decode().strip()
        except subprocess.CalledProcessError:
            return "unknown"
    
    def build_for_platform(self, platform, dev_mode=False, verbose=False):
        """Complete build process for a platform"""
        print(f"\n=== Building DANA Journal for {platform.upper()} ===")
        
        # Clean build directories
        if not self.clean_build_dirs():
            return False
        
        # Increment build number for production builds
        if not dev_mode:
            build_number = self.increment_build_number()
        else:
            build_number = 0  # Development build
        
        # Run the build
        success = self.run_build(platform, verbose=verbose, production=not dev_mode)
        
        if success:
            # Create build info
            self.create_build_info(platform, build_number, "0.1.0")  # Version from pyproject.toml
            print(f"\n✅ Build completed successfully for {platform}")
            
            # Show build artifacts location
            if platform == "macos":
                build_path = self.project_root / "dist" / "dana-journal.app"
            elif platform == "windows":
                build_path = self.project_root / "dist" / "dana-journal.exe"
            elif platform == "linux":
                build_path = self.project_root / "dist" / "dana-journal"
            elif platform == "web":
                build_path = self.project_root / "dist" / "web"
            else:
                build_path = self.project_root / "dist"
            
            print(f"Build artifacts: {build_path}")
            
        else:
            print(f"\n❌ Build failed for {platform}")
            return False
        
        return True


def main():
    parser = argparse.ArgumentParser(description="Build DANA Journal for different platforms")
    parser.add_argument("platform", choices=["macos", "windows", "linux", "web", "apk", "aab", "ipa"], 
                       help="Target platform to build for")
    parser.add_argument("--dev", action="store_true", help="Development build (faster, no optimizations)")
    parser.add_argument("--prod", action="store_true", help="Production build (default)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose build output")
    parser.add_argument("--clean", action="store_true", help="Clean build directories only")
    
    args = parser.parse_args()
    
    builder = BuildScript()
    
    if args.clean:
        builder.clean_build_dirs()
        print("Build directories cleaned.")
        return
    
    # Default to production unless --dev is specified
    dev_mode = args.dev and not args.prod
    
    success = builder.build_for_platform(args.platform, dev_mode=dev_mode, verbose=args.verbose)
    
    if success:
        print(f"\n🎉 DANA Journal build complete for {args.platform}!")
    else:
        print(f"\n💥 Build failed for {args.platform}")
        sys.exit(1)


if __name__ == "__main__":
    main()