"""
Theme System for AI Journal Vault

Comprehensive theme management with dark/light modes, proper contrast,
and accessibility considerations for a calming journaling experience.
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional
import flet as ft


@dataclass
class ThemeColors:
    """Color scheme for a theme variant."""
    # Core colors
    background: str
    surface: str
    surface_variant: str
    primary: str
    primary_variant: str
    secondary: str
    accent: str
    
    # Text colors
    text_primary: str
    text_secondary: str
    text_muted: str
    text_on_primary: str
    
    # Border and divider colors
    border: str
    border_subtle: str
    divider: str
    
    # State colors
    success: str
    warning: str
    error: str
    info: str
    
    # Interactive states
    hover: str
    pressed: str
    selected: str
    disabled: str
    
    # Shadow colors
    shadow_light: str
    shadow_medium: str
    shadow_heavy: str


class ThemeManager:
    """Manages theme state and provides theme switching functionality."""
    
    # Dark mode theme (default)
    DARK_THEME = ThemeColors(
        # Core colors
        background="#0F172A",          # Deep midnight
        surface="#1E293B",            # Dark slate
        surface_variant="#334155",    # Lighter slate
        primary="#8B5CF6",            # Violet
        primary_variant="#7C3AED",    # Darker violet
        secondary="#06B6D4",          # Cyan
        accent="#F59E0B",             # Amber accent
        
        # Text colors
        text_primary="#F1F5F9",       # Off-white
        text_secondary="#CBD5E1",     # Light gray
        text_muted="#94A3B8",         # Muted gray
        text_on_primary="#FFFFFF",    # White on primary
        
        # Border and divider colors
        border="#475569",             # Medium gray
        border_subtle="#334155",      # Subtle border
        divider="#374151",            # Divider gray
        
        # State colors
        success="#10B981",            # Green
        warning="#F59E0B",            # Amber
        error="#EF4444",              # Red
        info="#3B82F6",               # Blue
        
        # Interactive states
        hover="#2563EB20",            # Blue with opacity
        pressed="#2563EB30",          # Darker blue with opacity
        selected="#8B5CF620",         # Primary with opacity
        disabled="#6B728080",         # Gray with opacity
        
        # Shadow colors
        shadow_light="#00000010",     # Very light shadow
        shadow_medium="#00000020",    # Medium shadow
        shadow_heavy="#00000040",     # Heavy shadow
    )
    
    # Light mode theme
    LIGHT_THEME = ThemeColors(
        # Core colors
        background="#FFFFFF",         # Pure white
        surface="#F8FAFC",           # Very light gray
        surface_variant="#F1F5F9",   # Light gray
        primary="#6366F1",           # Indigo
        primary_variant="#4F46E5",   # Darker indigo
        secondary="#0891B2",         # Dark cyan
        accent="#D97706",            # Dark amber accent
        
        # Text colors
        text_primary="#0F172A",      # Dark slate
        text_secondary="#475569",    # Medium gray
        text_muted="#64748B",        # Muted gray
        text_on_primary="#FFFFFF",   # White on primary
        
        # Border and divider colors
        border="#D1D5DB",            # Light border
        border_subtle="#E5E7EB",     # Very subtle border
        divider="#E5E7EB",           # Light divider
        
        # State colors
        success="#059669",           # Dark green
        warning="#D97706",           # Dark amber
        error="#DC2626",             # Dark red
        info="#2563EB",              # Blue
        
        # Interactive states
        hover="#6366F110",           # Primary with low opacity
        pressed="#6366F120",         # Primary with higher opacity
        selected="#6366F115",        # Primary with opacity
        disabled="#9CA3AF80",        # Gray with opacity
        
        # Shadow colors
        shadow_light="#0000000A",    # Very light shadow
        shadow_medium="#00000015",   # Medium shadow
        shadow_heavy="#00000025",    # Heavy shadow
    )
    
    def __init__(self, initial_theme: str = "dark"):
        """Initialize theme manager with default theme."""
        self._current_theme = initial_theme
        self._observers: list = []
        
    @property
    def current_theme(self) -> str:
        """Get current theme name."""
        return self._current_theme
    
    @property
    def colors(self) -> ThemeColors:
        """Get current theme colors."""
        return self.DARK_THEME if self._current_theme == "dark" else self.LIGHT_THEME
    
    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark."""
        return self._current_theme == "dark"
    
    def toggle_theme(self) -> None:
        """Toggle between dark and light themes."""
        self._current_theme = "light" if self._current_theme == "dark" else "dark"
        self._notify_observers()
    
    def set_theme(self, theme: str) -> None:
        """Set specific theme by name."""
        if theme in ["dark", "light"]:
            if self._current_theme != theme:
                self._current_theme = theme
                self._notify_observers()
    
    def add_observer(self, callback) -> None:
        """Add a callback to be notified when theme changes."""
        self._observers.append(callback)
    
    def remove_observer(self, callback) -> None:
        """Remove a theme change observer."""
        if callback in self._observers:
            self._observers.remove(callback)
    
    def _notify_observers(self) -> None:
        """Notify all observers of theme change."""
        for callback in self._observers:
            try:
                callback(self._current_theme, self.colors)
            except Exception as e:
                print(f"Error notifying theme observer: {e}")


class ThemedContainer(ft.Container):
    """A container that automatically applies theme colors."""
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        variant: str = "surface",
        **kwargs
    ):
        # Store original properties for theme updates
        self._original_border = kwargs.get('border')
        self._original_shadow = kwargs.get('shadow')
        
        # Initialize parent first
        super().__init__(**kwargs)
        
        self.theme_manager = theme_manager
        self.variant = variant
        
        # Apply initial theme
        self._apply_theme()
        
        # Listen for theme changes
        theme_manager.add_observer(self._on_theme_changed)
    
    def _apply_theme(self) -> None:
        """Apply current theme colors."""
        colors = self.theme_manager.colors
        
        if self.variant == "surface":
            self.bgcolor = colors.surface
        elif self.variant == "background":
            self.bgcolor = colors.background
        elif self.variant == "surface_variant":
            self.bgcolor = colors.surface_variant
        elif self.variant == "primary":
            self.bgcolor = colors.primary
        
        # Update border colors if border exists
        if self._original_border:
            if hasattr(self._original_border, 'bottom') and self._original_border.bottom:
                self.border = ft.border.only(bottom=ft.border.BorderSide(1, colors.border_subtle))
            elif hasattr(self._original_border, 'right') and self._original_border.right:
                self.border = ft.border.only(right=ft.border.BorderSide(1, colors.border_subtle))
            elif hasattr(self._original_border, 'top') and self._original_border.top:
                self.border = ft.border.only(top=ft.border.BorderSide(1, colors.border_subtle))
            elif hasattr(self._original_border, 'left') and self._original_border.left:
                self.border = ft.border.only(left=ft.border.BorderSide(1, colors.border_subtle))
            else:
                # If it's a general border
                self.border = ft.border.all(1, colors.border_subtle)
        
        # Update shadow colors if shadow exists
        if self._original_shadow:
            # Create a new shadow with updated colors
            self.shadow = ft.BoxShadow(
                spread_radius=self._original_shadow.spread_radius,
                blur_radius=self._original_shadow.blur_radius,
                color=colors.shadow_light,
                offset=self._original_shadow.offset,
            )
    
    def _on_theme_changed(self, theme_name: str, colors: ThemeColors) -> None:
        """Handle theme change."""
        self._apply_theme()
        if hasattr(self, 'update'):
            self.update()


class ThemedText(ft.Text):
    """Text component that automatically applies theme colors."""
    
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
        
        # Apply initial theme
        self._apply_theme()
        
        # Listen for theme changes
        theme_manager.add_observer(self._on_theme_changed)
    
    def _apply_theme(self) -> None:
        """Apply current theme colors."""
        colors = self.theme_manager.colors
        
        if self.variant == "primary":
            self.color = colors.text_primary
        elif self.variant == "secondary":
            self.color = colors.text_secondary
        elif self.variant == "muted":
            self.color = colors.text_muted
        elif self.variant == "on_primary":
            self.color = colors.text_on_primary
    
    def _on_theme_changed(self, theme_name: str, colors: ThemeColors) -> None:
        """Handle theme change."""
        self._apply_theme()
        if hasattr(self, 'update'):
            self.update()


def create_theme_toggle_button(theme_manager: ThemeManager) -> ft.IconButton:
    """Create a theme toggle button with proper styling."""
    
    def toggle_theme(e):
        theme_manager.toggle_theme()
        # Update button icon
        button.icon = ft.Icons.LIGHT_MODE if theme_manager.is_dark else ft.Icons.DARK_MODE
        button.tooltip = f"Switch to {'light' if theme_manager.is_dark else 'dark'} mode"
        button.update()
    
    button = ft.IconButton(
        icon=ft.Icons.LIGHT_MODE if theme_manager.is_dark else ft.Icons.DARK_MODE,
        tooltip=f"Switch to {'light' if theme_manager.is_dark else 'dark'} mode",
        icon_color=theme_manager.colors.text_secondary,
        on_click=toggle_theme,
        style=ft.ButtonStyle(
            bgcolor={
                ft.ControlState.DEFAULT: "transparent",
                ft.ControlState.HOVERED: theme_manager.colors.hover,
            },
            overlay_color=theme_manager.colors.pressed,
        )
    )
    
    def update_button_colors(theme_name: str, colors: ThemeColors):
        button.icon_color = colors.text_secondary
        button.style.bgcolor[ft.ControlState.HOVERED] = colors.hover
        button.style.overlay_color = colors.pressed
        button.update()
    
    theme_manager.add_observer(update_button_colors)
    
    return button


def get_text_style(theme_manager: ThemeManager, variant: str = "body") -> ft.TextStyle:
    """Get text style for the current theme."""
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
    """Create a card style dictionary for the current theme."""
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