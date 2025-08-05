#!/usr/bin/env python3
"""
Test file picker functionality on macOS
"""

import flet as ft
import os
import time
import subprocess

def test_file_picker(page: ft.Page):
    """Test the file picker functionality."""
    
    # Force window to be visible and on top
    page.window_always_on_top = True
    page.window_focused = True
    page.update()
    
    def on_folder_selected(result: ft.FilePickerResultEvent):
        print(f"Folder selected: {result.path}")
        if result.path:
            result_text.value = f"Selected: {result.path}"
        else:
            result_text.value = "No folder selected (cancelled)"
        result_text.update()
    
    # Create file picker
    file_picker = ft.FilePicker(on_result=on_folder_selected)
    
    # Add to page overlay
    page.overlay.append(file_picker)
    page.update()
    
    # Create UI
    result_text = ft.Text("No folder selected yet")
    
    def select_folder_basic(e):
        print("Opening directory picker (basic)...")
        print("Window should be visible and on top")
        try:
            # Force window to front
            page.window_focused = True
            page.update()
            time.sleep(0.5)  # Give time for window to come to front
            
            file_picker.get_directory_path()
            print("Directory picker opened successfully")
        except Exception as ex:
            print(f"Error opening directory picker: {ex}")
            result_text.value = f"Error: {ex}"
            result_text.update()
    
    def select_folder_with_title(e):
        print("Opening directory picker (with title)...")
        try:
            # Force window to front
            page.window_focused = True
            page.update()
            time.sleep(0.5)
            
            file_picker.get_directory_path(dialog_title="Choose Folder")
            print("Directory picker opened successfully")
        except Exception as ex:
            print(f"Error opening directory picker: {ex}")
            result_text.value = f"Error: {ex}"
            result_text.update()
    
    def select_folder_with_initial_dir(e):
        print("Opening directory picker (with initial directory)...")
        try:
            # Force window to front
            page.window_focused = True
            page.update()
            time.sleep(0.5)
            
            file_picker.get_directory_path(
                dialog_title="Choose Folder",
                initial_directory=os.path.expanduser("~/Documents")
            )
            print("Directory picker opened successfully")
        except Exception as ex:
            print(f"Error opening directory picker: {ex}")
            result_text.value = f"Error: {ex}"
            result_text.update()
    
    def test_file_picker(e):
        print("Opening file picker...")
        try:
            # Force window to front
            page.window_focused = True
            page.update()
            time.sleep(0.5)
            
            file_picker.pick_files()
            print("File picker opened successfully")
        except Exception as ex:
            print(f"Error opening file picker: {ex}")
            result_text.value = f"Error: {ex}"
            result_text.update()
    
    def test_native_dialog(e):
        """Test if we can open a native dialog using subprocess"""
        print("Testing native dialog with subprocess...")
        try:
            # Try to open a native dialog using osascript
            result = subprocess.run([
                "osascript", "-e", 
                'choose folder with prompt "Choose a folder"'
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                selected_path = result.stdout.strip()
                result_text.value = f"Native dialog selected: {selected_path}"
                print(f"Native dialog selected: {selected_path}")
            else:
                result_text.value = f"Native dialog failed: {result.stderr}"
                print(f"Native dialog failed: {result.stderr}")
            result_text.update()
        except Exception as ex:
            result_text.value = f"Native dialog error: {ex}"
            print(f"Native dialog error: {ex}")
            result_text.update()
    
    page.add(
        ft.Column([
            ft.Text("File Picker Test", size=20, weight=ft.FontWeight.BOLD),
            ft.Text("Window should be on top and visible", size=12, color="red"),
            ft.Container(height=20),
            ft.ElevatedButton("Basic Directory Picker", on_click=select_folder_basic),
            ft.Container(height=10),
            ft.ElevatedButton("Directory Picker with Title", on_click=select_folder_with_title),
            ft.Container(height=10),
            ft.ElevatedButton("Directory Picker with Initial Dir", on_click=select_folder_with_initial_dir),
            ft.Container(height=10),
            ft.ElevatedButton("File Picker (for comparison)", on_click=test_file_picker),
            ft.Container(height=10),
            ft.ElevatedButton("Native Dialog (osascript)", on_click=test_native_dialog),
            ft.Container(height=20),
            result_text
        ])
    )

def main(page: ft.Page):
    page.title = "File Picker Test"
    page.padding = 50
    page.window_width = 600
    page.window_height = 500
    test_file_picker(page)

if __name__ == "__main__":
    ft.app(target=main) 