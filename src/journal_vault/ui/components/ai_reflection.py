"""
AI Reflection Component for AI Journal Vault

An inline component that displays AI-generated reflections below the text editor
with manual trigger support and persistent display.
"""

import flet as ft
from typing import Optional, Callable, Dict, Any
from ..theme import ThemeManager, ThemedText, ThemedCard, SPACING, TYPO_SCALE


class AIReflectionComponent:
    """Inline AI reflection display component."""
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        on_regenerate: Optional[Callable[[], None]] = None,
        on_hide: Optional[Callable[[], None]] = None
    ):
        self.theme_manager = theme_manager
        self.on_regenerate = on_regenerate
        self.on_hide = on_hide
        self.is_visible = False
        self.current_reflection = None
        self._is_regenerating = False
        
        # UI Components
        self.container = None
        self.content_area = None
        self.regenerate_button = None
        self.hide_button = None
        self._regenerate_progress_ring = None
        
        self._build_component()
    
    def _build_component(self) -> None:
        """Build the AI reflection component."""
        colors = self.theme_manager.colors
        
        # Content area for reflection display
        self.content_area = ft.Column(
            controls=[],
            spacing=SPACING["sm"],
            expand=True
        )
        
        # Control buttons
        # Create progress ring for loading state (initially hidden)
        self._regenerate_progress_ring = ft.ProgressRing(
            width=16,
            height=16,
            stroke_width=2,
            color=colors.primary,
            visible=False
        )
        
        self.regenerate_button = ft.TextButton(
            "Regenerate",
            icon=ft.Icons.REFRESH,
            on_click=lambda _: self._on_regenerate()
        )
        
        # Create container for button with loading indicator
        self._regenerate_button_container = ft.Row(
            controls=[
                self.regenerate_button,
                self._regenerate_progress_ring
            ],
            tight=True,
            spacing=8
        )
        
        self.hide_button = ft.TextButton(
            "Hide",
            icon=ft.Icons.VISIBILITY_OFF,
            on_click=lambda _: self._on_hide()
        )
        
        # Main container
        self.container = ft.Container(
            content=ft.Column(
                controls=[
                    # Header
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.PSYCHOLOGY,
                                color=colors.primary,
                                size=TYPO_SCALE["h4"]
                            ),
                            ThemedText(
                                self.theme_manager,
                                "AI Reflection",
                                variant="primary",
                                typography="h4"
                            ),
                            ft.Container(expand=True),
                            self._regenerate_button_container,
                            self.hide_button
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=SPACING["sm"]
                    ),
                    
                    # Content area
                    ThemedCard(
                        self.theme_manager,
                        elevation="sm",
                        content=self.content_area,
                        spacing="md"
                    )
                ],
                spacing=SPACING["md"]
            ),
            padding=ft.padding.all(SPACING["md"]),
            visible=False  # Hidden by default
        )
    
    def show_reflection(self, reflection_data: Dict[str, Any]) -> None:
        """Display AI reflection content."""
        self.current_reflection = reflection_data
        self._update_content(reflection_data)
        self.container.visible = True
        self.container.update()
    
    def show_generating_state(self) -> None:
        """Show loading/generating state."""
        self.content_area.controls = [
            ft.Row(
                controls=[
                    ft.ProgressRing(
                        width=20,
                        height=20,
                        stroke_width=2,
                        color=self.theme_manager.colors.primary
                    ),
                    ThemedText(
                        self.theme_manager,
                        "Generating AI reflection...",
                        variant="secondary"
                    )
                ],
                spacing=SPACING["sm"],
                alignment=ft.MainAxisAlignment.START
            )
        ]
        self.container.visible = True
        self.container.update()
    
    def hide(self) -> None:
        """Hide the AI reflection component."""
        self.container.visible = False
        self.container.update()
    
    def _update_content(self, reflection_data: Dict[str, Any]) -> None:
        """Update the reflection content display."""
        controls = []
        
        # Insights section
        if "insights" in reflection_data and reflection_data["insights"]:
            controls.append(
                ThemedText(
                    self.theme_manager,
                    "Key Insights:",
                    variant="primary",
                    typography="body_sm",
                    weight=ft.FontWeight.W_600
                )
            )
            
            for insight in reflection_data["insights"]:
                controls.append(
                    ft.Container(
                        content=ThemedText(
                            self.theme_manager,
                            f"• {insight}",
                            variant="secondary",
                            typography="body_sm"
                        ),
                        padding=ft.padding.only(left=SPACING["md"])
                    )
                )
        
        # Questions section
        if "questions" in reflection_data and reflection_data["questions"]:
            if controls:  # Add spacing if insights exist
                controls.append(ft.Container(height=SPACING["md"]))
            
            controls.append(
                ThemedText(
                    self.theme_manager,
                    "Reflection Questions:",
                    variant="primary",
                    typography="body_sm",
                    weight=ft.FontWeight.W_600
                )
            )
            
            for i, question in enumerate(reflection_data["questions"], 1):
                controls.append(
                    ft.Container(
                        content=ThemedText(
                            self.theme_manager,
                            f"{i}. {question}",
                            variant="secondary",
                            typography="body_sm"
                        ),
                        padding=ft.padding.only(left=SPACING["md"])
                    )
                )
        
        # Themes section (optional)
        if "themes" in reflection_data and reflection_data["themes"]:
            if controls:  # Add spacing if other sections exist
                controls.append(ft.Container(height=SPACING["md"]))
            
            controls.append(
                ThemedText(
                    self.theme_manager,
                    "Themes:",
                    variant="muted",
                    typography="caption"
                )
            )
            
            theme_text = ", ".join(reflection_data["themes"])
            controls.append(
                ft.Container(
                    content=ThemedText(
                        self.theme_manager,
                        theme_text,
                        variant="muted",
                        typography="caption"
                    ),
                    padding=ft.padding.only(left=SPACING["md"])
                )
            )
        
        self.content_area.controls = controls
    
    def _set_regenerate_button_loading(self, loading: bool) -> None:
        """Set the regenerate button loading state."""
        self._is_regenerating = loading
        
        if loading:
            self.regenerate_button.text = "Regenerating..."
            self.regenerate_button.disabled = True
            self.regenerate_button.icon = None  # Hide refresh icon
            self._regenerate_progress_ring.visible = True
        else:
            self.regenerate_button.text = "Regenerate"
            self.regenerate_button.disabled = False
            self.regenerate_button.icon = ft.Icons.REFRESH  # Restore refresh icon
            self._regenerate_progress_ring.visible = False
        
        # Update the UI
        if hasattr(self, 'container') and self.container:
            self.container.update()
    
    def _set_regenerate_button_enabled(self, enabled: bool) -> None:
        """Set the regenerate button enabled state."""
        self.regenerate_button.disabled = not enabled
        if hasattr(self, 'container') and self.container:
            self.container.update()
    
    def show_error_state(self, error_message: str) -> None:
        """Show error state with retry option."""
        self.content_area.controls = [
            ft.Row(
                controls=[
                    ft.Icon(
                        ft.Icons.ERROR_OUTLINE,
                        color=self.theme_manager.colors.error,
                        size=20
                    ),
                    ThemedText(
                        self.theme_manager,
                        f"Error generating reflection: {error_message}",
                        variant="secondary"
                    )
                ],
                spacing=SPACING["sm"],
                alignment=ft.MainAxisAlignment.START
            ),
            ft.Container(height=SPACING["sm"]),
            ThemedText(
                self.theme_manager,
                "Click 'Regenerate' to try again.",
                variant="muted",
                typography="body_sm"
            )
        ]
        self._set_regenerate_button_loading(False)  # Ensure button is re-enabled
        self.container.visible = True
        self.container.update()
    
    def _on_regenerate(self) -> None:
        """Handle regenerate button click."""
        if self._is_regenerating:
            return  # Prevent double-clicks
        
        if self.on_regenerate:
            self._set_regenerate_button_loading(True)
            self.on_regenerate()
    
    def _on_hide(self) -> None:
        """Handle hide button click."""
        if self.on_hide:
            self.on_hide()
    
    def get_container(self) -> ft.Control:
        """Get the component container."""
        return self.container
