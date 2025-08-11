"""
Theme System for DANA - The AI Journal Vault

Warm, companion-like theme system providing consistent styling and colors
for a supportive, human-centered journaling experience.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, TYPE_CHECKING
import flet as ft

if TYPE_CHECKING:
    import flet as ft


@dataclass
class DANATheme:
    """Warm companion theme color scheme for DANA - The AI Journal Vault."""
    # Core colors - Warm, companion-like palette for human connection
    background: str = "#FAF8F5"          # Warm off-white (journal paper)
    surface: str = "#F5F2ED"            # Soft cream surface
    surface_variant: str = "#EFEBE3"    # Slightly elevated cream
    surface_elevated: str = "#FFFFFF"   # Pure white for elevated cards
    primary: str = "#E07A5F"            # Terracotta - warm, human, approachable
    primary_variant: str = "#D96847"    # Slightly darker terracotta
    primary_subtle: str = "#E07A5F15"   # Primary with 15% opacity
    secondary: str = "#3D5A80"          # Deep blue - trust, wisdom
    accent: str = "#81B29A"             # Sage green - growth, reflection
    
    # Text colors - Warm, readable hierarchy
    text_primary: str = "#2C2421"       # Rich dark brown (ink-like)
    text_secondary: str = "#5D5651"     # Medium warm gray
    text_muted: str = "#8B8580"         # Light warm gray
    text_subtle: str = "#ADA8A3"        # Very light warm gray
    text_on_primary: str = "#FFFFFF"    # White on terracotta
    text_on_dark: str = "#2C2421"       # Dark text on light surfaces
    
    # Border and divider colors - Soft, warm boundaries
    border: str = "#ADA8A3"             # Primary borders
    border_subtle: str = "#D4CFC7"      # Subtle borders
    border_focus: str = "#E07A5F"       # Focus state borders (terracotta)
    divider: str = "#D4CFC7"            # Dividers
    
    # State colors - Warm, approachable feedback
    success: str = "#6BA368"            # Warm green
    success_subtle: str = "#6BA36820"   # Green with opacity
    warning: str = "#E6B84A"            # Warm amber
    warning_subtle: str = "#E6B84A20"   # Amber with opacity  
    error: str = "#D67B7B"              # Soft red
    error_subtle: str = "#D67B7B20"     # Red with opacity
    info: str = "#7BA3D4"               # Soft blue
    info_subtle: str = "#7BA3D420"      # Blue with opacity
    
    # Interactive states - Warm, welcoming feedback
    hover: str = "#E07A5F10"            # Terracotta hover (subtle)
    hover_strong: str = "#E07A5F25"     # Strong hover state
    pressed: str = "#E07A5F30"          # Pressed state
    selected: str = "#E07A5F20"         # Selected state
    focus: str = "#E07A5F40"            # Focus state
    disabled: str = "#ADA8A350"         # Disabled state
    
    # Shadow system - Warm, soft shadows
    shadow_sm: str = "#E07A5F08"        # Subtle terracotta shadow
    shadow_md: str = "#E07A5F12"        # Default warm shadow
    shadow_lg: str = "#E07A5F16"        # Elevated warm shadow
    shadow_xl: str = "#E07A5F20"        # Heavy warm shadow
    shadow_light: str = "#E07A5F10"      # Light shadow for components
    shadow_wisdom: str = "#E07A5F15"     # Special shadow for wisdom cards
    
    # Journal-specific colors
    entry_indicator: str = "#E07A5F"    # Terracotta for entries
    today_indicator: str = "#81B29A"    # Sage green for today
    reflection_glow: str = "#E07A5F20"  # Subtle terracotta glow for AI insights
    wisdom_card_bg: str = "#FFFFFF"     # Pure white for wisdom cards


class ThemeManager:
    """Simplified theme manager that provides consistent DANA theme colors."""
    
    def __init__(self):
        """Initialize theme manager with DANA theme."""
        self._colors = DANATheme()
        
    @property
    def colors(self) -> DANATheme:
        """Get current theme colors (always DANA theme)."""
        return self._colors
    
    @property
    def current_theme(self) -> str:
        """Get current theme name (always 'dana')."""
        return "dana"
    
    @property
    def is_dark(self) -> bool:
        """Check if current theme is dark (False for DANA's light theme)."""
        return False


class ThemedContainer(ft.Container):
    """A container that automatically applies DANA theme colors."""
    
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
    """Text component that automatically applies DANA theme colors."""
    
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




# Font Families - DANA dual typography system
FONT_FAMILIES = {
    "ui": "Inter, -apple-system, system-ui, sans-serif",           # UI elements, buttons, labels
    "content": "Crimson Pro, Georgia, Times New Roman, serif",     # Journal content, reading text
    "accent": "Inter, -apple-system, system-ui, sans-serif",       # Special accent text
}

# Typography Scale - Following 1.25 (Major Third) ratio for visual harmony and comfort
TYPO_SCALE = {
    "display": 52,      # DANA brand name (larger for presence)
    "h1": 42,          # Page titles
    "h2": 34,          # Section headings  
    "h3": 27,          # Component titles
    "h4": 22,          # Card headers
    "body_xl": 20,     # Large reading text (Crimson Pro)
    "body": 18,        # Default content (Crimson Pro)
    "body_ui": 16,     # UI labels (Inter)
    "body_sm": 14,     # Small text
    "caption": 13,     # Labels, metadata
    "label": 12,       # Form labels, buttons
}

# Line height ratios for optimal readability and comfort
LINE_HEIGHT_RATIOS = {
    "tight": 1.1,      # Display text (DANA brand)
    "normal": 1.4,     # Headlines and UI text
    "comfortable": 1.6, # Body text (Crimson Pro for reading)
    "relaxed": 1.8,    # Long-form journal content
}

def get_text_style(theme_manager: ThemeManager, variant: str = "body") -> ft.TextStyle:
    """Get text style with DANA typography system using Inter for UI and Crimson Pro for content."""
    colors = theme_manager.colors
    
    base_styles = {
        "display": ft.TextStyle(
            size=TYPO_SCALE["display"],
            weight=ft.FontWeight.BOLD,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["tight"],
            font_family=FONT_FAMILIES["ui"],  # Inter for DANA branding
        ),
        "h1": ft.TextStyle(
            size=TYPO_SCALE["h1"],
            weight=ft.FontWeight.BOLD,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for UI headers
        ),
        "h2": ft.TextStyle(
            size=TYPO_SCALE["h2"],
            weight=ft.FontWeight.W_600,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for UI headers
        ),
        "h3": ft.TextStyle(
            size=TYPO_SCALE["h3"],
            weight=ft.FontWeight.W_600,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for UI headers
        ),
        "h4": ft.TextStyle(
            size=TYPO_SCALE["h4"],
            weight=ft.FontWeight.W_500,
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for UI headers
        ),
        "body_xl": ft.TextStyle(
            size=TYPO_SCALE["body_xl"],
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["comfortable"],
            font_family=FONT_FAMILIES["content"],  # Crimson Pro for reading
        ),
        "body": ft.TextStyle(
            size=TYPO_SCALE["body"],
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["comfortable"],
            font_family=FONT_FAMILIES["content"],  # Crimson Pro for reading
        ),
        "body_ui": ft.TextStyle(
            size=TYPO_SCALE["body_ui"],
            color=colors.text_primary,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for UI text
        ),
        "body_sm": ft.TextStyle(
            size=TYPO_SCALE["body_sm"],
            color=colors.text_secondary,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for small UI text
        ),
        "caption": ft.TextStyle(
            size=TYPO_SCALE["caption"],
            color=colors.text_muted,
            weight=ft.FontWeight.W_500,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for captions
            letter_spacing=0.3,
        ),
        "label": ft.TextStyle(
            size=TYPO_SCALE["label"],
            weight=ft.FontWeight.W_600,
            color=colors.text_muted,
            height=LINE_HEIGHT_RATIOS["normal"],
            font_family=FONT_FAMILIES["ui"],  # Inter for labels
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

# Elevation system for warm, soft shadows that complement DANA's design
ELEVATION = {
    "none": {
        "shadow": None,
        "blur": 0,
        "offset": (0, 0)
    },
    "sm": {
        "shadow": "#E07A5F08",  # Subtle terracotta shadow
        "blur": 2,
        "offset": (0, 1)
    },
    "md": {
        "shadow": "#E07A5F12",  # Default warm shadow
        "blur": 4,
        "offset": (0, 2)
    },
    "lg": {
        "shadow": "#E07A5F16",  # Elevated warm shadow
        "blur": 8,
        "offset": (0, 4)
    },
    "xl": {
        "shadow": "#E07A5F20",  # Heavy warm shadow
        "blur": 16,
        "offset": (0, 8)
    },
    "wisdom": {
        "shadow": "#E07A5F15",  # Special shadow for wisdom cards
        "blur": 6,
        "offset": (0, 3)
    }
}

# Border radius scale for softer, more companion-like design
RADIUS = {
    "none": 0,
    "sm": 8,           # Small components (increased for warmth)
    "md": 12,          # Default components (increased for warmth)
    "lg": 16,          # Cards, containers (DANA's standard radius)
    "xl": 24,          # Large containers (more rounded)
    "wisdom": 20,      # Special radius for wisdom cards
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