"""
AI Journal Vault - Main Application Entry Point

A privacy-first desktop journaling application with local AI-powered insights.
"""

import os
from datetime import datetime, timedelta
from typing import Set
import flet as ft
from .ui.theme import theme_manager, ThemedContainer, ThemedText
from .ui.components import OnboardingFlow, CalendarComponent
from .config import app_config


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
        
        # Header with title and date
        header = ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Row(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "AI Journal Vault",
                        variant="primary",
                        size=20,
                        weight=ft.FontWeight.W_600
                    ),
                    ft.Container()  # Empty container for spacing
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.all(20),
            border=ft.border.only(bottom=ft.border.BorderSide(1, colors.border_subtle)),
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=4,
                color=colors.shadow_light,
                offset=ft.Offset(0, 1),
            )
        )
        
        # Left sidebar - Calendar and Files
        self.calendar_component = CalendarComponent(
            self.theme_manager,
            on_date_selected=self._on_date_selected,
            entry_dates=self.entry_dates
        )
        
        # Calendar section
        calendar_section = ft.Container(
            content=self.calendar_component.get_container(),
            padding=ft.padding.all(16)
        )
        
        # Files section
        files_section = ft.Container(
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "Files",
                        variant="primary",
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Container(height=8),
                    ThemedContainer(
                        self.theme_manager,
                        variant="surface",
                        content=ft.Text(
                            "Journal files will appear here",
                            color=colors.text_muted,
                            size=12
                        ),
                        padding=ft.padding.all(16),
                        border_radius=8,
                        border=ft.border.all(1, colors.border_subtle),
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            padding=ft.padding.all(16),
            expand=True
        )
        
        # Left sidebar container
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
            width=280,
            border=ft.border.only(right=ft.border.BorderSide(1, colors.border_subtle))
        )
        
        # Main content area - Journal Entry and AI Reflection
        # Journal Entry section
        journal_entry_section = ft.Container(
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "Journal Entry",
                        variant="primary",
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Container(height=8),
                    ThemedContainer(
                        self.theme_manager,
                        variant="surface",
                        content=ft.Column(
                            controls=[
                                ft.TextField(
                                    hint_text="Start writing your thoughts for today...",
                                    multiline=True,
                                    min_lines=10,
                                    max_lines=None,
                                    border=ft.InputBorder.NONE,
                                    hint_style=ft.TextStyle(color=colors.text_muted),
                                    text_style=ft.TextStyle(
                                        color=colors.text_primary,
                                        size=14
                                    ),
                                    bgcolor="transparent",
                                    expand=True
                                )
                            ],
                            expand=True
                        ),
                        padding=ft.padding.all(20),
                        border_radius=8,
                        border=ft.border.all(1, colors.border_subtle),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=2,
                            color=colors.shadow_light,
                            offset=ft.Offset(0, 1),
                        ),
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            padding=ft.padding.all(16),
            expand=True
        )
        
        # AI Reflection section
        ai_reflection_section = ft.Container(
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "AI Reflection",
                        variant="primary",
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Container(height=8),
                    ThemedContainer(
                        self.theme_manager,
                        variant="surface",
                        content=ft.Column(
                            controls=[
                                ThemedText(
                                    self.theme_manager,
                                    "AI-powered insights and reflection questions will appear here.",
                                    variant="secondary",
                                    size=12
                                )
                            ],
                            expand=True
                        ),
                        padding=ft.padding.all(20),
                        border_radius=8,
                        border=ft.border.all(1, colors.border_subtle),
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=2,
                            color=colors.shadow_light,
                            offset=ft.Offset(0, 1),
                        ),
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            padding=ft.padding.all(16),
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
    
    def _on_date_selected(self, selected_date: datetime) -> None:
        """Handle date selection from calendar."""
        self.selected_date = selected_date
        
        # Here you would typically load the entry for the selected date
        # For now, we'll just update the UI to reflect the selection
        print(f"Selected date: {selected_date.strftime('%Y-%m-%d')}")
    
    
    def run(self) -> None:
        """Run the application."""
        self.page.update()


def main(page: ft.Page) -> None:
    """Main application entry point."""
    app = JournalVaultApp(page)
    app.run()


if __name__ == "__main__":
    ft.app(target=main)