"""
AI Journal Vault - Main Application Entry Point

A privacy-first desktop journaling application with local AI-powered insights.
"""

import flet as ft
from ui.theme import theme_manager, ThemedContainer, ThemedText, create_theme_toggle_button


class JournalVaultApp:
    """Main application class for AI Journal Vault."""
    
    def __init__(self, page: ft.Page):
        self.page = page
        self.theme_manager = theme_manager
        
        # Configure page
        self._setup_page()
        
        # Create main layout
        self._create_layout()
    
    def _setup_page(self) -> None:
        """Configure page properties and theme."""
        self.page.title = "AI Journal Vault"
        self.page.window.width = 1400
        self.page.window.height = 900
        self.page.window.min_width = 1000
        self.page.window.min_height = 700
        self.page.window.center()
        self.page.padding = 0
        self.page.spacing = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START
        
        # Apply theme colors
        colors = self.theme_manager.colors
        self.page.bgcolor = colors.background
        
        # Listen for theme changes
        self.theme_manager.add_observer(self._on_theme_changed)
    
    def _create_layout(self) -> None:
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
                    ft.Row(
                        controls=[
                            create_theme_toggle_button(self.theme_manager),
                        ],
                        spacing=10
                    )
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
        calendar_panel = ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "Calendar",
                        variant="primary",
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    ThemedText(
                        self.theme_manager,
                        "Calendar view will go here",
                        variant="secondary",
                        size=12
                    )
                ],
                spacing=12,
                tight=True
            ),
            width=320,
            padding=ft.padding.all(20),
            border=ft.border.only(right=ft.border.BorderSide(1, colors.border_subtle))
        )
        
        # Right panel - Journal Editor
        editor_panel = ThemedContainer(
            self.theme_manager,
            variant="background",
            content=ft.Column(
                controls=[
                    ThemedText(
                        self.theme_manager,
                        "Journal Entry",
                        variant="primary",
                        size=16,
                        weight=ft.FontWeight.W_500
                    ),
                    ThemedContainer(
                        self.theme_manager,
                        variant="surface",
                        content=ThemedText(
                            self.theme_manager,
                            "Journal editor will go here...\n\nThis is where users will write their daily entries.",
                            variant="primary",
                            size=14
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
    
    def _on_theme_changed(self, theme_name: str, colors) -> None:
        """Handle theme change."""
        self.page.bgcolor = colors.background
        
        # Force update of all components
        try:
            self.page.update()
        except Exception as e:
            print(f"Error updating page on theme change: {e}")
    
    def run(self) -> None:
        """Run the application."""
        self.page.update()


def main(page: ft.Page) -> None:
    """Main application entry point."""
    app = JournalVaultApp(page)
    app.run()


if __name__ == "__main__":
    ft.app(target=main)