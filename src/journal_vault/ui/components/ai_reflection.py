"""
Dana's Wisdom Component for Dana - safe journal space

A warm, companion-like component that displays supportive insights and reflections
below the text editor with gentle, encouraging guidance.
"""

import flet as ft
from typing import Optional, Callable, Dict, Any
from ..theme import ThemeManager, ThemedText, SPACING, TYPO_SCALE, RADIUS


class DanaWisdomComponent:
    """Inline companion wisdom display component with sage green accents."""
    
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
            "New Reflection",  # Clean text without duplicate icon
            icon=ft.Icons.AUTO_AWESOME,  # Single sparkle icon
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
            "Hide",  # User preferred text
            icon=ft.Icons.VISIBILITY_OFF,  # More appropriate hide icon
            on_click=lambda _: self._on_hide()
        )
        
        # Main container - optimized for minimal space usage
        self.container = ft.Container(
            content=ft.Column(
                controls=[
                    # Compact header
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.NATURE_PEOPLE,  # More organic, companion-like icon
                                color=colors.accent,  # Sage green accent instead of primary
                                size=TYPO_SCALE["body"]  # Smaller icon to save space
                            ),
                            ThemedText(
                                self.theme_manager,
                                "Dana's Wisdom",  # Warm, companion-like name
                                variant="primary",
                                typography="body_sm"  # Smaller header text
                            ),
                            ft.Container(expand=True),
                            self._regenerate_button_container,
                            self.hide_button
                        ],
                        alignment=ft.MainAxisAlignment.START,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=SPACING["xs"]  # Tighter spacing
                    ),
                    
                    # Compact wisdom card with special styling
                    ft.Container(
                        content=self.content_area,
                        bgcolor=colors.wisdom_card_bg,  # Pure white for wisdom cards
                        border_radius=RADIUS["md"],  # Smaller radius for compactness
                        padding=ft.padding.all(SPACING["md"]),  # Reduced padding
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=4,  # Lighter shadow for less visual weight
                            color=colors.shadow_wisdom,  # Special warm shadow
                            offset=ft.Offset(0, 2)  # Smaller offset for subtlety
                        ),
                        border=ft.border.all(1, colors.accent + "20")  # Subtle sage green border
                    )
                ],
                spacing=SPACING["xs"],  # Tighter spacing between header and content
                tight=True  # Minimize vertical space
            ),
            padding=ft.padding.symmetric(
                horizontal=SPACING["md"],
                vertical=SPACING["sm"]  # Reduced vertical padding
            ),
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
                        "Dana is reflecting on your thoughts...",  # More personal and companion-like
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
                    "🌱 What I noticed:",  # More personal, growth-oriented language
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
                    "✨ Questions to explore:",  # More inviting and exploratory
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
                    "🌿 Gentle themes:",  # More nurturing language
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
            self.regenerate_button.text = "Reflecting..."
            self.regenerate_button.disabled = True
            self.regenerate_button.icon = None  # Hide sparkle icon
            self._regenerate_progress_ring.visible = True
        else:
            self.regenerate_button.text = "New Reflection"
            self.regenerate_button.disabled = False
            self.regenerate_button.icon = ft.Icons.AUTO_AWESOME  # Restore sparkle icon
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
                        f"I'm having trouble reflecting right now: {error_message}",  # More personal error message
                        variant="secondary"
                    )
                ],
                spacing=SPACING["sm"],
                alignment=ft.MainAxisAlignment.START
            ),
            ft.Container(height=SPACING["sm"]),
            ThemedText(
                self.theme_manager,
                "Let's try again when you're ready ✨",  # More encouraging and supportive
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


# Backward compatibility alias
AIReflectionComponent = DanaWisdomComponent
