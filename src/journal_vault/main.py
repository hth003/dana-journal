"""
AI Journal Vault - Main Application Entry Point

A privacy-first desktop journaling application with local AI-powered insights.
"""

import os
from datetime import datetime, timedelta
from typing import Set
import flet as ft
from .ui.theme import theme_manager, ThemedContainer, ThemedText, ThemedCard, SPACING, COMPONENT_SIZES
from .ui.components import OnboardingFlow, CalendarComponent, EnhancedTextEditor, FileExplorer
from .config import app_config
from .storage.file_manager import FileManager


class JournalVaultApp:
    """Main application class for AI Journal Vault."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.theme_manager = theme_manager
        
        # App state
        self.is_onboarded = app_config.is_onboarded()
        self.storage_path = app_config.get_storage_path()
        self.selected_date = datetime.now()
        # Sample entry dates for demo purposes
        # In real implementation, this would be loaded from storage
        self.entry_dates: Set[datetime] = {
            datetime.now() - timedelta(days=1),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=7),
            datetime.now() - timedelta(days=10),
        }
        
        # No theme configuration needed - always dark mode
        
        # UI components
        self.calendar_component = None
        self.onboarding_flow = None
        self.text_editor = None
        self.file_explorer = None
        self.file_manager = None
        
        # Current entry state
        self.current_entry_date = self.selected_date.date()
        self.current_entry_content = ""
        
        # Configure page
        self._setup_page()
        
        # Create appropriate layout
        if self.is_onboarded:
            self._create_main_layout()
        else:
            self._create_onboarding_layout()
    
    def _setup_page(self) -> None:
        """Configure page properties and theme."""
        self.page.title = "AI Journal Vault"
        # Apply saved window state
        window_state = app_config.get_window_state()
        self.page.window.width = window_state.get('width', 1400)
        self.page.window.height = window_state.get('height', 900)
        self.page.window.min_width = 1000
        self.page.window.min_height = 700
        self.page.window.center()
        
        # Listen for window close to save state
        def on_window_event(e):
            if e.data == "close":
                try:
                    app_config.set_window_state(
                        self.page.window.width or 1400,
                        self.page.window.height or 900
                    )
                except Exception as ex:
                    print(f"Error saving window state: {ex}")
        
        self.page.window.on_event = on_window_event
        self.page.padding = 0
        self.page.spacing = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        
        # Apply dark theme colors
        colors = self.theme_manager.colors
        self.page.bgcolor = colors.background
    
    
    def _create_onboarding_layout(self) -> None:
        """Create the onboarding flow layout."""
        self.onboarding_flow = OnboardingFlow(
            self.theme_manager,
            on_complete=self._on_onboarding_complete,
            page=self.page
        )
        
        # Set up page overlays for file picker
        self.onboarding_flow.setup_page_overlays(self.page)
        
        self.page.add(self.onboarding_flow.get_container())
    
    def _on_onboarding_complete(self, onboarding_data: dict) -> None:
        """Handle onboarding completion."""
        # Save onboarding data using config system
        self.storage_path = onboarding_data.get('storage_path')
        app_config.set_storage_path(self.storage_path)
        
        # No theme preference to save - always dark mode
        
        # Mark onboarding as complete
        app_config.set_onboarded(True)
        
        # Initialize file manager with storage path
        self.file_manager = FileManager(self.storage_path)
        
        # Clear page and create main layout
        self.page.clean()
        self.is_onboarded = True
        
        # Reset page overlays since they were cleared
        if hasattr(self.page, 'overlay') and self.page.overlay:
            self.page.overlay.clear()
        
        # Re-apply theme colors after clearing page
        colors = self.theme_manager.colors
        self.page.bgcolor = colors.background
        
        # Re-apply page configuration that might have been lost
        self.page.padding = 0
        self.page.spacing = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        
        self._create_main_layout()
        self.page.update()
    
    
    def _create_main_layout(self) -> None:
        """Create the main three-panel layout with Obsidian-like design."""
        colors = self.theme_manager.colors
        
        # Header with consistent spacing and typography
        header = ThemedContainer(
            self.theme_manager,
            variant="surface",
            elevation="sm",
            content=ft.Row(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "AI Journal Vault",
                        variant="primary",
                        typography="h3"
                    ),
                    ft.Container()  # Empty container for spacing
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            spacing="lg",
            border=ft.border.only(bottom=ft.border.BorderSide(1, colors.border_subtle))
        )
        
        # Initialize file manager if not already done
        if not self.file_manager:
            self.file_manager = FileManager(self.storage_path)
        
        # Get actual entry dates from file manager
        actual_entry_dates = self.file_manager.get_entry_dates()
        
        # Left sidebar - Calendar and Files
        self.calendar_component = CalendarComponent(
            self.theme_manager,
            on_date_selected=self._on_date_selected,
            entry_dates=actual_entry_dates
        )
        
        # File manager for file operations
        self.file_manager = FileManager(self.storage_path)
        
        # File explorer component
        self.file_explorer = FileExplorer(
            self.theme_manager,
            file_manager=self.file_manager,
            on_file_select=self._on_file_selected,
            on_create_entry=self._on_file_created
        )
        
        # Calendar section with consistent spacing
        calendar_section = ft.Container(
            content=self.calendar_component.get_container(),
            padding=ft.padding.all(SPACING["md"])
        )
        
        # Files section with file explorer
        files_section = ft.Container(
            content=self.file_explorer.get_container(),
            padding=ft.padding.all(SPACING["md"]),
            expand=True
        )
        
        # Left sidebar container with consistent sizing
        left_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    calendar_section,
                    ft.Container(
                        height=1,
                        bgcolor=colors.border_subtle
                    ),
                    files_section
                ],
                spacing=0,
                expand=True
            ),
            width=COMPONENT_SIZES["sidebar_width"],
            border=ft.border.only(right=ft.border.BorderSide(1, colors.border_subtle))
        )
        
        # Main content area - Enhanced Text Editor
        # Initialize text editor
        self.text_editor = EnhancedTextEditor(
            self.theme_manager,
            on_content_change=self._on_content_change,
            on_save=self._on_save_entry,
            placeholder_text=f"Start writing your thoughts for {self.current_entry_date.strftime('%B %d, %Y')}...",
            auto_save_delay=3.0,
            show_stats=True
        )
        
        journal_entry_section = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ThemedText(
                                self.theme_manager,
                                f"Journal Entry - {self.current_entry_date.strftime('%B %d, %Y')}",
                                variant="primary",
                                typography="h4"
                            ),
                            ft.Container(expand=True),
                            ft.TextButton(
                                text="Save",
                                on_click=self._manual_save,
                                style=ft.ButtonStyle(
                                    color=colors.primary,
                                    bgcolor={ft.ControlState.HOVERED: colors.hover}
                                )
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    ft.Container(height=SPACING["sm"]),
                    ft.Container(
                        content=self.text_editor.get_container(),
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            padding=ft.padding.all(SPACING["md"]),
            expand=True
        )
        
        # AI Reflection section with improved consistency
        ai_reflection_section = ft.Container(
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "AI Reflection",
                        variant="primary",
                        typography="h4"
                    ),
                    ft.Container(height=SPACING["sm"]),
                    ThemedCard(
                        self.theme_manager,
                        elevation="md",
                        content=ft.Column(
                            controls=[
                                ThemedText(
                                    self.theme_manager,
                                    "AI-powered insights and reflection questions will appear here.",
                                    variant="secondary",
                                    typography="body_sm"
                                )
                            ],
                            expand=True
                        ),
                        spacing="lg",
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            padding=ft.padding.all(SPACING["md"]),
            expand=True
        )
        
        # Main content area container
        main_content = ft.Container(
            content=ft.Column(
                controls=[
                    journal_entry_section,
                    ft.Container(
                        height=1,
                        bgcolor=colors.border_subtle
                    ),
                    ai_reflection_section
                ],
                spacing=0,
                expand=True
            ),
            expand=True
        )
        
        # Main layout with left sidebar and main content
        main_layout = ft.Column(
            controls=[
                header,
                ft.Row(
                    controls=[left_sidebar, main_content],
                    spacing=0,
                    expand=True
                )
            ],
            spacing=0,
            expand=True
        )
        
        self.page.add(main_layout)
        
        # Load initial entry
        if self.file_manager:
            self._load_entry_for_date(self.current_entry_date)
    
    def _on_date_selected(self, selected_date: datetime) -> None:
        """Handle date selection from calendar."""
        self.selected_date = selected_date
        new_date = selected_date.date()
        
        # Save current entry before switching
        if self.text_editor and self.current_entry_date != new_date:
            current_content = self.text_editor.get_content()
            if current_content.strip():  # Only save if there's content
                self._save_entry_for_date(self.current_entry_date, current_content)
        
        # Switch to new date
        self.current_entry_date = new_date
        
        # Load entry for new date
        self._load_entry_for_date(new_date)
        
        # Update text editor placeholder and title
        self._update_editor_for_date(new_date)
        
        # Update file explorer selection
        if self.file_explorer:
            self.file_explorer.select_entry_by_date(new_date)
        
        print(f"Selected date: {selected_date.strftime('%Y-%m-%d')}")
    
    def _on_file_selected(self, file_path, entry_date) -> None:
        """Handle file selection from file explorer."""
        if entry_date:
            # Update calendar and load entry
            self.selected_date = datetime.combine(entry_date, datetime.min.time())
            self.current_entry_date = entry_date
            
            # Load entry content
            self._load_entry_for_date(entry_date)
            
            # Update calendar selection
            if self.calendar_component:
                self.calendar_component.set_selected_date(self.selected_date)
            
            # Update text editor
            self._update_editor_for_date(entry_date)
            
            print(f"Selected file: {file_path} for date: {entry_date}")
    
    def _on_file_created(self, entry_date) -> None:
        """Handle new file creation."""
        # Create new entry
        if self.file_manager:
            try:
                entry = self.file_manager.create_entry(entry_date)
                
                # Update UI
                self._refresh_entry_dates()
                
                # Select the new entry
                self.selected_date = datetime.combine(entry_date, datetime.min.time())
                self._on_date_selected(self.selected_date)
                
                print(f"Created new entry for: {entry_date}")
            except Exception as e:
                print(f"Error creating entry: {e}")
    
    def _on_file_deleted(self, entry_date) -> None:
        """Handle file deletion."""
        # Delete entry from file manager
        if self.file_manager:
            try:
                self.file_manager.delete_entry(entry_date)
                
                # Update UI
                self._refresh_entry_dates()
                
                # Clear text editor if this was the current entry
                if self.current_entry_date == entry_date and self.text_editor:
                    self.text_editor.clear()
                
                print(f"Deleted entry for: {entry_date}")
            except Exception as e:
                print(f"Error deleting entry: {e}")
    
    def _on_content_change(self, content: str) -> None:
        """Handle text editor content changes."""
        self.current_entry_content = content
    
    def _on_save_entry(self, content: str) -> None:
        """Handle auto-save from text editor."""
        self._save_entry_for_date(self.current_entry_date, content)
    
    def _manual_save(self, e) -> None:
        """Handle manual save button click."""
        if self.text_editor:
            self.text_editor.save_now()
    
    def _load_entry_for_date(self, entry_date) -> None:
        """Load entry content for a specific date."""
        if not self.file_manager:
            return
        
        try:
            entry = self.file_manager.load_entry(entry_date)
            if entry:
                self.current_entry_content = entry.content
                if self.text_editor:
                    self.text_editor.set_content(entry.content)
            else:
                self.current_entry_content = ""
                if self.text_editor:
                    self.text_editor.clear()
        except Exception as e:
            print(f"Error loading entry for {entry_date}: {e}")
            self.current_entry_content = ""
            if self.text_editor:
                self.text_editor.clear()
    
    def _save_entry_for_date(self, entry_date, content: str) -> None:
        """Save entry content for a specific date."""
        if not self.file_manager or not content.strip():
            return
        
        try:
            # Load existing entry or create new one
            entry = self.file_manager.load_entry(entry_date)
            if entry:
                entry.content = content
                self.file_manager.save_entry(entry)
            else:
                self.file_manager.create_entry(entry_date, content=content)
            
            # Update entry dates in UI components
            self._refresh_entry_dates()
            
            print(f"Saved entry for {entry_date}")
        except Exception as e:
            print(f"Error saving entry for {entry_date}: {e}")
    
    def _update_editor_for_date(self, entry_date) -> None:
        """Update text editor for a specific date."""
        if not self.text_editor:
            return
        
        # Update placeholder text
        placeholder = f"Start writing your thoughts for {entry_date.strftime('%B %d, %Y')}..."
        # Note: Flet doesn't allow dynamic placeholder updates, so this is conceptual
        
        # Update header in the UI would require rebuilding the header section
        # For now, just print the date change
        print(f"Editor updated for date: {entry_date}")
    
    def _refresh_entry_dates(self) -> None:
        """Refresh entry dates in all UI components."""
        if not self.file_manager:
            return
        
        try:
            entry_dates = self.file_manager.get_entry_dates()
            
            # Update calendar
            if self.calendar_component:
                self.calendar_component.update_entry_dates(entry_dates)
            
            # Update file explorer
            if self.file_explorer:
                self.file_explorer.update_entry_dates(entry_dates)
                
        except Exception as e:
            print(f"Error refreshing entry dates: {e}")
    
    
    def run(self) -> None:
        """Run the application."""
        self.page.update()


def main(page: ft.Page) -> None:
    """Main application entry point."""
    app = JournalVaultApp(page)
    app.run()


if __name__ == "__main__":
    ft.app(target=main)