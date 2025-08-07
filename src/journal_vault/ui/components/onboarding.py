"""
Onboarding Flow for AI Journal Vault

Comprehensive onboarding experience including welcome screen, privacy explanation,
storage location selection, theme preference, and optional first entry creation.
"""

import os
from typing import Callable, Optional
from pathlib import Path
import flet as ft
from ..theme import ThemeManager, ThemedContainer, ThemedText, SPACING
from ...storage.file_manager import FileManager


class OnboardingFlow:
    """Multi-step onboarding flow for new users."""
    
    def __init__(self, theme_manager: ThemeManager, on_complete: Callable[[dict], None], page: Optional[ft.Page] = None):
        self.theme_manager = theme_manager
        self.on_complete = on_complete
        self.page = page
        self.current_step = 0
        self.total_steps = 3
        self.vault_mode = "create"  # "create" or "load"
        self.onboarding_data = {
            'storage_path': None,
            'vault_name': 'My Journal',
            'parent_directory': None,
        }
        
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
                    "Welcome to AI Journal Vault",
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
                                    active_color=colors.primary
                                ),
                                ft.Radio(
                                    value="load",
                                    label="Load Existing Vault",
                                    active_color=colors.accent
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
                    next_text="Create Vault" if self.vault_mode == "create" else "Complete Setup",
                    show_next=self._is_ready_to_proceed(),
                    is_final=True
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
    
    def _use_documents_folder(self, e) -> None:
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
    
    def _use_default_location(self, e) -> None:
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
    
    
    def _go_back(self, e) -> None:
        """Go to previous step."""
        if self.current_step > 0:
            self.current_step -= 1
            self._update_step_content()
    
    def _go_next(self, e) -> None:
        """Go to next step."""
        if self.current_step < self.total_steps - 1:
            self.current_step += 1
            self._update_step_content()
        else:
            # This should not happen as final step should call _complete_onboarding
            self._complete_onboarding(e)
    
    def _complete_onboarding(self, e) -> None:
        """Complete the onboarding process based on selected mode."""
        try:
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
            def open_existing_vault(e):
                dialog.open = False
                if self.page:
                    self.page.update()
                # Use existing vault
                self.on_complete(self.onboarding_data)
            
            def choose_different_location(e):
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
            
            def close_dialog(e):
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
            def close_dialog(e):
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
            def close_dialog(e):
                error_dialog.open = False
                e.page.update()
            
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