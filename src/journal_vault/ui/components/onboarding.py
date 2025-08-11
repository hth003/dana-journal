"""
Onboarding Flow for Dana - safe journal space

Comprehensive onboarding experience including welcome screen, privacy explanation,
storage location selection, theme preference, and optional first entry creation.
"""

import os
from typing import Callable, Optional
from pathlib import Path
import flet as ft
from ..theme import ThemeManager, ThemedContainer, ThemedText, SPACING
from ...ai.download_model import ModelDownloadManager, DownloadProgress, format_bytes, format_speed, format_eta


class OnboardingFlow:
    """Multi-step onboarding flow for new users."""
    
    def __init__(self, theme_manager: ThemeManager, on_complete: Callable[[dict], None], page: Optional[ft.Page] = None):
        self.theme_manager = theme_manager
        self.on_complete = on_complete
        self.page = page
        self.current_step = 0
        self.total_steps = 4
        self.vault_mode = "create"  # "create" or "load"
        self.onboarding_data = {
            'storage_path': None,
            'vault_name': 'My Journal',
            'parent_directory': None,
            'ai_enabled': True,  # Default to AI enabled
            'ai_model_downloaded': False,
            'ai_skipped': False,
        }
        
        # AI download manager
        self.ai_manager = ModelDownloadManager()
        self.download_progress = self.ai_manager.progress  # Use the manager's progress instance
        
        # Create file picker for directory selection
        self.file_picker = ft.FilePicker(on_result=self._on_folder_selected)
        
        # Create main container
        self.container = self._create_container()
    
    def _create_container(self) -> ThemedContainer:
        """Create the main onboarding container."""
        return ThemedContainer(
            self.theme_manager,
            variant="background",
            content=ft.Column(
                controls=[
                    self._create_progress_indicator(),
                    ft.Container(height=10),  # Reduced spacer
                    self._get_current_step_content(),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            ),
            padding=ft.padding.all(SPACING["lg"]),  # Reduced from 4xl to lg for more compact layout
            expand=True
        )
    
    def _create_progress_indicator(self) -> ft.Row:
        """Create progress indicator for onboarding steps."""
        colors = self.theme_manager.colors
        
        steps = []
        for i in range(self.total_steps):
            is_current = i == self.current_step
            is_completed = i < self.current_step
            
            # Step circle
            circle_color = colors.primary if (is_current or is_completed) else colors.border_subtle
            text_color = colors.text_on_primary if (is_current or is_completed) else colors.text_muted
            
            step_circle = ft.Container(
                content=ft.Text(
                    str(i + 1),
                    color=text_color,
                    size=14,
                    weight=ft.FontWeight.W_600
                ),
                width=30,
                height=30,
                border_radius=15,
                bgcolor=circle_color,
                alignment=ft.alignment.center
            )
            
            steps.append(step_circle)
            
            # Add connector line (except for last step)
            if i < self.total_steps - 1:
                line_color = colors.primary if is_completed else colors.border_subtle
                steps.append(
                    ft.Container(
                        width=40,
                        height=2,
                        bgcolor=line_color,
                        margin=ft.margin.symmetric(horizontal=10)
                    )
                )
        
        return ft.Row(
            controls=steps,
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _get_current_step_content(self) -> ft.Container:
        """Get content for the current step."""
        steps = [
            self._create_welcome_step,
            self._create_privacy_step,
            self._create_storage_step,
            self._create_ai_setup_step,
        ]
        
        return ft.Container(
            content=steps[self.current_step](),
            width=600,
            alignment=ft.alignment.center
        )
    
    def _create_welcome_step(self) -> ft.Column:
        """Create welcome step content."""
        colors = self.theme_manager.colors
        
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.MENU_BOOK_ROUNDED,
                        size=80,
                        color=colors.primary
                    ),
                    margin=ft.margin.only(bottom=30)
                ),
                ThemedText(
                    self.theme_manager,
                    "Welcome to Dana - safe journal space",
                    variant="primary",
                    size=32,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=15),
                ThemedText(
                    self.theme_manager,
                    "Your private, AI-enhanced journaling companion",
                    variant="secondary",
                    size=18,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=30),
                ThemedContainer(
                    self.theme_manager,
                    variant="surface",
                    content=ft.Column(
                        controls=[
                            self._create_feature_item("🔒", "Complete Privacy", "All data stays on your device"),
                            self._create_feature_item("🤖", "AI Insights", "Get thoughtful reflections on your entries"),
                            self._create_feature_item("📅", "Smart Calendar", "Visualize your journaling journey"),
                        ],
                        spacing=15
                    ),
                    padding=ft.padding.all(SPACING["xl"]),
                    border_radius=12,
                    border=ft.border.all(1, colors.border_subtle)
                ),
                ft.Container(height=40),
                self._create_step_buttons(next_text="Get Started")
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )
    
    def _create_feature_item(self, emoji: str, title: str, description: str) -> ft.Row:
        """Create a feature item for the welcome step."""
        return ft.Row(
            controls=[
                ft.Text(emoji, size=24),
                ft.Column(
                    controls=[
                        ThemedText(
                            self.theme_manager,
                            title,
                            variant="primary",
                            size=16,
                            weight=ft.FontWeight.W_600
                        ),
                        ThemedText(
                            self.theme_manager,
                            description,
                            variant="secondary",
                            size=14
                        )
                    ],
                    spacing=2,
                    expand=True
                )
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
    
    def _create_privacy_step(self) -> ft.Column:
        """Create privacy explanation step."""
        colors = self.theme_manager.colors
        
        return ft.Column(
            controls=[
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.SHIELD_ROUNDED,
                        size=80,
                        color=colors.success
                    ),
                    margin=ft.margin.only(bottom=30)
                ),
                ThemedText(
                    self.theme_manager,
                    "Your Privacy Matters",
                    variant="primary",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                ThemedContainer(
                    self.theme_manager,
                    variant="surface",
                    content=ft.Column(
                        controls=[
                            self._create_privacy_point(
                                "🏠", "Local Storage Only",
                                "Your journal entries are stored only on your device. Nothing is sent to external servers."
                            ),
                            self._create_privacy_point(
                                "🚫", "No Account Required",
                                "No sign-ups, no accounts, no data collection. Just pure, private journaling."
                            ),
                            self._create_privacy_point(
                                "🤖", "Local AI Processing",
                                "AI insights are generated locally when possible, keeping your thoughts private."
                            ),
                        ],
                        spacing=20
                    ),
                    padding=ft.padding.all(SPACING["xl"]),
                    border_radius=12,
                    border=ft.border.all(1, colors.border_subtle)
                ),
                ft.Container(height=40),
                self._create_step_buttons()
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )
    
    def _create_privacy_point(self, emoji: str, title: str, description: str) -> ft.Row:
        """Create a privacy point item."""
        return ft.Row(
            controls=[
                ft.Text(emoji, size=20),
                ft.Column(
                    controls=[
                        ThemedText(
                            self.theme_manager,
                            title,
                            variant="primary",
                            size=16,
                            weight=ft.FontWeight.W_600
                        ),
                        ThemedText(
                            self.theme_manager,
                            description,
                            variant="secondary",
                            size=14
                        )
                    ],
                    spacing=5,
                    expand=True
                )
            ],
            spacing=15,
            vertical_alignment=ft.CrossAxisAlignment.START
        )
    
    def _create_ai_setup_step(self) -> ft.Column:
        """Create AI setup step with comparison cards and download options."""
        colors = self.theme_manager.colors
        
        # Create UI components if not exists
        if not hasattr(self, 'ai_setup_components_created'):
            self._create_ai_setup_components()
            self.ai_setup_components_created = True
        
        return ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.PSYCHOLOGY_ROUNDED,
                        size=60,
                        color=colors.primary
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                ThemedText(
                    self.theme_manager,
                    "AI-Powered Insights",
                    variant="primary",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=8),
                ThemedText(
                    self.theme_manager,
                    "Add intelligent reflections and insights to your journaling experience",
                    variant="secondary",
                    size=16,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=25),
                
                # Comparison Cards
                self._create_ai_comparison_cards(),
                
                ft.Container(height=20),
                
                # AI Setup Options
                self._get_ai_setup_content(),
                
                ft.Container(height=25),
                self._create_step_buttons(
                    next_text="Complete Setup" if not self._is_ai_download_needed() else "Complete Setup",
                    show_next=True,
                    is_final=True
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )
    
    def _create_ai_setup_components(self) -> None:
        """Create components for AI setup step."""
        colors = self.theme_manager.colors
        
        # Download progress bar
        self.download_progress_bar = ft.ProgressBar(
            value=0,
            width=400,
            height=8,
            bgcolor=colors.surface_variant,
            color=colors.primary,
            visible=False
        )
        
        # Download status text
        self.download_status_text = ThemedText(
            self.theme_manager,
            "",
            variant="secondary",
            size=12,
            text_align=ft.TextAlign.CENTER
        )
    
    def _create_ai_comparison_cards(self) -> ft.Row:
        """Create interactive comparison cards for With AI vs Traditional with selection capability."""
        colors = self.theme_manager.colors
        
        # Determine which option is currently selected
        ai_selected = self.onboarding_data.get('ai_enabled', True)
        
        # Fixed width for both cards to ensure equal sizing
        card_width = 260
        
        # With AI Card - interactive with selection feedback
        with_ai_selected = ai_selected
        with_ai_card = ft.GestureDetector(
            content=ThemedContainer(
                self.theme_manager,
                variant="surface",  # Consistent base styling
                content=ft.Column(
                    controls=[
                        # Header with selection indicator
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE if with_ai_selected else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                    color=colors.primary if with_ai_selected else colors.text_secondary,
                                    size=18
                                ),
                                ft.Icon(ft.Icons.AUTO_AWESOME, color=colors.primary, size=18),
                                ThemedText(
                                    self.theme_manager,
                                    "With AI",
                                    variant="primary" if with_ai_selected else "secondary",
                                    size=15,
                                    weight=ft.FontWeight.BOLD
                                )
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Container(height=12),
                        
                        # Features - compact layout
                        ft.Column(
                            controls=[
                                self._create_feature_item_compact("🔍", "Smart insights"),
                                self._create_feature_item_compact("💭", "Mood reflections"),
                                self._create_feature_item_compact("📈", "Pattern recognition"),
                                self._create_feature_item_compact("✨", "Writing prompts"),
                                self._create_feature_item_compact("🔒", "100% private")
                            ],
                            spacing=8,
                            tight=True
                        )
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    expand=True
                ),
                padding=ft.padding.all(SPACING["md"]),
                border_radius=12,
                border=ft.border.all(2 if with_ai_selected else 1, colors.primary if with_ai_selected else colors.border_subtle),
                bgcolor=colors.surface,  # Consistent background
                width=card_width,
                expand=False
            ),
            on_tap=lambda e: self._select_ai_option("with_ai")
        )
        
        # Traditional Card - interactive with selection feedback
        traditional_selected = not ai_selected
        traditional_card = ft.GestureDetector(
            content=ThemedContainer(
                self.theme_manager,
                variant="surface",  # Same base styling as AI card
                content=ft.Column(
                    controls=[
                        # Header with selection indicator
                        ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.CHECK_CIRCLE if traditional_selected else ft.Icons.RADIO_BUTTON_UNCHECKED,
                                    color=colors.primary if traditional_selected else colors.text_secondary,
                                    size=18
                                ),
                                ft.Icon(ft.Icons.EDIT_NOTE, color=colors.text_secondary, size=18),
                                ThemedText(
                                    self.theme_manager,
                                    "Traditional",
                                    variant="primary" if traditional_selected else "secondary",
                                    size=15,
                                    weight=ft.FontWeight.BOLD
                                )
                            ],
                            spacing=6,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        ft.Container(height=12),
                        
                        # Features - compact layout with balanced text
                        ft.Column(
                            controls=[
                                self._create_feature_item_compact("✍️", "Manual analysis"),
                                self._create_feature_item_compact("📝", "Text editing"),
                                self._create_feature_item_compact("📅", "Calendar view"),
                                self._create_feature_item_compact("💾", "Simple storage"),
                                self._create_feature_item_compact("🔒", "Complete privacy")
                            ],
                            spacing=8,
                            tight=True
                        )
                    ],
                    spacing=0,
                    horizontal_alignment=ft.CrossAxisAlignment.START,
                    expand=True
                ),
                padding=ft.padding.all(SPACING["md"]),
                border_radius=12,
                border=ft.border.all(2 if traditional_selected else 1, colors.primary if traditional_selected else colors.border_subtle),
                bgcolor=colors.surface,  # Same background as AI card
                width=card_width,
                expand=False
            ),
            on_tap=lambda e: self._select_ai_option("traditional")
        )
        
        return ft.Row(
            controls=[
                with_ai_card,
                ft.Container(width=16),  # Reduced spacer
                traditional_card
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            vertical_alignment=ft.CrossAxisAlignment.START,
            spacing=0
        )
    
    def _create_feature_item_compact(self, emoji: str, text: str, secondary: bool = False) -> ft.Row:
        """Create a compact feature item for comparison cards with consistent styling."""
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Text(emoji, size=14),
                    width=18,
                    alignment=ft.alignment.center_left
                ),
                ThemedText(
                    self.theme_manager,
                    text,
                    variant="primary",  # Always use primary for consistent appearance
                    size=12,
                    text_align=ft.TextAlign.LEFT
                )
            ],
            spacing=8,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            tight=True
        )
    
    def _create_feature_list(self, features, secondary=False) -> ft.Column:
        """Create a list of features for comparison cards with consistent sizing."""
        feature_controls = []
        
        for emoji, text in features:
            feature_controls.append(
                ft.Row(
                    controls=[
                        ft.Container(
                            content=ft.Text(emoji, size=16),
                            width=24,  # Fixed width for emojis
                            alignment=ft.alignment.center
                        ),
                        ft.Container(
                            content=ThemedText(
                                self.theme_manager,
                                text,
                                variant="secondary" if secondary else "primary",
                                size=13,
                                text_align=ft.TextAlign.LEFT
                            ),
                            expand=True
                        )
                    ],
                    spacing=8,
                    vertical_alignment=ft.CrossAxisAlignment.START,
                    tight=True
                )
            )
        
        return ft.Column(
            controls=feature_controls,
            spacing=8,
            tight=True
        )
    
    def _get_ai_setup_content(self) -> ThemedContainer:
        """Get AI setup content based on current state."""
        if self.ai_manager.is_model_available():
            # Model already available
            return self._create_ai_ready_content()
        elif self.download_progress.status == "downloading":
            # Download in progress
            return self._create_download_progress_content()
        elif self.download_progress.status == "complete":
            # Download complete
            return self._create_download_complete_content()
        elif self.download_progress.status == "error":
            # Download error
            return self._create_download_error_content()
        else:
            # Initial state - show options
            return self._create_ai_options_content()
    
    def _create_ai_ready_content(self) -> ThemedContainer:
        """Content when AI model is already available."""
        colors = self.theme_manager.colors
        
        # Use consistent width for all cards
        card_width = 536
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=colors.success, size=24),
                            ThemedText(
                                self.theme_manager,
                                "AI Model Ready",
                                variant="primary",
                                size=16,
                                weight=ft.FontWeight.W_600
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(height=8),
                    ThemedText(
                        self.theme_manager,
                        "The AI model is already downloaded and ready to provide insights on your journal entries.",
                        variant="secondary",
                        size=13,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                spacing=0
            ),
            padding=ft.padding.all(SPACING["lg"]),
            border_radius=12,
            border=ft.border.all(1, colors.success),
            bgcolor=colors.surface,
            width=card_width,  # Set consistent width
            expand=False  # Prevent expansion
        )
    
    def _create_ai_options_content(self) -> ThemedContainer:
        """Simplified content showing single action button based on AI selection."""
        colors = self.theme_manager.colors
        
        # Check system requirements
        requirements = self.ai_manager.check_system_requirements()
        
        # Calculate consistent width for all cards (matching the two comparison cards)
        card_width = 536  # Same width as download progress card
        
        controls = []
        
        # System requirements check
        if requirements["meets_requirements"]:
            controls.extend([
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, color=colors.success, size=20),
                        ThemedText(
                            self.theme_manager,
                            "System Ready for AI",
                            variant="primary",
                            size=14,
                            weight=ft.FontWeight.W_500
                        )
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=4),
                ThemedText(
                    self.theme_manager,
                    f"Available space: {requirements['disk_space_gb']}GB | Memory: {requirements['available_memory_gb']}GB",
                    variant="secondary",
                    size=11,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=16)
            ])
        else:
            controls.extend([
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.WARNING, color=colors.warning, size=20),
                        ThemedText(
                            self.theme_manager,
                            "System Requirements Check",
                            variant="primary",
                            size=14,
                            weight=ft.FontWeight.W_500
                        )
                    ],
                    spacing=8,
                    alignment=ft.MainAxisAlignment.CENTER
                ),
                ft.Container(height=8)
            ])
            
            for issue in requirements["issues"]:
                controls.extend([
                    ThemedText(
                        self.theme_manager,
                        f"⚠️ {issue}",
                        variant="secondary",
                        size=12,
                        text_align=ft.TextAlign.LEFT
                    ),
                    ft.Container(height=4)
                ])
            
            controls.append(ft.Container(height=12))
        
        # Single action button based on selection
        ai_enabled = self.onboarding_data.get('ai_enabled', True)
        
        if ai_enabled:
            # AI is selected - show download button
            if requirements["meets_requirements"]:
                action_button = ft.ElevatedButton(
                    text="Download AI Model (~2.1GB)",
                    icon=ft.Icons.DOWNLOAD,
                    on_click=self._start_ai_download,
                    style=ft.ButtonStyle(
                        bgcolor=colors.primary,
                        color=colors.text_on_primary,
                        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500),
                        padding=ft.padding.symmetric(horizontal=20, vertical=12)
                    )
                )
            else:
                # Requirements not met - show disabled button
                action_button = ft.ElevatedButton(
                    text="System Requirements Not Met",
                    icon=ft.Icons.WARNING,
                    disabled=True,
                    style=ft.ButtonStyle(
                        bgcolor=colors.surface_variant,
                        color=colors.text_secondary,
                        text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500),
                        padding=ft.padding.symmetric(horizontal=20, vertical=12)
                    )
                )
        else:
            # Traditional is selected - show continue button
            action_button = ft.ElevatedButton(
                text="Continue with Traditional Journal",
                icon=ft.Icons.CHECK,
                on_click=self._continue_without_ai,
                style=ft.ButtonStyle(
                    bgcolor=colors.primary,
                    color=colors.text_on_primary,
                    text_style=ft.TextStyle(size=14, weight=ft.FontWeight.W_500),
                    padding=ft.padding.symmetric(horizontal=20, vertical=12)
                )
            )
        
        controls.extend([
            ft.Row(
                controls=[action_button],
                spacing=12,
                alignment=ft.MainAxisAlignment.CENTER
            )
        ])
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(controls=controls, spacing=0),
            padding=ft.padding.all(SPACING["lg"]),
            border_radius=12,
            border=ft.border.all(1, colors.border_subtle),
            width=card_width,  # Set consistent width
            expand=False  # Prevent expansion
        )
    
    def _create_download_progress_content(self) -> ThemedContainer:
        """Content showing download progress with real-time updates."""
        colors = self.theme_manager.colors
        
        # Calculate width to match the two cards above (260 + 16 + 260 = 536)
        download_card_width = 536
        
        # Create progress components if they don't exist
        if not hasattr(self, 'download_progress_bar'):
            self.download_progress_bar = ft.ProgressBar(
                value=0,
                width=400,  # Fixed width for better visibility
                height=8,
                bgcolor=colors.surface_variant,
                color=colors.primary
            )
            self.download_status_text = ThemedText(
                self.theme_manager,
                "Initializing download...",
                variant="secondary",
                size=12,
                text_align=ft.TextAlign.CENTER
            )
        
        # Update progress bar with proper value calculation
        if self.download_progress.total_bytes > 0:
            progress_value = self.download_progress.bytes_downloaded / self.download_progress.total_bytes
            self.download_progress_bar.value = progress_value
            self.download_progress_bar.visible = True
        else:
            self.download_progress_bar.value = 0
            self.download_progress_bar.visible = True
        
        # Update status text with real-time info
        if self.download_progress.download_speed > 0:
            downloaded_mb = format_bytes(self.download_progress.bytes_downloaded)
            total_mb = format_bytes(self.download_progress.total_bytes)
            speed = format_speed(self.download_progress.download_speed)
            eta = format_eta(self.download_progress.eta_seconds)
            
            status = f"Downloading: {downloaded_mb} / {total_mb} at {speed} - ETA: {eta}"
        else:
            status = "Initializing download..."
        
        self.download_status_text.value = status
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.DOWNLOAD, color=colors.primary, size=20),
                    ThemedText(self.theme_manager, "Downloading AI Model", variant="primary", size=14, weight=ft.FontWeight.W_500)
                ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=12),
                self.download_progress_bar,
                ft.Container(height=8),
                self.download_status_text,
                ft.Container(height=16),
                ft.TextButton(
                    text="Cancel Download",
                    icon=ft.Icons.CANCEL,
                    on_click=self._cancel_ai_download,
                    style=ft.ButtonStyle(color=colors.text_secondary, text_style=ft.TextStyle(size=12))
                )
            ], spacing=0),
            padding=ft.padding.all(SPACING["lg"]),
            border_radius=12,
            border=ft.border.all(1, colors.primary),
            width=download_card_width,  # Match the width of both cards + spacer
            expand=False  # Ensure it doesn't expand beyond the specified width
        )
    
    def _create_download_complete_content(self) -> ThemedContainer:
        """Content when download is complete."""
        colors = self.theme_manager.colors
        
        # Use consistent width for all cards
        card_width = 536
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.CHECK_CIRCLE, color=colors.success, size=24),
                            ThemedText(
                                self.theme_manager,
                                "AI Model Downloaded Successfully",
                                variant="primary",
                                size=16,
                                weight=ft.FontWeight.W_600
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(height=8),
                    ThemedText(
                        self.theme_manager,
                        "Your AI-powered journaling experience is ready! The model will provide insights and reflections on your entries.",
                        variant="secondary",
                        size=13,
                        text_align=ft.TextAlign.CENTER
                    )
                ],
                spacing=0
            ),
            padding=ft.padding.all(SPACING["lg"]),
            border_radius=12,
            border=ft.border.all(1, colors.success),
            width=card_width,  # Set consistent width
            expand=False  # Prevent expansion
        )
    
    def _create_download_error_content(self) -> ThemedContainer:
        """Content when download encounters an error."""
        colors = self.theme_manager.colors
        
        # Use consistent width for all cards
        card_width = 536
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.ERROR, color=colors.error, size=20),
                            ThemedText(
                                self.theme_manager,
                                "Download Failed",
                                variant="primary",
                                size=14,
                                weight=ft.FontWeight.W_500
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER
                    ),
                    ft.Container(height=8),
                    ThemedText(
                        self.theme_manager,
                        self.download_progress.error_message or "An error occurred during download.",
                        variant="secondary",
                        size=12,
                        text_align=ft.TextAlign.CENTER
                    ),
                    ft.Container(height=16),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                text="Retry Download",
                                icon=ft.Icons.REFRESH,
                                on_click=self._start_ai_download,
                                style=ft.ButtonStyle(
                                    bgcolor=colors.primary,
                                    color=colors.text_on_primary,
                                    text_style=ft.TextStyle(size=13)
                                )
                            ),
                            ft.TextButton(
                                text="Choose Traditional",
                                on_click=lambda e: self._select_ai_option("traditional"),
                                style=ft.ButtonStyle(
                                    color=colors.text_secondary,
                                    text_style=ft.TextStyle(size=13)
                                )
                            )
                        ],
                        spacing=12,
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                spacing=0
            ),
            padding=ft.padding.all(SPACING["lg"]),
            border_radius=12,
            border=ft.border.all(1, colors.error),
            width=card_width,  # Set consistent width
            expand=False  # Prevent expansion
        )
    
    def _is_ai_download_needed(self) -> bool:
        """Check if AI download is needed to proceed."""
        return (not self.ai_manager.is_model_available() and 
                self.download_progress.status not in ["complete", "downloading"] and
                not self.onboarding_data.get('ai_skipped', False))
    
    def _start_ai_download(self, e) -> None:
        """Start AI model download with improved UI updates."""
        try:
            # Use the download manager's progress instance
            self.download_progress = self.ai_manager.progress
            self.download_progress.status = "downloading"  # Set status immediately
            self.onboarding_data['ai_enabled'] = True
            
            # Ensure progress bar is initialized
            if not hasattr(self, 'download_progress_bar'):
                colors = self.theme_manager.colors
                self.download_progress_bar = ft.ProgressBar(
                    value=0,
                    width=400,
                    height=8,
                    bgcolor=colors.surface_variant,
                    color=colors.primary
                )
                self.download_status_text = ThemedText(
                    self.theme_manager,
                    "Initializing download...",
                    variant="secondary",
                    size=12,
                    text_align=ft.TextAlign.CENTER
                )
            
            # Start download with progress callback
            def on_progress(progress: DownloadProgress):
                self.download_progress = progress
                # Update UI on main thread with proper error handling
                if hasattr(self, 'container') and self.container:
                    try:
                        # Update the content
                        self.container.content.controls[2] = self._get_current_step_content()
                        # Force update with better error handling
                        if self.page:
                            self.page.update()
                        else:
                            self.container.update()
                    except Exception as ex:
                        print(f"UI update error: {ex}")
            
            # Start the download
            self.ai_manager.download_model_async(on_progress)
            
            # Immediate UI update to show download starting
            self.container.content.controls[2] = self._get_current_step_content()
            if self.page:
                self.page.update()
            else:
                self.container.update()
            
        except Exception as ex:
            self.download_progress.status = "error"
            self.download_progress.error_message = f"Failed to start download: {str(ex)}"
            # Update UI to show error state
            self.container.content.controls[2] = self._get_current_step_content()
            if self.page:
                self.page.update()
            else:
                self.container.update()
    
    def _cancel_ai_download(self, e) -> None:
        """Cancel AI model download."""
        try:
            # Cancel the download
            self.ai_manager.cancel_download()
            
            # Reset download progress
            self.download_progress.status = "error"
            self.download_progress.error_message = "Download cancelled by user"
            
            # Update UI to show error state
            self.container.content.controls[2] = self._get_current_step_content()
            if self.page:
                self.page.update()
            else:
                self.container.update()
                
        except Exception as ex:
            print(f"Cancel download error: {ex}")
            # Fallback: just update the UI
            self.download_progress.status = "error"
            self.download_progress.error_message = "Download cancelled by user"
            self.container.content.controls[2] = self._get_current_step_content()
            if self.page:
                self.page.update()
            else:
                self.container.update()
    

    
    def _create_storage_step(self) -> ft.Column:
        """Create dual-mode vault setup step with clear create/load distinction."""
        colors = self.theme_manager.colors
        
        # Create UI components
        self._create_vault_setup_components()
        
        return ft.Column(
            controls=[
                # Header
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.CREATE_NEW_FOLDER_ROUNDED if self.vault_mode == "create" else ft.Icons.FOLDER_OPEN,
                        size=50,
                        color=colors.primary if self.vault_mode == "create" else colors.accent
                    ),
                    margin=ft.margin.only(bottom=15)
                ),
                ThemedText(
                    self.theme_manager,
                    "Set Up Your Vault",
                    variant="primary",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=8),
                ThemedText(
                    self.theme_manager,
                    "Choose how to set up your journal vault",
                    variant="secondary",
                    size=14,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=20),
                
                # Mode Selection Radio Buttons
                ft.Container(
                    content=ft.RadioGroup(
                        content=ft.Row(
                            controls=[
                                ft.Radio(
                                    value="create",
                                    label="Create New Vault",
                                    active_color=colors.primary,
                                    label_style=ft.TextStyle(
                                        color=colors.text_primary,
                                        size=14,
                                        weight=ft.FontWeight.W_500
                                    )
                                ),
                                ft.Radio(
                                    value="load",
                                    label="Load Existing Vault",
                                    active_color=colors.accent,
                                    label_style=ft.TextStyle(
                                        color=colors.text_primary,
                                        size=14,
                                        weight=ft.FontWeight.W_500
                                    )
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=40
                        ),
                        value=self.vault_mode,
                        on_change=self._on_mode_change
                    ),
                    margin=ft.margin.only(bottom=20)
                ),
                
                # Dynamic content based on mode
                self._get_mode_content(),
                
                ft.Container(height=12),
                
                # Path Preview Section
                self._create_path_preview(),
                
                ft.Container(height=20),
                self._create_step_buttons(
                    next_text="Continue to AI Setup",
                    show_next=self._is_ready_to_proceed(),
                    is_final=False
                )
            ],
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0
        )
    
    def _create_vault_setup_components(self) -> None:
        """Create the UI components for vault setup."""
        colors = self.theme_manager.colors
        
        # Vault name input field - pre-filled, no confusing default button
        self.vault_name_field = ft.TextField(
            label="Enter vault name",
            value=self.onboarding_data['vault_name'],  # Already set to "My Journal" in __init__
            on_change=self._on_vault_name_change,
            hint_text="My Journal, Personal Vault, etc.",
            bgcolor=colors.surface,
            border_color=colors.border_subtle,
            focused_border_color=colors.primary,
            color=colors.text_primary,
            text_style=ft.TextStyle(color=colors.text_primary, size=14),
            label_style=ft.TextStyle(color=colors.text_secondary, size=12),
            hint_style=ft.TextStyle(color=colors.text_muted, size=12),
            width=400,
            text_align=ft.TextAlign.LEFT,  # Left align for better readability
            cursor_color=colors.primary,
            content_padding=ft.padding.symmetric(horizontal=12, vertical=8)  # Better padding
        )
        
        # Path preview text - smaller and cleaner
        self.path_preview_text = ThemedText(
            self.theme_manager,
            self._get_preview_path(),
            variant="secondary",
            size=12,  # Reduced size
            weight=ft.FontWeight.W_400,  # Lighter weight
            text_align=ft.TextAlign.LEFT  # Left align for readability
        )
        
        # Storage location text - cleaner display
        self.storage_location_text = ThemedText(
            self.theme_manager,
            self.onboarding_data.get('parent_directory') or "No location selected",
            variant="secondary",
            size=13,  # Slightly smaller
            text_align=ft.TextAlign.LEFT
        )
    
    def _on_mode_change(self, e) -> None:
        """Handle vault mode change."""
        self.vault_mode = e.control.value
        # Refresh the storage step
        self.container.content.controls[2] = self._get_current_step_content()
        self.container.update()
    
    def _get_mode_content(self) -> ThemedContainer:
        """Get content for the currently selected mode."""
        if self.vault_mode == "create":
            return self._create_mode_content()
        else:
            return self._load_mode_content()
    
    def _create_mode_content(self) -> ThemedContainer:
        """Create content for 'Create New Vault' mode."""
        colors = self.theme_manager.colors
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    # Vault Name Section
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.EDIT_OUTLINED, color=colors.primary, size=20),
                            ThemedText(
                                self.theme_manager,
                                "Vault Name:",
                                variant="primary",
                                size=14,
                                weight=ft.FontWeight.W_600
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    ft.Container(height=8),
                    self.vault_name_field,
                    
                    ft.Container(height=16),
                    ft.Divider(color=colors.border_subtle, height=1),
                    ft.Container(height=16),
                    
                    # Storage Location Section
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER_OUTLINED, color=colors.primary, size=20),
                            ThemedText(
                                self.theme_manager,
                                "Storage Location:",
                                variant="primary",
                                size=14,
                                weight=ft.FontWeight.W_600
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    ft.Container(height=8),
                    self.storage_location_text,
                    ft.Container(height=12),
                    ft.Row(
                        controls=[
                            ft.ElevatedButton(
                                text="Browse",
                                icon=ft.Icons.FOLDER_OPEN,
                                on_click=self._select_parent_directory,
                                style=ft.ButtonStyle(
                                    bgcolor=colors.primary,
                                    color=colors.text_on_primary,
                                    text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_500),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8)
                                )
                            ),
                            ft.OutlinedButton(
                                text="Use Documents",
                                icon=ft.Icons.HOME,
                                on_click=self._use_documents_folder,
                                style=ft.ButtonStyle(
                                    side=ft.BorderSide(1, colors.primary),
                                    color=colors.primary,
                                    text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_500),
                                    padding=ft.padding.symmetric(horizontal=16, vertical=8)
                                )
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.CENTER
                    )
                ],
                spacing=0
            ),
            padding=ft.padding.all(SPACING["lg"]),
            border_radius=12,
            border=ft.border.all(1, colors.border_subtle)
        )
    
    def _load_mode_content(self) -> ThemedContainer:
        """Create content for 'Load Existing Vault' mode."""
        colors = self.theme_manager.colors
        
        # Check if we have a loaded vault path and its type
        loaded_vault = self.onboarding_data.get('loaded_vault_path')
        vault_type = self.onboarding_data.get('vault_type', '')
        
        # Create content based on whether a vault is selected
        if loaded_vault:
            # Show selected vault info
            vault_info_text = f"Selected: {os.path.basename(loaded_vault)}"
            if vault_type == "confirmed_vault":
                status_text = "✅ Confirmed Journal Vault"
                status_color = colors.success
            elif vault_type == "compatible_vault":
                status_text = "✅ Compatible Journal Vault"
                status_color = colors.success
            else:
                status_text = "Selected vault"
                status_color = colors.text_secondary
                
            vault_content = [
                ThemedText(
                    self.theme_manager,
                    vault_info_text,
                    variant="primary",
                    size=13,
                    weight=ft.FontWeight.W_500,
                    text_align=ft.TextAlign.LEFT
                ),
                ft.Container(height=4),
                ft.Row(
                    controls=[
                        ft.Icon(ft.Icons.CHECK_CIRCLE, color=status_color, size=16),
                        ThemedText(
                            self.theme_manager,
                            status_text,
                            variant="secondary",
                            size=12,
                            text_align=ft.TextAlign.LEFT
                        )
                    ],
                    spacing=4
                )
            ]
        else:
            # Show instruction text
            vault_content = [
                ThemedText(
                    self.theme_manager,
                    "Click below to browse for your existing journal vault folder",
                    variant="secondary",
                    size=13,
                    text_align=ft.TextAlign.LEFT
                ),
                ft.Container(height=4),
                ThemedText(
                    self.theme_manager,
                    "Valid vaults contain '.journal_vault' or 'entries' folder structure",
                    variant="secondary",
                    size=11,
                    text_align=ft.TextAlign.LEFT
                )
            ]
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    # Load Vault Section
                    ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.FOLDER_SPECIAL, color=colors.accent, size=20),
                            ThemedText(
                                self.theme_manager,
                                "Select Your Existing Vault:",
                                variant="primary",
                                size=14,
                                weight=ft.FontWeight.W_600
                            )
                        ],
                        spacing=8,
                        alignment=ft.MainAxisAlignment.START
                    ),
                    ft.Container(height=12),
                    
                    # Dynamic vault selection info
                    *vault_content,
                    
                    ft.Container(height=16),
                    
                    # Browse button
                    ft.ElevatedButton(
                        text="Browse for Vault" if not loaded_vault else "Choose Different Vault",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=self._load_existing_vault,
                        style=ft.ButtonStyle(
                            bgcolor=colors.accent,
                            color=colors.text_on_primary,
                            text_style=ft.TextStyle(size=13, weight=ft.FontWeight.W_500),
                            padding=ft.padding.symmetric(horizontal=16, vertical=8)
                        )
                    )
                ],
                spacing=0
            ),
            padding=ft.padding.all(SPACING["lg"]),
            border_radius=12,
            border=ft.border.all(1, colors.border_subtle)
        )
    
    def _create_path_preview(self) -> ThemedContainer:
        """Create the path preview section."""
        colors = self.theme_manager.colors
        
        if self.vault_mode == "create":
            preview_text = "Vault will be created at:"
            path_text = self._get_preview_path()
        else:
            preview_text = "Vault will be loaded from:"
            loaded_vault = self.onboarding_data.get('loaded_vault_path')
            path_text = loaded_vault or "[Select an existing vault]"
        
        # Store reference to path text for updates
        self.current_path_text = ThemedText(
            self.theme_manager,
            path_text,
            variant="primary" if path_text != "[Select an existing vault]" else "secondary",
            size=12,
            weight=ft.FontWeight.W_500
        )
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface_variant",
            content=ft.Row(
                controls=[
                    ft.Icon(ft.Icons.PREVIEW, color=colors.primary, size=16),
                    ft.Column(
                        controls=[
                            ThemedText(
                                self.theme_manager,
                                preview_text,
                                variant="secondary",
                                size=12
                            ),
                            self.current_path_text
                        ],
                        spacing=2,
                        expand=True
                    )
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.CENTER
            ),
            padding=ft.padding.all(SPACING["sm"]),
            border_radius=8
        )
    
    def _is_ready_to_proceed(self) -> bool:
        """Check if ready to proceed based on current mode."""
        if self.vault_mode == "create":
            return bool(self.onboarding_data.get('parent_directory')) and bool(self.onboarding_data.get('vault_name'))
        else:  # load mode
            return bool(self.onboarding_data.get('loaded_vault_path'))
    
    def _get_preview_path(self) -> str:
        """Get the preview path for the vault with proper path handling."""
        parent_dir = self.onboarding_data.get('parent_directory')
        vault_name = self.onboarding_data.get('vault_name', 'My Journal')
        
        # Ensure vault_name is not empty or just whitespace
        if not vault_name or not vault_name.strip():
            vault_name = 'My Journal'
        
        # Clean the vault name for filesystem use
        clean_vault_name = vault_name.strip()
        
        if parent_dir:
            full_path = os.path.join(parent_dir, clean_vault_name)
            # Ensure proper path separators for display
            return full_path.replace('\\', '/')
        else:
            return f"[Select Parent Directory] → {clean_vault_name}"
    
    def _on_vault_name_change(self, e) -> None:
        """Handle vault name input changes with real-time preview update."""
        # Get the current value, fallback to default if empty
        vault_name = e.control.value if e.control.value else "My Journal"
        
        # Update the data immediately
        self.onboarding_data['vault_name'] = vault_name
        
        # Update path preview in real-time
        self._update_path_preview()
        
        # Update storage path if parent directory is already selected
        self._update_final_storage_path()
    
    
    def _update_path_preview(self) -> None:
        """Update the path preview display."""
        # Update the path text directly without recreating the entire UI
        try:
            if hasattr(self, 'current_path_text') and self.current_path_text:
                if self.vault_mode == "create":
                    new_path = self._get_preview_path()
                    self.current_path_text.value = new_path
                    self.current_path_text.update()
        except Exception:
            pass  # Ignore update errors
    
    def _update_final_storage_path(self) -> None:
        """Update the final storage path when both parent dir and vault name are available."""
        parent_dir = self.onboarding_data.get('parent_directory')
        vault_name = self.onboarding_data.get('vault_name', 'My Journal')
        
        if parent_dir and vault_name:
            clean_vault_name = vault_name.strip() if vault_name.strip() else 'My Journal'
            self.onboarding_data['storage_path'] = os.path.join(parent_dir, clean_vault_name)
    
    def _select_parent_directory(self, e) -> None:
        """Handle parent directory selection using native macOS dialog."""
        try:
            # Update button text to show it's working
            if hasattr(e, 'control'):
                e.control.text = "Opening..."
                e.control.update()
            
            # Use native macOS dialog via osascript
            import subprocess
            result = subprocess.run([
                "osascript", "-e", 
                'choose folder with prompt "Choose Parent Directory for Your Vault"'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                selected_path = result.stdout.strip()
                
                # Convert alias path to regular path if needed
                if selected_path.startswith("alias "):
                    selected_path = self._convert_alias_path(selected_path)
                
                # Validate that we can create the folder in this location
                if os.access(selected_path, os.W_OK):
                    self.onboarding_data['parent_directory'] = selected_path
                    self.storage_location_text.value = selected_path
                    self.storage_location_text.update()
                    self._update_path_preview()
                    self._update_final_storage_path()
                    # Recreate the step to show the next button
                    self.container.content.controls[2] = self._get_current_step_content()
                    self.container.update()
                else:
                    self._show_storage_error("Cannot create folder in selected location. Please choose a different location.")
            else:
                # User cancelled or error occurred
                pass
            
            # Reset button text
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Browse"
                    e.control.update()
            except Exception:
                pass
            
        except subprocess.TimeoutExpired:
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Browse"
                    e.control.update()
            except Exception:
                pass
            self._show_storage_error("Folder selection dialog timed out. Please try again.")
        except Exception as ex:
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Browse"
                    e.control.update()
            except Exception:
                pass
            self._show_storage_error(f"Could not open folder picker: {str(ex)}. Try using 'Use Documents' instead.")
    
    def _use_documents_folder(self, _) -> None:
        """Use the Documents folder as parent directory."""
        try:
            documents_path = os.path.expanduser("~/Documents")
            
            # Validate the directory
            if os.path.exists(documents_path) and os.access(documents_path, os.W_OK):
                self.onboarding_data['parent_directory'] = documents_path
                self.storage_location_text.value = documents_path
                self.storage_location_text.update()
                self._update_path_preview()
                self._update_final_storage_path()
                # Recreate the step to show the next button
                self.container.content.controls[2] = self._get_current_step_content()
                self.container.update()
            else:
                self._show_storage_error("Cannot access Documents folder. Please choose a custom location.")
                
        except Exception as ex:
            self._show_storage_error(f"Error setting up Documents folder: {str(ex)}")
    
    def _convert_alias_path(self, alias_path: str) -> str:
        """Convert macOS alias path to regular path."""
        # Remove "alias " prefix
        path_part = alias_path.replace("alias ", "").strip()
        
        # Split by colons and reconstruct the path
        parts = path_part.split(":")
        
        if len(parts) >= 2:
            # Standard macOS alias format: "Macintosh HD:Users:username:folder:subfolder"
            # Convert to Unix path: /Users/username/folder/subfolder
            if parts[0] == "Macintosh HD" and len(parts) >= 3:
                # Standard case: skip "Macintosh HD", convert rest
                unix_parts = parts[1:]  # Skip "Macintosh HD"
                selected_path = "/" + "/".join(unix_parts)
            else:
                # Fallback: assume it's already a partial path
                selected_path = "/" + "/".join(parts)
        else:
            # Single part, assume it's a folder name in root
            selected_path = "/" + path_part
        
        # Clean up the path
        selected_path = selected_path.replace("//", "/")  # Remove double slashes
        if selected_path.endswith("/") and len(selected_path) > 1:
            selected_path = selected_path[:-1]  # Remove trailing slash
            
        return selected_path
    
    def _create_step_buttons(self, next_text: str = "Continue", show_next: bool = True, is_final: bool = False) -> ft.Row:
        """Create navigation buttons for steps."""
        colors = self.theme_manager.colors
        
        buttons = []
        
        # Back button (not shown on first step)
        if self.current_step > 0:
            back_button = ft.TextButton(
                text="Back",
                icon=ft.Icons.ARROW_BACK,
                on_click=self._go_back,
                style=ft.ButtonStyle(
                    color=colors.text_secondary,
                    overlay_color=colors.hover
                )
            )
            buttons.append(back_button)
        
        # Add spacer if back button exists
        if buttons:
            buttons.append(ft.Container(expand=True))
        
        # Next/Complete button
        if show_next:
            next_button = ft.ElevatedButton(
                text=next_text,
                icon=ft.Icons.CHECK if is_final else ft.Icons.ARROW_FORWARD,
                icon_color=colors.text_on_primary,
                on_click=self._go_next if not is_final else self._complete_onboarding,
                style=ft.ButtonStyle(
                    bgcolor=colors.primary,
                    color=colors.text_on_primary,
                    text_style=ft.TextStyle(weight=ft.FontWeight.W_500),
                    padding=ft.padding.symmetric(horizontal=25, vertical=12)
                )
            )
            buttons.append(next_button)
        
        return ft.Row(
            controls=buttons,
            alignment=ft.MainAxisAlignment.CENTER if len(buttons) == 1 else ft.MainAxisAlignment.SPACE_BETWEEN
        )
    
    def _select_storage_location(self, e) -> None:
        """Handle storage location selection using native macOS dialog."""
        try:
            # Update button text to show it's working
            if hasattr(e, 'control'):
                e.control.text = "Opening..."
                e.control.update()
            
            # Use native macOS dialog via osascript
            import subprocess
            result = subprocess.run([
                "osascript", "-e", 
                'choose folder with prompt "Choose Journal Storage Location"'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                selected_path = result.stdout.strip()
                
                # Convert alias path to regular path if needed
                if selected_path.startswith("alias "):
                    # Extract the path from the alias format
                    # Format is: alias Macintosh HD:Users:username:Documents:
                    # We need to convert this to: /Users/username/Documents
                    selected_path = selected_path.replace("alias ", "")
                    
                    # Split by colons and reconstruct the path
                    parts = selected_path.split(":")
                    if len(parts) >= 4:  # Should have at least Macintosh HD, Users, username, Documents
                        # Skip "Macintosh HD" and "Users", start from username
                        username = parts[2]
                        folder = parts[3]
                        selected_path = f"/Users/{username}/{folder}"
                    else:
                        # Fallback: just replace colons with slashes
                        selected_path = selected_path.replace(":", "/")
                        # Remove trailing slash
                        if selected_path.endswith("/"):
                            selected_path = selected_path[:-1]
                
                # Store the selected path (don't create folder yet)
                journal_vault_path = os.path.join(selected_path, "Journal Vault")
                
                # Validate that we can create the folder in this location
                if os.access(selected_path, os.W_OK):
                    self.onboarding_data['storage_path'] = journal_vault_path
                    self.storage_path_text.value = journal_vault_path
                    self.storage_path_text.update()
                    # Recreate the step to show the next button
                    self.container.content.controls[2] = self._get_current_step_content()
                    self.container.update()
                else:
                    self._show_storage_error("Cannot create folder in selected location. Please choose a different location.")
            else:
                # User cancelled or error occurred
                self._show_storage_error("No folder selected or dialog was cancelled.")
            
            # Reset button text (only if control is still valid)
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Choose Folder"
                    e.control.update()
            except Exception:
                # Ignore button update errors
                pass
            
        except subprocess.TimeoutExpired:
            # Reset button text on timeout
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Choose Folder"
                    e.control.update()
            except Exception:
                pass
            self._show_storage_error("Folder selection dialog timed out. Please try again.")
        except Exception as ex:
            # Reset button text on error
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Choose Folder"
                    e.control.update()
            except Exception:
                pass
            self._show_storage_error(f"Could not open folder picker: {str(ex)}. Using default location instead.")
            self._use_default_location(e)
    
    def _on_folder_selected(self, result: ft.FilePickerResultEvent) -> None:
        """Handle file picker result."""
        try:
            if result.path and os.path.isdir(result.path):
                # Validate that the directory is writable
                if self._validate_storage_directory(result.path):
                    self.onboarding_data['storage_path'] = result.path
                    self.storage_path_text.value = result.path
                    self.storage_path_text.update()
                    # Recreate the step to show the next button
                    self.container.content.controls[2] = self._get_current_step_content()
                    self.container.update()
                else:
                    self._show_storage_error("Selected directory is not writable. Please choose a different location.")
            elif result.path:
                self._show_storage_error("Please select a valid directory.")
            else:
                # User cancelled - do nothing
                pass
        except Exception as ex:
            self._show_storage_error(f"Error selecting directory: {str(ex)}")
    
    def _use_default_location(self, _) -> None:
        """Use the default storage location."""
        try:
            default_path = os.path.expanduser("~/Documents/Journal Vault")
            
            # Create the directory if it doesn't exist
            if not os.path.exists(default_path):
                os.makedirs(default_path, exist_ok=True)
            
            # Validate the directory
            if self._validate_storage_directory(default_path):
                self.onboarding_data['storage_path'] = default_path
                self.storage_path_text.value = default_path
                self.storage_path_text.update()
                # Recreate the step to show the next button
                self.container.content.controls[2] = self._get_current_step_content()
                self.container.update()
            else:
                self._show_storage_error("Cannot create or access default directory. Please choose a custom location.")
                
        except Exception as ex:
            self._show_storage_error(f"Error setting up default location: {str(ex)}")
    
    def _offer_default_location(self, default_path: str) -> None:
        """Offer default location as fallback when file picker fails."""
        try:
            # Create the directory if it doesn't exist
            if not os.path.exists(default_path):
                os.makedirs(default_path, exist_ok=True)
            
            # Validate the directory
            if self._validate_storage_directory(default_path):
                self.onboarding_data['storage_path'] = default_path
                self.storage_path_text.value = f"{default_path} (default)"
                self.storage_path_text.update()
                # Recreate the step to show the next button
                self.container.content.controls[2] = self._get_current_step_content()
                self.container.update()
            
        except Exception:
            # If default also fails, just show error message
            pass
    
    # Removed unused dialog method
    
    
    def _go_back(self, _) -> None:
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step_content()
    
    def _go_next(self, e) -> None:
        """Go to next step."""
        # Handle special case for AI step (now at step 3)
        if self.current_step == 3:  # AI step (0-indexed)
            # Check if we need to wait for download or if user has made a choice
            if (self.download_progress.status == "downloading" or 
                (not self.ai_manager.is_model_available() and 
                 not self.onboarding_data.get('ai_skipped', False) and
                 self.download_progress.status not in ["complete", "error"])):
                # Can't proceed yet - download in progress or no choice made
                return
        
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self._update_step_content()
        else:
            # This should not happen as final step should call _complete_onboarding
            self._complete_onboarding(e)
    
    def _complete_onboarding(self, _) -> None:
        """Complete the onboarding process based on selected mode."""
        try:
            # Update AI settings in onboarding data
            if self.ai_manager.is_model_available() or self.download_progress.status == "complete":
                self.onboarding_data['ai_enabled'] = True
                self.onboarding_data['ai_model_downloaded'] = True
                model_path = self.ai_manager.get_model_path()
                if model_path:
                    self.onboarding_data['ai_model_path'] = str(model_path)
            
            if self.vault_mode == "create":
                # Create new vault
                storage_path = self.onboarding_data.get('storage_path')
                if not storage_path:
                    self._show_storage_error("No storage location configured.")
                    return
                
                # Check if folder already exists
                if os.path.exists(storage_path):
                    self._show_folder_exists_error()
                else:
                    self._create_new_vault(storage_path)
            
            else:  # load mode
                # Load existing vault
                loaded_vault_path = self.onboarding_data.get('loaded_vault_path')
                if not loaded_vault_path:
                    self._show_storage_error("No vault selected to load.")
                    return
                
                # Vault already validated in _load_existing_vault method
                self.on_complete(self.onboarding_data)
                
        except Exception as ex:
            self._show_storage_error(f"Error completing setup: {str(ex)}")
    
    def _create_new_vault(self, storage_path: str) -> None:
        """Create a new vault at the specified path."""
        try:
            # Create the folder
            os.makedirs(storage_path, exist_ok=True)
            
            # Validate that the folder was created successfully
            if os.path.exists(storage_path) and os.access(storage_path, os.W_OK):
                # Save vault name to onboarding data for config
                vault_name = self.onboarding_data.get('vault_name', 'My Journal')
                self.onboarding_data['vault_name'] = vault_name
                
                # Call completion callback
                self.on_complete(self.onboarding_data)
            else:
                self._show_storage_error("Failed to create vault folder. Please try again.")
        except Exception as ex:
            self._show_storage_error(f"Error creating vault: {str(ex)}")
    
    def _show_existing_vault_dialog(self, vault_path: str) -> None:
        """Show dialog when existing vault is detected."""
        try:
            def open_existing_vault(_):
                dialog.open = False
                if self.page:
                    self.page.update()
                # Use existing vault
                self.on_complete(self.onboarding_data)
            
            def choose_different_location(_):
                dialog.open = False
                if self.page:
                    self.page.update()
                # Reset parent directory selection
                self.onboarding_data['parent_directory'] = None
                self.onboarding_data['storage_path'] = None
                self.storage_location_text.value = "No location selected"
                self.storage_location_text.update()
                self._update_path_preview()
                # Refresh the step
                self.container.content.controls[2] = self._get_current_step_content()
                self.container.update()
            
            def close_dialog(_):
                dialog.open = False
                if self.page:
                    self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Existing Vault Found"),
                content=ft.Column(
                    controls=[
                        ft.Text("A Journal Vault already exists at:"),
                        ft.Text(vault_path, weight=ft.FontWeight.BOLD),
                        ft.Container(height=10),
                        ft.Text("What would you like to do?")
                    ],
                    tight=True,
                    spacing=10
                ),
                actions=[
                    ft.TextButton(
                        text="Open Existing Vault",
                        on_click=open_existing_vault,
                        style=ft.ButtonStyle(
                            bgcolor=self.theme_manager.colors.primary,
                            color=self.theme_manager.colors.text_on_primary
                        )
                    ),
                    ft.TextButton(
                        text="Choose Different Location",
                        on_click=choose_different_location
                    ),
                    ft.TextButton(
                        text="Cancel",
                        on_click=close_dialog
                    )
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            # Show dialog
            if self.page:
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
            else:
                # Fallback: assume user wants to open existing vault
                self.on_complete(self.onboarding_data)
        except Exception as ex:
            self._show_storage_error(f"Error handling existing vault: {str(ex)}")
    
    def _show_folder_exists_error(self) -> None:
        """Show error dialog when selected folder already exists."""
        try:
            def close_dialog(_):
                dialog.open = False
                if self.page:
                    self.page.update()
            
            dialog = ft.AlertDialog(
                title=ft.Text("Folder Already Exists"),
                content=ft.Column(
                    controls=[
                        ft.Text("A folder with this name already exists in the selected location."),
                        ft.Container(height=10),
                        ft.Text("Please choose a different name or select a different parent directory.")
                    ],
                    tight=True,
                    spacing=10
                ),
                actions=[
                    ft.TextButton("OK", on_click=close_dialog)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            # Show dialog
            if self.page:
                self.page.dialog = dialog
                dialog.open = True
                self.page.update()
        except Exception as ex:
            self._show_storage_error(f"Error showing folder exists dialog: {str(ex)}")
    
    def _can_load_as_vault(self, path: str) -> tuple[bool, str]:
        """Check if a folder can be loaded as a vault with smart detection.
        
        Returns:
            tuple[bool, str]: (is_valid, vault_type)
            vault_type can be: "confirmed_vault", "compatible_vault", "invalid_structure"
        """
        try:
            vault_path = Path(path)
            
            if not vault_path.exists() or not vault_path.is_dir():
                return False, "invalid_structure"
            
            # Check for confirmed vault (has .journal_vault directory)
            journal_vault_dir = vault_path / ".journal_vault"
            if journal_vault_dir.exists() and journal_vault_dir.is_dir():
                return True, "confirmed_vault"
            
            # Check for compatible vault (has entries structure)
            entries_dir = vault_path / "entries"
            if entries_dir.exists() and entries_dir.is_dir():
                # Look for YYYY/MM/*.md files
                has_journal_files = False
                for year_dir in entries_dir.iterdir():
                    if year_dir.is_dir() and year_dir.name.isdigit():
                        for month_dir in year_dir.iterdir():
                            if month_dir.is_dir() and month_dir.name.isdigit():
                                # Check for .md files
                                md_files = list(month_dir.glob("*.md"))
                                if md_files:
                                    has_journal_files = True
                                    break
                        if has_journal_files:
                            break
                
                if has_journal_files:
                    return True, "compatible_vault"
            
            # Check if folder is empty (not valid for loading)
            try:
                if not any(vault_path.iterdir()):
                    return False, "empty_folder"
            except PermissionError:
                return False, "permission_denied"
            
            # Has content but not journal structure
            return False, "invalid_structure"
            
        except Exception:
            return False, "invalid_structure"
    
    def _load_existing_vault(self, e) -> None:
        """Handle loading an existing vault."""
        try:
            # Update button text to show it's working
            if hasattr(e, 'control'):
                e.control.text = "Opening..."
                e.control.update()
            
            # Use native macOS dialog via osascript
            import subprocess
            result = subprocess.run([
                "osascript", "-e", 
                'choose folder with prompt "Select Existing Journal Vault Folder"'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                selected_path = result.stdout.strip()
                
                # Convert alias path to regular path if needed
                if selected_path.startswith("alias "):
                    selected_path = self._convert_alias_path(selected_path)
                
                # Use smart vault detection
                can_load, vault_type = self._can_load_as_vault(selected_path)
                
                if can_load:
                    # Set the loaded vault path and update UI
                    self.onboarding_data['loaded_vault_path'] = selected_path
                    self.onboarding_data['storage_path'] = selected_path
                    self.onboarding_data['vault_name'] = os.path.basename(selected_path)
                    self.onboarding_data['vault_type'] = vault_type  # Store for later reference
                    
                    # Refresh the storage step to show the updated path
                    self.container.content.controls[2] = self._get_current_step_content()
                    self.container.update()
                else:
                    # Show appropriate error message based on vault type
                    if vault_type == "empty_folder":
                        self._show_storage_error("Selected folder is empty. Please select a folder with existing journal entries or create a new vault instead.")
                    elif vault_type == "permission_denied":
                        self._show_storage_error("Cannot access the selected folder. Please check permissions and try again.")
                    else:  # invalid_structure
                        self._show_storage_error("Selected folder is not a valid Journal Vault.\n\nValid vaults should contain either:\n• A '.journal_vault' directory (confirmed vault)\n• An 'entries' folder with journal files (compatible vault)")
            else:
                # User cancelled - do nothing
                pass
            
            # Reset button text
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Load Existing Vault"
                    e.control.update()
            except Exception:
                pass
            
        except subprocess.TimeoutExpired:
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Load Existing Vault"
                    e.control.update()
            except Exception:
                pass
            self._show_storage_error("Folder selection dialog timed out. Please try again.")
        except Exception as ex:
            try:
                if hasattr(e, 'control') and e.control:
                    e.control.text = "Load Existing Vault"
                    e.control.update()
            except Exception:
                pass
            self._show_storage_error(f"Could not open folder picker: {str(ex)}")
    
    def _validate_storage_directory(self, path: str) -> bool:
        """Validate that the storage directory is accessible and writable."""
        try:
            # Check if directory exists and is writable
            if not os.path.exists(path):
                return False
            if not os.path.isdir(path):
                return False
            if not os.access(path, os.W_OK):
                return False
            
            # Try to create a test file to verify write permissions
            test_file = os.path.join(path, '.journal_vault_test')
            try:
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                return True
            except (IOError, OSError):
                return False
                
        except Exception:
            return False
    
    def _show_storage_error(self, message: str) -> None:
        """Show storage-related error message to user."""
        try:
            # Create error dialog
            def close_dialog(_):
                error_dialog.open = False
                self.page.update()
            
            error_dialog = ft.AlertDialog(
                title=ft.Text("Storage Selection Error"),
                content=ft.Text(message),
                actions=[
                    ft.TextButton("OK", on_click=close_dialog)
                ],
                actions_alignment=ft.MainAxisAlignment.END
            )
            
            # Show dialog - try multiple ways to get page reference
            page_ref = None
            if self.page:
                page_ref = self.page
            elif hasattr(self.container, 'page') and self.container.page:
                page_ref = self.container.page
            
            if page_ref:
                page_ref.dialog = error_dialog
                error_dialog.open = True
                page_ref.update()
            else:
                # Fallback to console output if no page reference
                print(f"Storage Error: {message}")
        except Exception as ex:
            print(f"Error showing storage error dialog: {ex}")
            print(f"Original error: {message}")
    
    def _update_step_content(self) -> None:
        """Update the step content and progress indicator."""
        self.container.content.controls[0] = self._create_progress_indicator()
        self.container.content.controls[2] = self._get_current_step_content()
        self.container.update()
    
    def get_container(self) -> ThemedContainer:
        """Get the main onboarding container."""
        return self.container
    
    def setup_page_overlays(self, page: ft.Page) -> None:
        """Set up page overlays including file picker."""
        # Ensure page has overlay list
        if not hasattr(page, 'overlay'):
            page.overlay = []
        
        # Add file picker to page overlay if not already added
        if self.file_picker not in page.overlay:
            page.overlay.append(self.file_picker)
            page.update()

    def _select_ai_option(self, option: str) -> None:
        """Handle AI option selection with visual feedback."""
        # Update onboarding data
        self.onboarding_data['ai_enabled'] = (option == "with_ai")
        
        # Update the action section based on selection
        self._update_action_section()
        
        # Update UI
        if self.page:
            self.page.update()
        else:
            self.container.update()

    def _update_action_section(self) -> None:
        """Update the action section based on AI selection."""
        # Recreate the AI setup content to reflect the new selection
        if hasattr(self, 'container') and self.container:
            try:
                self.container.content.controls[2] = self._get_current_step_content()
            except Exception:
                pass  # Ignore UI update errors
    
    def _continue_without_ai(self, _) -> None:
        """Handle continuing without AI features."""
        # Mark AI as skipped
        self.onboarding_data['ai_enabled'] = False
        self.onboarding_data['ai_skipped'] = True
        
        # Show confirmation dialog
        self._show_traditional_confirmation()
    
    def _show_traditional_confirmation(self) -> None:
        """Show confirmation dialog for traditional journal setup."""
        colors = self.theme_manager.colors
        
        def confirm_traditional(e):
            dialog.open = False
            if self.page:
                self.page.update()
            # Proceed to next step
            self._go_next(e)
        
        def go_back(_):
            dialog.open = False
            if self.page:
                self.page.update()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Continue with Traditional Journal?", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text("You've chosen the traditional journaling experience:", size=14),
                    ft.Container(height=12),
                    ft.Text("✓ Manual reflection and analysis", size=13),
                    ft.Text("✓ Basic text editing & formatting", size=13),
                    ft.Text("✓ Calendar view of entries", size=13),
                    ft.Text("✓ Simple storage & organization", size=13),
                    ft.Text("✓ Complete privacy", size=13),
                    ft.Container(height=12),
                    ft.Container(
                        content=ft.Text(
                            "💡 You can always add AI enhancement later in Settings.",
                            size=12,
                            color=colors.text_secondary,
                            italic=True
                        ),
                        padding=ft.padding.all(8),
                        bgcolor=colors.surface_variant,
                        border_radius=8
                    )
                ], tight=True, spacing=4),
                width=400
            ),
            actions=[
                ft.TextButton("Go Back", on_click=go_back, style=ft.ButtonStyle(color=colors.primary)),
                ft.ElevatedButton("Continue Setup", on_click=confirm_traditional, style=ft.ButtonStyle(bgcolor=colors.primary))
            ]
        )
        
        if self.page:
            self.page.dialog = dialog
            dialog.open = True
            self.page.update()