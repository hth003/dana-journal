"""
Theme System for AI Journal Vault

Simplified dark theme system providing consistent styling and colors
for a focused, calming journaling experience.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, TYPE_CHECKING
import flet as ft

if TYPE_CHECKING:
    import flet as ft


@dataclass
class DarkTheme:
    """Dark theme color scheme for AI Journal Vault."""
    # Core colors
    background: str = "#0F172A"          # Deep midnight
    surface: str = "#1E293B"            # Dark slate
    surface_variant: str = "#334155"    # Lighter slate
    primary: str = "#8B5CF6"            # Violet
    primary_variant: str = "#7C3AED"    # Darker violet
    secondary: str = "#06B6D4"          # Cyan
    accent: str = "#F59E0B"             # Amber accent
    
    # Text colors
    text_primary: str = "#F1F5F9"       # Off-white
    text_secondary: str = "#CBD5E1"     # Light gray
    text_muted: str = "#94A3B8"         # Muted gray
    text_on_primary: str = "#FFFFFF"    # White on primary
    
    # Border and divider colors
    border: str = "#475569"             # Medium gray
    border_subtle: str = "#334155"      # Subtle border
    divider: str = "#374151"            # Divider gray
    
    # State colors
    success: str = "#10B981"            # Green
    warning: str = "#F59E0B"            # Amber
    error: str = "#EF4444"              # Red
    info: str = "#3B82F6"               # Blue
    
    # Interactive states
    hover: str = "#2563EB20"            # Blue with opacity
    pressed: str = "#2563EB30"          # Darker blue with opacity
    selected: str = "#8B5CF620"         # Primary with opacity
    disabled: str = "#6B728080"         # Gray with opacity
    
    # Shadow colors
    shadow_light: str = "#00000010"     # Very light shadow
    shadow_medium: str = "#00000020"    # Medium shadow
    shadow_heavy: str = "#00000040"     # Heavy shadow


class ThemeManager:
    """Simplified theme manager that provides consistent dark theme colors."""
    
    def __init__(self):
        """Initialize theme manager with dark theme."""
        self._colors = DarkTheme()
        
    @property
    def colors(self) -> DarkTheme:
        """Get current theme colors (always dark mode)."""
        return self._colors
    
    @property
    def current_theme(self) -> str:
        """Get current theme name (always 'dark')."""
        return "dark"
    
    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark (always True)."""
        return True


class ThemedContainer(ft.Container):
    """A container that automatically applies dark theme colors."""
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        variant: str = "surface",
        **kwargs
    ):
        # Store original properties for shadow updates
        self._original_shadow = kwargs.get('shadow')
        
        # Initialize parent first
        super().__init__(**kwargs)
        
        self.theme_manager = theme_manager
        self.variant = variant
        
        # Apply theme colors
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply dark theme colors."""
        colors = self.theme_manager.colors
        
        if self.variant == "surface":
            self.bgcolor = colors.surface
        elif self.variant == "background":
            self.bgcolor = colors.background
        elif self.variant == "surface_variant":
            self.bgcolor = colors.surface_variant
        elif self.variant == "primary":
            self.bgcolor = colors.primary
        
        # Update shadow colors if shadow exists
        if self._original_shadow:
            # Create a new shadow with updated colors
            self.shadow = ft.BoxShadow(
                spread_radius=self._original_shadow.spread_radius,
                blur_radius=self._original_shadow.blur_radius,
                color=colors.shadow_light,
                offset=self._original_shadow.offset,
            )


class ThemedText(ft.Text):
    """Text component that automatically applies dark theme colors."""
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        text: str = "",
        variant: str = "primary",
        **kwargs
    ):
        # Initialize parent first with text value
        super().__init__(value=text, **kwargs)
        
        self.theme_manager = theme_manager
        self.variant = variant
        
        # Apply theme colors
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply dark theme colors."""
        colors = self.theme_manager.colors
        
        if self.variant == "primary":
            self.color = colors.text_primary
        elif self.variant == "secondary":
            self.color = colors.text_secondary
        elif self.variant == "muted":
            self.color = colors.text_muted
        elif self.variant == "on_primary":
            self.color = colors.text_on_primary




def get_text_style(theme_manager: ThemeManager, variant: str = "body") -> ft.TextStyle:
    """Get text style for the dark theme."""
    colors = theme_manager.colors
    
    base_styles = {
        "heading1": ft.TextStyle(
            size=32,
            weight=ft.FontWeight.BOLD,
            color=colors.text_primary,
        ),
        "heading2": ft.TextStyle(
            size=24,
            weight=ft.FontWeight.W_600,
            color=colors.text_primary,
        ),
        "heading3": ft.TextStyle(
            size=18,
            weight=ft.FontWeight.W_500,
            color=colors.text_primary,
        ),
        "body": ft.TextStyle(
            size=14,
            color=colors.text_primary,
        ),
        "body_large": ft.TextStyle(
            size=16,
            color=colors.text_primary,
        ),
        "caption": ft.TextStyle(
            size=12,
            color=colors.text_secondary,
        ),
        "label": ft.TextStyle(
            size=11,
            weight=ft.FontWeight.W_500,
            color=colors.text_muted,
            letter_spacing=0.5,
        ),
    }
    
    return base_styles.get(variant, base_styles["body"])


def create_card_style(theme_manager: ThemeManager, elevated: bool = True) -> Dict[str, Any]:
    """Create a card style dictionary for the dark theme."""
    colors = theme_manager.colors
    
    return {
        "bgcolor": colors.surface,
        "border": ft.border.all(1, colors.border_subtle),
        "border_radius": 12,
        "shadow": ft.BoxShadow(
            spread_radius=0,
            blur_radius=8 if elevated else 4,
            color=colors.shadow_medium if elevated else colors.shadow_light,
            offset=ft.Offset(0, 2 if elevated else 1),
        ) if elevated else None,
    }


# Export the main theme manager instance
theme_manager = ThemeManager()