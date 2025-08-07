"""
Onboarding Flow for AI Journal Vault

Comprehensive onboarding experience including welcome screen, privacy explanation,
storage location selection, theme preference, and optional first entry creation.
"""

import os
from typing import Callable, Optional
import flet as ft
from ..theme import ThemeManager, ThemedContainer, ThemedText, ThemedCard, ThemedButton, SPACING
from ...storage.file_manager import FileManager


class OnboardingFlow:
    """Multi-step onboarding flow for new users."""
    
    def __init__(self, theme_manager: ThemeManager, on_complete: Callable[[dict], None], page: Optional[ft.Page] = None):
        self.theme_manager = theme_manager
        self.on_complete = on_complete
        self.page = page
        self.current_step = 0
        self.total_steps = 3
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
        """Create compact vault setup step with name and location selection."""
        colors = self.theme_manager.colors
        
        # Create UI components
        self._create_vault_setup_components()
        
        return ft.Column(
            controls=[
                # Compact header with smaller icon
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.CREATE_NEW_FOLDER_ROUNDED,
                        size=50,  # Reduced from 80px to 50px
                        color=colors.accent
                    ),
                    margin=ft.margin.only(bottom=15)  # Reduced margin
                ),
                ThemedText(
                    self.theme_manager,
                    "Set Up Your Vault",
                    variant="primary",
                    size=24,  # Reduced from 28 to 24
                    weight=ft.FontWeight.BOLD,
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=8),  # Reduced spacing
                ThemedText(
                    self.theme_manager,
                    "Choose a name and location for your journal vault",
                    variant="secondary",
                    size=14,  # Reduced from 16 to 14
                    text_align=ft.TextAlign.CENTER
                ),
                ft.Container(height=16),  # Reduced spacing
                
                # Combined compact layout - single container for both sections
                ThemedContainer(
                    self.theme_manager,
                    variant="surface",
                    content=ft.Column(
                        controls=[
                            # Vault Name Section - more compact
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
                            
                            ft.Container(height=16),  # Divider spacing
                            ft.Divider(color=colors.border_subtle, height=1),
                            ft.Container(height=16),
                            
                            # Storage Location Section - more compact
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
                ),
                
                ft.Container(height=12),  # Reduced spacing
                
                # Path Preview Section - more compact
                ThemedContainer(
                    self.theme_manager,
                    variant="surface_variant",
                    content=ft.Row(
                        controls=[
                            ft.Icon(ft.Icons.PREVIEW, color=colors.primary, size=16),
                            ft.Column(
                                controls=[
                                    ThemedText(
                                        self.theme_manager,
                                        "Vault will be created at:",
                                        variant="secondary",
                                        size=12
                                    ),
                                    self.path_preview_text
                                ],
                                spacing=2,
                                expand=True
                            )
                        ],
                        spacing=8,
                        vertical_alignment=ft.CrossAxisAlignment.CENTER
                    ),
                    padding=ft.padding.all(SPACING["sm"]),  # Reduced padding
                    border_radius=8
                ),
                
                ft.Container(height=20),  # Navigation button spacing
                self._create_step_buttons(
                    next_text="Create Vault",
                    show_next=bool(self.onboarding_data.get('parent_directory')),
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
        if hasattr(self, 'path_preview_text'):
            self.path_preview_text.value = self._get_preview_path()
            try:
                self.path_preview_text.update()
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
        selected_path = alias_path.replace("alias ", "")
        
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
        """Complete the onboarding process with vault safety checks."""
        try:
            storage_path = self.onboarding_data.get('storage_path')
            if not storage_path:
                self._show_storage_error("No storage location configured.")
                return
            
            # Check if vault already exists
            if FileManager.is_existing_vault(storage_path):
                self._show_existing_vault_dialog(storage_path)
            else:
                self._create_new_vault(storage_path)
                
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
                        ft.Text(f"A Journal Vault already exists at:"),
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