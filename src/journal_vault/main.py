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
        """Create the main three-panel layout."""
        colors = self.theme_manager.colors
        
        # Header with title and theme toggle
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
                    ft.Container()  # Empty container instead of theme toggle
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
        
        # Left panel - Calendar
        self.calendar_component = CalendarComponent(
            self.theme_manager,
            on_date_selected=self._on_date_selected,
            entry_dates=self.entry_dates
        )
        
        calendar_panel = ft.Container(
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "Calendar",
                        variant="primary",
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    ft.Container(height=5),
                    self.calendar_component.get_container()
                ],
                spacing=0,
                tight=True
            ),
            width=320,
            padding=ft.padding.only(top=20, left=20, right=0, bottom=20)
        )
        
        # Right panel - Journal Editor
        self.editor_panel = ThemedContainer(
            self.theme_manager,
            variant="background",
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ThemedText(
                                self.theme_manager,
                                "Journal Entry",
                                variant="primary",
                                size=16,
                                weight=ft.FontWeight.W_500
                            ),
                            ThemedText(
                                self.theme_manager,
                                self.selected_date.strftime("%B %d, %Y"),
                                variant="secondary",
                                size=14
                            )
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
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
                spacing=12,
                expand=True
            ),
            expand=True,
            padding=ft.padding.all(20)
        )
        
        editor_panel = self.editor_panel
        
        # Main content area (calendar + editor)
        main_content = ft.Row(
            controls=[calendar_panel, editor_panel],
            spacing=0,
            expand=True,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
        
        # Bottom panel - AI Reflection
        ai_panel = ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "AI Reflection",
                        variant="primary",
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    ThemedText(
                        self.theme_manager,
                        "AI-powered insights and reflection questions will appear here.",
                        variant="secondary",
                        size=12
                    )
                ],
                spacing=12,
                tight=True
            ),
            height=220,
            padding=ft.padding.all(20),
            border=ft.border.only(top=ft.border.BorderSide(1, colors.border_subtle))
        )
        
        # Main layout
        main_layout = ft.Column(
            controls=[
                header,
                main_content,
                ai_panel
            ],
            spacing=0,
            expand=True
        )
        
        self.page.add(main_layout)
    
    def _on_date_selected(self, selected_date: datetime) -> None:
        """Handle date selection from calendar."""
        self.selected_date = selected_date
        
        # Update the editor panel header with the new date
        if self.editor_panel and len(self.editor_panel.content.controls) > 0:
            header_row = self.editor_panel.content.controls[0]
            if isinstance(header_row, ft.Row) and len(header_row.controls) > 1:
                date_text = header_row.controls[1]
                if hasattr(date_text, 'value'):
                    date_text.value = selected_date.strftime("%B %d, %Y")
                    date_text.update()
        
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