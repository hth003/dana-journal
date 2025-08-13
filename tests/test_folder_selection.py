#!/usr/bin/env python3
"""
Test script to debug folder selection functionality
"""

import os
import flet as ft


def test_folder_selection(page: ft.Page):
    """Test the folder selection functionality."""

    def on_folder_selected(result: ft.FilePickerResultEvent):
        print(f"Folder selected: {result.path}")
        if result.path:
            result_text.value = f"Selected: {result.path}"
        else:
            result_text.value = "No folder selected"
        result_text.update()

    # Create file picker
    file_picker = ft.FilePicker(on_result=on_folder_selected)

    # Add to page overlay
    page.overlay.append(file_picker)

    # Create UI
    result_text = ft.Text("No folder selected yet")

    def select_folder(e):
        print("Select folder button clicked")
        try:
            file_picker.get_directory_path(dialog_title="Choose Folder")
            print("Directory picker opened")
        except Exception as ex:
            print(f"Error opening directory picker: {ex}")

    def use_default(e):
        print("Use default button clicked")
        default_path = os.path.expanduser("~/Documents/Journal Vault")
        print(f"Default path: {default_path}")

        # Create directory if it doesn't exist
        if not os.path.exists(default_path):
            os.makedirs(default_path, exist_ok=True)
            print(f"Created directory: {default_path}")

        result_text.value = f"Default: {default_path}"
        result_text.update()

    page.add(
        ft.Column(
            [
                ft.Text("Folder Selection Test", size=20, weight=ft.FontWeight.BOLD),
                ft.Container(height=20),
                ft.ElevatedButton("Choose Folder", on_click=select_folder),
                ft.Container(height=10),
                ft.OutlinedButton("Use Default", on_click=use_default),
                ft.Container(height=20),
                result_text,
            ]
        )
    )


def main(page: ft.Page):
    page.title = "Folder Selection Test"
    page.padding = 50
    test_folder_selection(page)


if __name__ == "__main__":
    ft.app(target=main)
