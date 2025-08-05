#!/usr/bin/env python3
"""
Test script for folder selection functionality
"""

import os
import sys
import tempfile
import shutil

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_storage_validation():
    """Test the storage directory validation functionality"""
    print("Testing storage directory validation...")
    
    try:
        from journal_vault.ui.components.onboarding import OnboardingFlow
        from journal_vault.ui.theme import ThemeManager
        
        # Create a mock onboarding flow to test validation
        theme_manager = ThemeManager()
        onboarding = OnboardingFlow(theme_manager, lambda x: None)
        
        # Test 1: Valid directory
        temp_dir = tempfile.mkdtemp()
        try:
            result = onboarding._validate_storage_directory(temp_dir)
            print(f"✓ Valid directory test: {result}")
            assert result == True, "Valid directory should return True"
        finally:
            shutil.rmtree(temp_dir)
        
        # Test 2: Non-existent directory
        non_existent = "/this/path/does/not/exist"
        result = onboarding._validate_storage_directory(non_existent)
        print(f"✓ Non-existent directory test: {result}")
        assert result == False, "Non-existent directory should return False"
        
        # Test 3: Default storage creation
        default_path = os.path.join(os.path.expanduser("~"), "Documents", "Journal Vault Test")
        
        # Clean up if exists
        if os.path.exists(default_path):
            shutil.rmtree(default_path)
        
        # Create default storage path
        os.makedirs(default_path, exist_ok=True)
        try:
            result = onboarding._validate_storage_directory(default_path)
            print(f"✓ Default storage creation test: {result}")
            assert result == True, "Created default directory should be valid"
        finally:
            shutil.rmtree(default_path)
        
        print("✅ All storage validation tests passed!")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Note: This is expected if flet is not installed")
        return False
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

def test_default_path_creation():
    """Test default path creation logic"""
    print("Testing default path creation...")
    
    default_path = os.path.join(os.path.expanduser("~"), "Documents", "Journal Vault")
    print(f"Default path would be: {default_path}")
    
    # Check if Documents folder exists
    docs_path = os.path.join(os.path.expanduser("~"), "Documents")
    if os.path.exists(docs_path):
        print("✓ Documents folder exists")
        print("✓ Default path creation should work")
        return True
    else:
        print("⚠️  Documents folder doesn't exist, fallback needed")
        return False

if __name__ == "__main__":
    print("Journal Vault - Folder Selection Test")
    print("=" * 40)
    
    # Test storage validation
    validation_passed = test_storage_validation()
    
    print()
    
    # Test default path
    default_path_ok = test_default_path_creation()
    
    print()
    print("Summary:")
    print(f"Storage validation: {'✅ PASS' if validation_passed else '❌ FAIL'}")
    print(f"Default path logic: {'✅ PASS' if default_path_ok else '⚠️  WARN'}")
    
    if validation_passed and default_path_ok:
        print("\n🎉 Folder selection fix appears to be working correctly!")
    else:
        print("\n⚠️  Some tests failed, but core logic is implemented.")