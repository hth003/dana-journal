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
    """Enhanced dark theme color scheme for AI Journal Vault."""
    # Core colors - Refined for better contrast and depth
    background: str = "#0A0E1A"          # Deeper midnight for more depth
    surface: str = "#1A1F2E"            # Warmer dark slate
    surface_variant: str = "#2A3441"    # Elevated surface
    surface_elevated: str = "#323B4A"   # Higher elevation surface
    primary: str = "#8B5CF6"            # Violet (unchanged)
    primary_variant: str = "#7C3AED"    # Darker violet
    primary_subtle: str = "#8B5CF615"   # Primary with 15% opacity
    secondary: str = "#06B6D4"          # Cyan accent
    accent: str = "#F59E0B"             # Amber accent
    
    # Text colors - Improved hierarchy
    text_primary: str = "#F8FAFC"       # Pure off-white for better contrast
    text_secondary: str = "#CBD5E1"     # Light gray
    text_muted: str = "#94A3B8"         # Muted gray
    text_subtle: str = "#64748B"        # More subtle text
    text_on_primary: str = "#FFFFFF"    # White on primary
    text_on_dark: str = "#F1F5F9"       # Text on dark surfaces
    
    # Border and divider colors - More subtle gradations
    border: str = "#334155"             # Primary borders
    border_subtle: str = "#1E293B"      # Subtle borders
    border_focus: str = "#8B5CF6"       # Focus state borders
    divider: str = "#1E293B"            # Dividers
    
    # State colors - Improved accessibility
    success: str = "#10B981"            # Green
    success_subtle: str = "#10B98120"   # Green with opacity
    warning: str = "#F59E0B"            # Amber
    warning_subtle: str = "#F59E0B20"   # Amber with opacity  
    error: str = "#EF4444"              # Red
    error_subtle: str = "#EF444420"     # Red with opacity
    info: str = "#3B82F6"               # Blue
    info_subtle: str = "#3B82F620"      # Blue with opacity
    
    # Interactive states - More pronounced feedback
    hover: str = "#8B5CF610"            # Primary hover (subtle)
    hover_strong: str = "#8B5CF625"     # Strong hover state
    pressed: str = "#8B5CF630"          # Pressed state
    selected: str = "#8B5CF620"         # Selected state
    focus: str = "#8B5CF640"            # Focus state
    disabled: str = "#64748B50"         # Disabled state
    
    # Shadow system - More depth
    shadow_sm: str = "#00000008"        # Subtle shadow
    shadow_md: str = "#00000015"        # Default shadow
    shadow_lg: str = "#00000025"        # Elevated shadow
    shadow_xl: str = "#00000040"        # Heavy shadow
    shadow_light: str = "#00000012"      # Light shadow for components
    
    # Entry indicator colors
    entry_indicator: str = "#F59E0B"    # Amber for entries
    today_indicator: str = "#8B5CF6"    # Primary for today


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
        elevation: str = None,
        spacing: str = None,
        **kwargs
    ):
        # Extract parameters that don't belong to Container
        if 'elevation' in kwargs:
            elevation = kwargs.pop('elevation')
        if 'spacing' in kwargs:
            spacing = kwargs.pop('spacing')
        
        # Store original properties for shadow updates
        self._original_shadow = kwargs.get('shadow')
        
        # Initialize parent first
        super().__init__(**kwargs)
        
        self.theme_manager = theme_manager
        self.variant = variant
        self.elevation = elevation
        self.spacing = spacing
        
        # Apply theme colors and styling
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply dark theme colors, elevation, and spacing."""
        colors = self.theme_manager.colors
        
        # Apply background color based on variant
        if self.variant == "surface":
            self.bgcolor = colors.surface
        elif self.variant == "background":
            self.bgcolor = colors.background
        elif self.variant == "surface_variant":
            self.bgcolor = colors.surface_variant
        elif self.variant == "primary":
            self.bgcolor = colors.primary
        
        # Apply elevation (shadow) if specified
        if self.elevation and self.elevation in ELEVATION:
            elevation_data = ELEVATION[self.elevation]
            if elevation_data["shadow"]:  # Only apply shadow if it exists
                self.shadow = ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=elevation_data["blur"],
                    color=elevation_data["shadow"],
                    offset=ft.Offset(elevation_data["offset"][0], elevation_data["offset"][1])
                )
        
        # Apply spacing (padding) if specified
        if self.spacing and self.spacing in SPACING:
            spacing_value = SPACING[self.spacing]
            self.padding = ft.padding.all(spacing_value)
        
        # Update shadow colors if shadow exists
        if self._original_shadow:
            # Create a new shadow with updated colors
            self.shadow = ft.BoxShadow(
                spread_radius=self._original_shadow.spread_radius,
                blur_radius=self._original_shadow.blur_radius,
                color=colors.shadow_md,
                offset=self._original_shadow.offset,
            )


class ThemedText(ft.Text):
    """Text component that automatically applies dark theme colors."""
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        text: str = "",
        variant: str = "primary",
        typography: str = None,
        **kwargs
    ):
        # Extract typography parameter before passing to parent
        if 'typography' in kwargs:
            typography = kwargs.pop('typography')
        
        # Initialize parent first with text value
        super().__init__(value=text, **kwargs)
        
        self.theme_manager = theme_manager
        self.variant = variant
        self.typography = typography
        
        # Apply theme colors and typography
        self._apply_theme()
    
    def _apply_theme(self) -> None:
        """Apply dark theme colors and typography."""
        colors = self.theme_manager.colors
        
        # Apply color based on variant
        if self.variant == "primary":
            self.color = colors.text_primary
        elif self.variant == "secondary":
            self.color = colors.text_secondary
        elif self.variant == "muted":
            self.color = colors.text_muted
        elif self.variant == "on_primary":
            self.color = colors.text_on_primary
        
        # Apply typography if specified
        if self.typography and self.typography in TYPO_SCALE:
            self.size = TYPO_SCALE[self.typography]
            
            # Apply weight based on typography type
            if self.typography in ["display", "h1"]:
                self.weight = ft.FontWeight.BOLD
            elif self.typography in ["h2", "h3"]:
                self.weight = ft.FontWeight.W_600
            elif self.typography in ["h4", "label"]:
                self.weight = ft.FontWeight.W_500




# Typography Scale - Following 1.25 (Major Third) ratio for visual harmony
TYPO_SCALE = {
    "display": 48,      # App title, major headings
    "h1": 38,          # Primary headings
    "h2": 30,          # Section headings  
    "h3": 24,          # Subsection headings
    "h4": 19,          # Component titles
    "body_xl": 16,     # Large body text
    "body": 14,        # Default body text
    "body_sm": 12,     # Small body text
    "caption": 10,     # Captions, labels
}

# Line height ratios for optimal readability
LINE_HEIGHT_RATIOS = {
    "tight": 1.2,      # Headlines
    "normal": 1.4,     # Body text
    "relaxed": 1.6,    # Long-form content
}

def get_text_style(theme_manager: ThemeManager, variant: str = "body") -> ft.TextStyle:
    """Get text style with improved typography scale and hierarchy."""
    colors = theme_manager.colors
    
    base_styles = {
        "display": ft.TextStyle(
            size=TYPO_SCALE["display"],
            weight=ft.FontWeight.BOLD,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["tight"],
        ),
        "h1": ft.TextStyle(
            size=TYPO_SCALE["h1"],
            weight=ft.FontWeight.BOLD,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["tight"],
        ),
        "h2": ft.TextStyle(
            size=TYPO_SCALE["h2"],
            weight=ft.FontWeight.W_600,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["tight"],
        ),
        "h3": ft.TextStyle(
            size=TYPO_SCALE["h3"],
            weight=ft.FontWeight.W_600,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
        ),
        "h4": ft.TextStyle(
            size=TYPO_SCALE["h4"],
            weight=ft.FontWeight.W_500,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
        ),
        "body_xl": ft.TextStyle(
            size=TYPO_SCALE["body_xl"],
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
        ),
        "body": ft.TextStyle(
            size=TYPO_SCALE["body"],
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
        ),
        "body_sm": ft.TextStyle(
            size=TYPO_SCALE["body_sm"],
            color=colors.text_secondary,
            height=LINE_HEIGHT_RATIOS["normal"],
        ),
        "caption": ft.TextStyle(
            size=TYPO_SCALE["caption"],
            color=colors.text_muted,
            weight=ft.FontWeight.W_500,
            height=LINE_HEIGHT_RATIOS["normal"],
            letter_spacing=0.3,
        ),
        "label": ft.TextStyle(
            size=TYPO_SCALE["caption"],
            weight=ft.FontWeight.W_600,
            color=colors.text_muted,
            height=LINE_HEIGHT_RATIOS["normal"],
            letter_spacing=0.8,
        ),
    }
    
    return base_styles.get(variant, base_styles["body"])


def create_card_style(theme_manager: ThemeManager, elevation: str = "md") -> Dict[str, Any]:
    """Create a card style dictionary with elevation system."""
    colors = theme_manager.colors
    elev = ELEVATION.get(elevation, ELEVATION["md"])
    
    base_style = {
        "bgcolor": colors.surface_variant if elevation != "none" else colors.surface,
        "border_radius": RADIUS["lg" if elevation in ["lg", "xl"] else "md"],
        "border": ft.border.all(1, colors.border_subtle),
    }
    
    if elev["shadow"]:
        base_style["shadow"] = ft.BoxShadow(
            spread_radius=0,
            blur_radius=elev["blur"],
            color=elev["shadow"],
            offset=ft.Offset(elev["offset"][0], elev["offset"][1]),
        )
    
    return base_style


# Spacing Scale - Based on 8px grid system for consistent rhythm
SPACING = {
    "xs": 4,           # 0.25rem - Tight spacing
    "sm": 8,           # 0.5rem - Small spacing  
    "md": 16,          # 1rem - Default spacing
    "lg": 24,          # 1.5rem - Large spacing
    "xl": 32,          # 2rem - Extra large spacing
    "2xl": 40,         # 2.5rem - Section spacing
    "3xl": 48,         # 3rem - Major section spacing
    "4xl": 64,         # 4rem - Layout spacing
}

# Elevation system for consistent shadows and layering
ELEVATION = {
    "none": {
        "shadow": None,
        "blur": 0,
        "offset": (0, 0)
    },
    "sm": {
        "shadow": "#00000008",
        "blur": 2,
        "offset": (0, 1)
    },
    "md": {
        "shadow": "#00000015",
        "blur": 4,
        "offset": (0, 2)
    },
    "lg": {
        "shadow": "#00000025",
        "blur": 8,
        "offset": (0, 4)
    },
    "xl": {
        "shadow": "#00000040",
        "blur": 16,
        "offset": (0, 8)
    }
}

# Border radius scale for consistent rounded corners
RADIUS = {
    "none": 0,
    "sm": 4,           # Small components
    "md": 8,           # Default components
    "lg": 12,          # Cards, containers
    "xl": 16,          # Large containers
    "full": 9999,      # Pills, badges
}

# Component sizing standards - Following 8px grid
COMPONENT_SIZES = {
    "button_height": 36,
    "button_sm_height": 28,
    "input_height": 40,
    "sidebar_width": 280,      # Optimized for content
    "calendar_day_size": 32,   # Consistent with 8px grid
    "calendar_spacing": 2,
    "header_height": 64,       # Consistent header height
    "panel_min_width": 240,
    "icon_xs": 12,
    "icon_sm": 16,
    "icon_md": 20,
    "icon_lg": 24,
}

class ThemedCard(ThemedContainer):
    """A card component with consistent elevation and styling."""
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        elevation: str = "md",
        **kwargs
    ):
        # Apply card-specific defaults
        kwargs.setdefault('border_radius', RADIUS["lg" if elevation in ["lg", "xl"] else "md"])
        kwargs.setdefault('border', ft.border.all(1, theme_manager.colors.border_subtle))
        
        super().__init__(
            theme_manager=theme_manager,
            variant="surface_variant" if elevation != "none" else "surface",
            elevation=elevation,
            **kwargs
        )


class ThemedButton(ft.ElevatedButton):
    """A button component with consistent theming."""
    
    def __init__(
        self,
        theme_manager: ThemeManager,
        text: str,
        variant: str = "primary",
        size: str = "md",
        **kwargs
    ):
        colors = theme_manager.colors
        
        # Define button variants
        if variant == "primary":
            style = ft.ButtonStyle(
                bgcolor=colors.primary,
                color=colors.text_on_primary,
                elevation=2,
                surface_tint_color=colors.primary,
            )
        elif variant == "secondary":
            style = ft.ButtonStyle(
                bgcolor=colors.surface_variant,
                color=colors.text_primary,
                elevation=1,
                side=ft.BorderSide(1, colors.border),
            )
        elif variant == "ghost":
            style = ft.ButtonStyle(
                bgcolor="transparent",
                color=colors.text_secondary,
                elevation=0,
                overlay_color=colors.hover,
            )
        else:
            style = kwargs.get('style', ft.ButtonStyle())
        
        # Apply size
        height = COMPONENT_SIZES["button_height"] if size == "md" else COMPONENT_SIZES["button_sm_height"]
        
        super().__init__(
            text=text,
            style=style,
            height=height,
            **kwargs
        )


def create_consistent_spacing(size: str) -> int:
    """Get consistent spacing value by size key."""
    return SPACING.get(size, SPACING["md"])


def create_consistent_elevation(theme_manager: ThemeManager, elevation: str = "md") -> Optional[ft.BoxShadow]:
    """Create consistent box shadow for elevation."""
    if elevation not in ELEVATION:
        return None
    
    elev = ELEVATION[elevation]
    if not elev["shadow"]:
        return None
        
    return ft.BoxShadow(
        spread_radius=0,
        blur_radius=elev["blur"],
        color=elev["shadow"],
        offset=ft.Offset(elev["offset"][0], elev["offset"][1]),
    )


def create_input_field(
    theme_manager: ThemeManager,
    hint_text: str = "",
    multiline: bool = False,
    **kwargs
) -> ft.TextField:
    """Create a consistently styled input field."""
    colors = theme_manager.colors
    
    return ft.TextField(
        hint_text=hint_text,
        multiline=multiline,
        border=ft.InputBorder.UNDERLINE,
        border_color=colors.border_subtle,
        focused_border_color=colors.primary,
        hint_style=ft.TextStyle(
            color=colors.text_muted,
            size=14
        ),
        text_style=ft.TextStyle(
            color=colors.text_primary,
            size=14,
            height=1.6  # Better readability
        ),
        bgcolor="transparent",
        **kwargs
    )


# Export the main theme manager instance
theme_manager = ThemeManager()