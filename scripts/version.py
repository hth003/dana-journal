#!/usr/bin/env python3
"""
DANA Journal Version Management Script

This script helps manage semantic versioning for the DANA Journal application.
It updates version numbers in pyproject.toml and creates git tags.

Usage: 
  python scripts/version.py current                    # Show current version
  python scripts/version.py bump [major|minor|patch]   # Bump version
  python scripts/version.py set 1.2.3                  # Set specific version
  python scripts/version.py tag                        # Create git tag
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Tuple


class VersionManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.pyproject_path = self.project_root / "pyproject.toml"
    
    def parse_version(self, version_string: str) -> Tuple[int, int, int]:
        """Parse semantic version string into components"""
        match = re.match(r'^(\d+)\.(\d+)\.(\d+)(?:-.*)?$', version_string.strip())
        if not match:
            raise ValueError(f"Invalid version format: {version_string}")
        return int(match.group(1)), int(match.group(2)), int(match.group(3))
    
    def format_version(self, major: int, minor: int, patch: int) -> str:
        """Format version components into semantic version string"""
        return f"{major}.{minor}.{patch}"
    
    def get_current_version(self) -> str:
        """Get current version from pyproject.toml"""
        with open(self.pyproject_path, 'r') as f:
            content = f.read()
        
        # Look for version in [project] section
        match = re.search(r'^version = ["\']([^"\']+)["\']', content, re.MULTILINE)
        if not match:
            raise RuntimeError("Could not find version in pyproject.toml")
        
        return match.group(1)
    
    def update_version_in_file(self, new_version: str):
        """Update version in pyproject.toml"""
        with open(self.pyproject_path, 'r') as f:
            content = f.read()
        
        # Update version in [project] section
        content = re.sub(
            r'^version = ["\'][^"\']+["\']',
            f'version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        
        # Update build_version in [tool.flet] section if it exists
        content = re.sub(
            r'^build_version = ["\'][^"\']+["\']',
            f'build_version = "{new_version}"',
            content,
            flags=re.MULTILINE
        )
        
        with open(self.pyproject_path, 'w') as f:
            f.write(content)
        
        print(f"Updated version to {new_version} in {self.pyproject_path}")
    
    def bump_version(self, bump_type: str) -> str:
        """Bump version according to semantic versioning rules"""
        current_version = self.get_current_version()
        major, minor, patch = self.parse_version(current_version)
        
        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1
        else:
            raise ValueError(f"Invalid bump type: {bump_type}. Use major, minor, or patch.")
        
        new_version = self.format_version(major, minor, patch)
        self.update_version_in_file(new_version)
        
        return new_version
    
    def set_version(self, version: str) -> str:
        """Set specific version"""
        # Validate version format
        self.parse_version(version)
        self.update_version_in_file(version)
        return version
    
    def create_git_tag(self, version: str = None) -> bool:
        """Create git tag for current version"""
        if version is None:
            version = self.get_current_version()
        
        tag_name = f"v{version}"
        
        try:
            # Check if tag already exists
            result = subprocess.run(
                ["git", "tag", "-l", tag_name],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                print(f"Warning: Tag {tag_name} already exists")
                return False
            
            # Create annotated tag
            subprocess.run(
                ["git", "tag", "-a", tag_name, "-m", f"Release version {version}"],
                cwd=self.project_root,
                check=True
            )
            
            print(f"Created git tag: {tag_name}")
            print("To push the tag, run: git push origin --tags")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Error creating git tag: {e}")
            return False
    
    def show_version_info(self):
        """Show comprehensive version information"""
        current_version = self.get_current_version()
        major, minor, patch = self.parse_version(current_version)
        
        print(f"Current Version: {current_version}")
        print(f"  Major: {major}")
        print(f"  Minor: {minor}")
        print(f"  Patch: {patch}")
        
        # Show git information if available
        try:
            git_commit = subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=self.project_root,
                text=True
            ).strip()
            
            git_branch = subprocess.check_output(
                ["git", "branch", "--show-current"],
                cwd=self.project_root,
                text=True
            ).strip()
            
            print(f"  Git Branch: {git_branch}")
            print(f"  Git Commit: {git_commit}")
            
            # Check for uncommitted changes
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            
            if result.stdout.strip():
                print("  Status: ⚠️  Uncommitted changes")
            else:
                print("  Status: ✅ Clean working directory")
                
        except subprocess.CalledProcessError:
            print("  Git: Not in a git repository")
        
        # Show next possible versions
        next_patch = self.format_version(major, minor, patch + 1)
        next_minor = self.format_version(major, minor + 1, 0)
        next_major = self.format_version(major + 1, 0, 0)
        
        print(f"\nNext versions:")
        print(f"  Patch: {next_patch}")
        print(f"  Minor: {next_minor}")  
        print(f"  Major: {next_major}")


def main():
    parser = argparse.ArgumentParser(description="Manage DANA Journal version")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Current version command
    subparsers.add_parser("current", help="Show current version information")
    
    # Bump version command
    bump_parser = subparsers.add_parser("bump", help="Bump version")
    bump_parser.add_argument("type", choices=["major", "minor", "patch"], 
                           help="Type of version bump")
    
    # Set version command
    set_parser = subparsers.add_parser("set", help="Set specific version")
    set_parser.add_argument("version", help="Version to set (e.g., 1.2.3)")
    
    # Tag command
    tag_parser = subparsers.add_parser("tag", help="Create git tag for current version")
    tag_parser.add_argument("--version", help="Specific version to tag (default: current)")
    
    # Release command (bump + tag)
    release_parser = subparsers.add_parser("release", help="Bump version and create git tag")
    release_parser.add_argument("type", choices=["major", "minor", "patch"],
                               help="Type of version bump for release")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    version_manager = VersionManager()
    
    try:
        if args.command == "current":
            version_manager.show_version_info()
            
        elif args.command == "bump":
            new_version = version_manager.bump_version(args.type)
            print(f"Version bumped to {new_version}")
            
        elif args.command == "set":
            new_version = version_manager.set_version(args.version)
            print(f"Version set to {new_version}")
            
        elif args.command == "tag":
            tag_version = args.version if hasattr(args, 'version') and args.version else None
            success = version_manager.create_git_tag(tag_version)
            if not success:
                sys.exit(1)
                
        elif args.command == "release":
            print(f"Creating {args.type} release...")
            new_version = version_manager.bump_version(args.type)
            print(f"Version bumped to {new_version}")
            
            success = version_manager.create_git_tag(new_version)
            if success:
                print(f"🎉 Release {new_version} created successfully!")
                print("Don't forget to:")
                print("  1. Push the changes: git push")
                print("  2. Push the tag: git push origin --tags")
                print("  3. Create release notes")
                print("  4. Build and distribute packages")
            else:
                print("⚠️  Tag creation failed, but version was updated")
                sys.exit(1)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()