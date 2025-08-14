"""
Dana - safe journal space - Main Application Entry Point

A privacy-first desktop journaling application with local AI-powered insights.
"""

from datetime import datetime, timedelta, date
from typing import Set, Dict, Any, Optional
import flet as ft
from .ui.theme import (
    theme_manager,
    ThemedText,
    SPACING,
    COMPONENT_SIZES,
)
from .ui.components import (
    OnboardingFlow,
    CalendarComponent,
    EnhancedTextEditor,
    FileExplorer,
    AIReflectionComponent,
)
from .config import app_config
from .storage.file_manager import FileManager, JournalEntry
from .ai import AIReflectionService, AIServiceConfig


class JournalVaultApp:
    """Main application class for Dana - safe journal space."""

    def __init__(self, page: ft.Page):
        self.page = page
        self.theme_manager = theme_manager

        # App state
        self.is_onboarded = app_config.is_onboarded()
        self.storage_path = app_config.get_storage_path()
        self.selected_date = datetime.now()
        # Sample entry dates for demo purposes
        # In real implementation, this would be loaded from storage
        self.entry_dates: Set[datetime] = {
            datetime.now() - timedelta(days=1),
            datetime.now() - timedelta(days=3),
            datetime.now() - timedelta(days=7),
            datetime.now() - timedelta(days=10),
        }

        # No theme configuration needed - always dark mode

        # UI components
        self.calendar_component = None
        self.onboarding_flow = None
        self.text_editor = None
        self.file_explorer = None
        self.file_manager = None
        self.entry_title_component = None
        self.ai_reflection_component = None  # NEW

        # AI service
        self.ai_service: Optional[AIReflectionService] = None
        self._ai_thread = None  # Track AI generation threads

        # Current entry state
        self.current_entry_date = self.selected_date.date()
        self.current_entry_content = ""
        self.current_entry_exists = False

        # Delete confirmation UI
        self.delete_confirmation_sheet = None

        # Configure page
        self._setup_page()

        # Initialize AI service
        self._initialize_ai_service()

        # Create appropriate layout
        if self.is_onboarded:
            self._create_main_layout()
        else:
            self._create_onboarding_layout()

    def _setup_page(self) -> None:
        """Configure page properties and theme."""
        self.page.title = "Dana"

        # Apply saved window state
        window_state = app_config.get_window_state()
        self.page.window.width = window_state.get("width", 1400)
        self.page.window.height = window_state.get("height", 900)
        self.page.window.min_width = 1000
        self.page.window.min_height = 700
        self.page.window.center()

        # Listen for window close to save state
        def on_window_event(e):
            if e.data == "close":
                try:
                    app_config.set_window_state(
                        self.page.window.width or 1400, self.page.window.height or 900
                    )
                except Exception as ex:
                    print(f"Error saving window state: {ex}")

        self.page.window.on_event = on_window_event
        self.page.padding = 0
        self.page.spacing = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START

        # Apply dark theme colors
        colors = self.theme_manager.colors
        self.page.bgcolor = colors.background

    def _create_onboarding_layout(self) -> None:
        """Create the onboarding flow layout."""
        self.onboarding_flow = OnboardingFlow(
            self.theme_manager, on_complete=self._on_onboarding_complete, page=self.page
        )

        # Set up page overlays for file picker
        self.onboarding_flow.setup_page_overlays(self.page)

        self.page.add(self.onboarding_flow.get_container())

    def _on_onboarding_complete(self, onboarding_data: dict) -> None:
        """Handle onboarding completion."""
        # Save onboarding data using config system
        self.storage_path = onboarding_data.get("storage_path")
        app_config.set_storage_path(self.storage_path)

        # Save vault name
        vault_name = onboarding_data.get("vault_name")
        if vault_name:
            app_config.set_vault_name(vault_name)

        # Save AI configuration
        ai_enabled = onboarding_data.get("ai_enabled", False)
        app_config.set_ai_enabled(ai_enabled)

        ai_model_downloaded = onboarding_data.get("ai_model_downloaded", False)
        app_config.set_ai_model_downloaded(ai_model_downloaded)

        ai_skipped = onboarding_data.get("ai_skipped", False)
        app_config.set_ai_skipped_during_onboarding(ai_skipped)

        ai_model_path = onboarding_data.get("ai_model_path")
        if ai_model_path:
            app_config.set_ai_model_path(ai_model_path)

        # No theme preference to save - always dark mode

        # Mark onboarding as complete
        app_config.set_onboarded(True)

        # Initialize file manager with storage path
        self.file_manager = FileManager(self.storage_path)

        # Clear page and create main layout
        self.page.clean()
        self.is_onboarded = True

        # Reset page overlays since they were cleared
        if hasattr(self.page, "overlay") and self.page.overlay:
            self.page.overlay.clear()

        # Re-apply theme colors after clearing page
        colors = self.theme_manager.colors
        self.page.bgcolor = colors.background

        # Re-apply page configuration that might have been lost
        self.page.padding = 0
        self.page.spacing = 0
        self.page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
        self.page.vertical_alignment = ft.MainAxisAlignment.START

        self._create_main_layout()
        self.page.update()

    def _initialize_ai_service(self) -> None:
        """Initialize the AI reflection service."""
        try:
            print("DEBUG: Starting AI service initialization...")
            
            # Get AI settings from configuration
            ai_inference_settings = app_config.get_ai_inference_settings()
            print(f"DEBUG: AI inference settings: {ai_inference_settings}")

            # Configure AI service with user preferences
            ai_config = AIServiceConfig(
                cache_enabled=ai_inference_settings.get("cache_enabled", True),
                cache_expiry_hours=ai_inference_settings.get("cache_expiry_hours", 168),
                auto_load_model=ai_inference_settings.get("auto_load_model", True),
            )
            print(f"DEBUG: AI config created: cache_enabled={ai_config.cache_enabled}, auto_load_model={ai_config.auto_load_model}")

            # Initialize service with retry if needed
            print("DEBUG: Creating AIReflectionService...")
            self.ai_service = AIReflectionService(ai_config)
            print(f"DEBUG: AIReflectionService created. Available: {self.ai_service.is_available}")
            print(f"DEBUG: AI service detailed status: {self.ai_service.status}")
            
            # If initial creation failed but model exists, try immediate retry
            if not self.ai_service.is_available and hasattr(self.ai_service, 'retry_initialization'):
                print("DEBUG: Initial AI service creation failed, attempting immediate retry...")
                retry_success = self.ai_service.retry_initialization()
                print(f"DEBUG: Immediate retry result: {retry_success}")
                if retry_success:
                    print("DEBUG: AI service successfully initialized on immediate retry!")
                else:
                    print("DEBUG: Immediate retry also failed, will retry on first use")

            # Update service status
            app_config.update_ai_service_status(
                {
                    "last_model_load_success": self.ai_service.is_available,
                    "model_load_count": app_config.get_ai_service_status().get(
                        "model_load_count", 0
                    )
                    + 1,
                }
            )

            print(f"AI service initialized. Available: {self.ai_service.is_available}")
            
            # Test that the service remains available
            import time
            time.sleep(0.1)  # Small delay
            print(f"DEBUG: AI service still available after delay: {self.ai_service.is_available}")

        except Exception as e:
            error_msg = f"Failed to initialize AI service: {e}"
            print(error_msg)
            import traceback
            traceback.print_exc()

            # Update error status in config
            app_config.update_ai_service_status(
                {"last_model_load_error": str(e), "last_model_load_success": False}
            )

            self.ai_service = None

    def _create_main_layout(self) -> None:
        """Create the main three-panel layout with Obsidian-like design."""
        colors = self.theme_manager.colors

        # Initialize file manager if not already done
        if not self.file_manager:
            self.file_manager = FileManager(self.storage_path)
            print(f"Main: Initialized FileManager with path: {self.storage_path}")

        # Get actual entry dates from file manager (after ensuring it's properly initialized)
        try:
            actual_entry_dates = self.file_manager.get_entry_dates()
            print(f"Main: Loaded {len(actual_entry_dates)} entry dates from storage")
        except Exception as e:
            print(f"Main: Error loading entry dates: {e}")
            actual_entry_dates = set()

        # Left sidebar - Calendar and Files
        self.calendar_component = CalendarComponent(
            self.theme_manager,
            on_date_selected=self._on_date_selected,
            entry_dates=actual_entry_dates,
        )

        # File explorer component (reuse the same file_manager instance)
        self.file_explorer = FileExplorer(
            self.theme_manager,
            file_manager=self.file_manager,  # Use same instance
            on_file_select=self._on_file_selected,
            on_create_entry=self._on_file_created,
            on_delete_entry=self._on_file_deleted,
        )

        # Calendar section with consistent spacing
        calendar_section = ft.Container(
            content=self.calendar_component.get_container(),
            padding=ft.padding.all(SPACING["md"]),
        )

        # Files section with file explorer - REMOVED DOUBLE CONTAINER
        # The FileExplorer component already has its own ThemedContainer with proper padding
        files_section = self.file_explorer.get_container()

        # Left sidebar container with consistent sizing
        left_sidebar = ft.Container(
            content=ft.Column(
                controls=[
                    calendar_section,
                    ft.Container(height=1, bgcolor=colors.border_subtle),
                    files_section,
                ],
                spacing=0,
                expand=True,
            ),
            width=COMPONENT_SIZES["sidebar_width"],
            border=ft.border.only(right=ft.border.BorderSide(1, colors.border_subtle)),
        )

        # Main content area - Enhanced Text Editor
        # Initialize text editor with AI callback
        self.text_editor = EnhancedTextEditor(
            self.theme_manager,
            on_content_change=self._on_content_change,
            on_save=self._on_save_entry,
            on_ai_generate=self._on_ai_generate,  # NEW
            placeholder_text=f"Start writing your thoughts for {self.current_entry_date.strftime('%B %d, %Y')}...",
            auto_save_delay=3.0,
        )

        # Create entry title component
        self.entry_title_component = ThemedText(
            self.theme_manager,
            f"{self.current_entry_date.strftime('%B %d, %Y')}",
            variant="primary",
            typography="h4",
        )

        # Create delete button for entries (initially hidden)
        self.entry_delete_button = ft.IconButton(
            icon=ft.Icons.DELETE_OUTLINE,
            icon_size=COMPONENT_SIZES["icon_sm"],
            icon_color=colors.text_muted,
            tooltip="Delete this entry",
            visible=False,
            on_click=self._on_delete_current_entry,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=6),
                overlay_color=colors.error_subtle,
            ),
        )

        # Entry header with title and delete button
        entry_header = ft.Row(
            controls=[
                self.entry_title_component,
                ft.Container(expand=True),
                self.entry_delete_button,
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Initialize AI reflection component
        self.ai_reflection_component = AIReflectionComponent(
            self.theme_manager,
            on_regenerate=self._on_ai_regenerate,
            on_hide=self._on_ai_hide,
        )

        # Create scrollable container for text editor
        text_editor_scroll = ft.Container(
            content=self.text_editor.get_container(),
            # Expand is handled by the flex container above
        )

        # Create collapsible wisdom card container
        self.wisdom_container = ft.Container(
            content=self.ai_reflection_component.get_container(),
            # No margin or border - cleaner look
            # No fixed height - will be controlled by the component itself
            # Wisdom card will be collapsible and use flex ratios
        )

        # Journal entry section with conditional wisdom card
        journal_entry_section = ft.Container(
            content=ft.Column(
                controls=[
                    entry_header,
                    ft.Container(height=SPACING["sm"]),
                    # Text editor gets full space when wisdom card is hidden
                    ft.Container(
                        content=text_editor_scroll,
                        expand=True,
                    ),
                    # Wisdom card container - will be conditionally shown
                    self.wisdom_container,
                ],
                spacing=0,
                expand=True,
            ),
            padding=ft.padding.all(SPACING["md"]),
            expand=True,
        )

        # Main content area container (simplified - no separate AI section)
        main_content = ft.Container(
            content=journal_entry_section,
            expand=True,
        )

        # Main layout with left sidebar and main content (header removed for more writing space)
        main_layout = ft.Row(
            controls=[left_sidebar, main_content], spacing=0, expand=True
        )

        self.page.add(main_layout)

        # Load initial entry after page is updated
        self.page.update()

        # Now load initial entry
        if self.file_manager:
            self._load_entry_for_date(self.current_entry_date)
            self._update_entry_delete_button()

    def _on_date_selected(self, selected_date: datetime) -> None:
        """Handle date selection from calendar."""
        self.selected_date = selected_date
        new_date = selected_date.date()

        # Cancel any running AI process when switching entries
        if (
            hasattr(self, "_ai_thread")
            and self._ai_thread
            and self._ai_thread.is_alive()
        ):
            # Note: We can't easily cancel a thread, so we just note it
            # The thread will complete and be replaced by any new AI requests
            pass
            # Note: Don't hide AI reflection here - let it persist if it exists

        # Save current entry before switching
        if self.text_editor and self.current_entry_date != new_date:
            current_content = self.text_editor.get_content()
            if current_content.strip():  # Only save if there's content
                self._save_entry_for_date(self.current_entry_date, current_content)

        # Switch to new date
        self.current_entry_date = new_date

        # Load entry for new date
        self._load_entry_for_date(new_date)

        # Update text editor placeholder and title
        self._update_editor_for_date(new_date)

        # Update entry title
        if self.entry_title_component:
            title = f"{new_date.strftime('%B %d, %Y')}"
            self.entry_title_component.value = title
            self.entry_title_component.update()

        # Update file explorer selection
        if self.file_explorer:
            self.file_explorer.select_entry_by_date(new_date)

        # Update delete button visibility
        self._update_entry_delete_button()

        print(f"Selected date: {selected_date.strftime('%Y-%m-%d')}")

    def _on_file_selected(self, entry_date: date, entry: JournalEntry) -> None:
        """Handle file selection from file explorer."""
        if entry_date and entry:
            # Cancel any running AI process when switching entries
            if (
                hasattr(self, "_ai_thread")
                and self._ai_thread
                and self._ai_thread.is_alive()
            ):
                # Note: We can't easily cancel a thread, so we just note it
                # The thread will complete and be replaced by any new AI requests
                pass
                # Note: Don't hide AI reflection here - let it persist if it exists

            # Update calendar and load entry
            self.selected_date = datetime.combine(entry_date, datetime.min.time())
            self.current_entry_date = entry_date

            # Load entry content directly from provided entry (no need to reload from file)
            self.current_entry_content = entry.content

            # Update calendar selection
            if self.calendar_component:
                self.calendar_component.set_selected_date(self.selected_date)

            # Update text editor with entry content
            if self.text_editor:
                self.text_editor.set_content(entry.content)

            # Update entry title - always use date for consistency
            if self.entry_title_component:
                title = f"{entry_date.strftime('%B %d, %Y')}"
                self.entry_title_component.value = title
                self.entry_title_component.update()

            # Update file explorer selection state if needed
            if self.file_explorer:
                self.file_explorer.select_entry_by_date(entry_date)

            # Update delete button visibility
            self.current_entry_exists = True
            self._update_entry_delete_button()

            # Store AI reflection data and show minimal indicator
            # Let user decide when to view AI insights
            if entry.ai_reflection and self.ai_reflection_component:
                # Store the reflection data
                self.ai_reflection_component.current_reflection = entry.ai_reflection
                self.ai_reflection_component._update_content(entry.ai_reflection)
                # Show minimal indicator that AI reflection is available
                self.ai_reflection_component.show_available_indicator()
                # Show the wisdom container
                if hasattr(self, "wisdom_container"):
                    self.wisdom_container.visible = True
                    self.wisdom_container.update()
                print(
                    f"Loaded AI reflection data for entry: {entry_date} (showing indicator)"
                )

            print(f"Selected entry for date: {entry_date.strftime('%Y-%m-%d')}")

    def _on_file_created(self, entry_date) -> None:
        """Handle new file creation."""
        # Create new entry
        if self.file_manager:
            try:
                self.file_manager.create_entry(entry_date)

                # Update UI
                self._refresh_entry_dates()

                # Select the new entry
                self.selected_date = datetime.combine(entry_date, datetime.min.time())
                self._on_date_selected(self.selected_date)

                print(f"Created new entry for: {entry_date}")
            except Exception as e:
                print(f"Error creating entry: {e}")

    def _on_file_deleted(self, entry_date) -> None:
        """Handle file deletion."""
        # Delete entry from file manager
        if self.file_manager:
            try:
                self.file_manager.delete_entry(entry_date)

                # Update UI
                self._refresh_entry_dates()

                # Clear text editor if this was the current entry
                if self.current_entry_date == entry_date:
                    if self.text_editor:
                        self.text_editor.clear()
                    self.current_entry_exists = False
                    self._update_entry_delete_button()

                print(f"Deleted entry for: {entry_date}")
            except Exception as e:
                print(f"Error deleting entry: {e}")

    def _on_content_change(self, content: str) -> None:
        """Handle content changes from text editor."""
        self.current_entry_content = content
        self.current_entry_exists = bool(content.strip())
        
        # Update delete button visibility when content changes
        self._update_entry_delete_button()

    def _on_save_entry(self, content: str) -> None:
        """Handle save requests from text editor."""
        self._save_entry_for_date(self.current_entry_date, content)

    def _on_ai_generate(self, content: str) -> None:
        """Handle AI generation request from toolbar button."""
        if not content.strip():
            return

        # Show generating state - component handles its own visibility
        self.ai_reflection_component.show_generating_state()

        # Generate AI reflection
        self._generate_ai_reflection(content)

    def _on_ai_regenerate(self) -> None:
        """Handle AI regeneration request."""
        content = self.text_editor.get_content()
        if content.strip():
            # Show generating state immediately for visual feedback
            self.ai_reflection_component.show_generating_state()
            # Force regeneration by clearing cache
            self._generate_ai_reflection(content, force_regenerate=True)
        else:
            # Re-enable button if no content to regenerate
            self.ai_reflection_component._set_regenerate_button_loading(False)

    def _on_ai_hide(self) -> None:
        """Handle AI hide request."""
        self.ai_reflection_component.hide()

        # Clear AI reflection data from the entry
        self._clear_ai_reflection_from_entry()

    def _clear_ai_reflection_from_entry(self) -> None:
        """Clear AI reflection data from the current journal entry."""
        if not self.file_manager:
            return

        try:
            # Load current entry
            entry = self.file_manager.load_entry(self.current_entry_date)
            if entry:
                # Clear AI reflection data
                entry.ai_reflection = None
                entry.modified_at = datetime.now()

                # Save the entry without AI reflection data
                self.file_manager.save_entry(entry)
                print(f"Cleared AI reflection for entry: {self.current_entry_date}")
        except Exception as e:
            print(f"Error clearing AI reflection: {e}")

    def _generate_ai_reflection(
        self, content: str, force_regenerate: bool = False
    ) -> None:
        """Generate AI reflection for journal content."""
        import threading
        import asyncio

        def run_ai_generation():
            """Run AI generation in a separate thread with its own event loop."""
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Run the async generation
                loop.run_until_complete(
                    self._generate_reflection_async(content, force_regenerate)
                )
            finally:
                loop.close()

        # Cancel any existing AI task
        if (
            hasattr(self, "_ai_thread")
            and self._ai_thread
            and self._ai_thread.is_alive()
        ):
            # Note: We can't easily cancel a thread, so we'll just start a new one
            pass

        # Start new AI generation in a separate thread
        self._ai_thread = threading.Thread(target=run_ai_generation, daemon=True)
        self._ai_thread.start()

    async def _generate_reflection_async(
        self, content: str, force_regenerate: bool = False
    ) -> None:
        """Async method to generate AI reflection."""
        try:
            # Enhanced debugging for AI service availability
            print(f"DEBUG: AI service object exists: {self.ai_service is not None}")
            if self.ai_service:
                print(f"DEBUG: AI service is_available: {self.ai_service.is_available}")
                print(f"DEBUG: AI service status: {self.ai_service.status}")
                
            # Progress callback to update UI
            def update_progress(message: str):
                # Update the UI based on the message type
                if "Loading AI model" in message or "Initializing" in message:
                    self.ai_reflection_component.show_model_loading_state()
                elif "Generating" in message or "Processing" in message:
                    self.ai_reflection_component.show_generating_state()
                elif hasattr(self.ai_reflection_component, "update_generating_status"):
                    self.ai_reflection_component.update_generating_status(message)

            # Check if AI service is available, with silent retry attempt
            if not self.ai_service or not self.ai_service.is_available:
                # Try to retry initialization if service exists but isn't available
                retry_attempted = False
                if self.ai_service and hasattr(self.ai_service, 'retry_initialization'):
                    print("DEBUG: Attempting to retry AI service initialization...")
                    # Show loading message during retry instead of error
                    update_progress("Initializing AI service...")
                    
                    retry_success = self.ai_service.retry_initialization()
                    retry_attempted = True
                    print(f"DEBUG: Retry initialization result: {retry_success}")
                    if retry_success:
                        print("DEBUG: AI service successfully initialized on retry!")
                        # Continue with normal generation flow
                    else:
                        print("DEBUG: Retry initialization failed")
                
                # Only show error if retry was not attempted or failed
                if not self.ai_service or not self.ai_service.is_available:
                    # Enhanced error message with debugging info
                    debug_info = "No AI service" if not self.ai_service else f"Service exists but unavailable: {self.ai_service.status}"
                    print(f"DEBUG: AI not available - {debug_info}")
                    
                    # Show appropriate message based on whether we tried to retry
                    if retry_attempted:
                        error_message = "AI service failed to initialize. Please restart the application or check if the AI model is properly installed."
                    else:
                        error_message = "AI reflection is not currently available. Please ensure the AI model is downloaded."
                    
                    # Show fallback message
                    fallback_data = {
                        "insights": [
                            error_message
                        ],
                        "questions": [
                            "What insights can you draw from this entry on your own?"
                        ],
                        "themes": ["reflection"],
                        "generated_at": datetime.now().isoformat(),
                    }
                    self.ai_reflection_component.show_reflection(fallback_data)
                    self.ai_reflection_component._set_regenerate_button_loading(False)
                    return

            # Check if model is currently loading
            if self.ai_service.is_loading:
                # Show model loading state instead of generating state
                self.ai_reflection_component.show_model_loading_state()
                # The service will wait for loading to complete, so we can proceed normally

            # Generate reflection using AI service
            entry_date_str = self.current_entry_date.isoformat()
            result = await self.ai_service.generate_reflection(
                content=content,
                entry_date=entry_date_str,
                progress_callback=update_progress,
                force_regenerate=force_regenerate,
            )

            # Convert ReflectionResult to dict format expected by UI
            reflection_data = {
                "insights": result.insights,
                "questions": result.questions,
                "themes": result.themes,
                "generated_at": result.generated_at,
                "model_used": result.model_used,
                "generation_time": result.generation_time,
                "cached": result.cached,
            }

            # Show the reflection and re-enable regenerate button
            self.ai_reflection_component.show_reflection(reflection_data)
            self.ai_reflection_component._set_regenerate_button_loading(False)

            # Save AI reflection data to the journal entry
            self._save_ai_reflection_to_entry(reflection_data)

            # Log result and update statistics
            status = "cached" if result.cached else "generated"
            print(
                f"AI reflection {status} in {result.generation_time:.2f}s for entry: {self.current_entry_date}"
            )

            # Update success statistics
            if result.error is None:
                app_config.update_ai_service_status(
                    {
                        "successful_generations": app_config.get_ai_service_status().get(
                            "successful_generations", 0
                        )
                        + 1
                    }
                )
            else:
                app_config.update_ai_service_status(
                    {
                        "failed_generations": app_config.get_ai_service_status().get(
                            "failed_generations", 0
                        )
                        + 1
                    }
                )

        except Exception as e:
            error_msg = f"Error generating AI reflection: {e}"
            print(error_msg)

            # Update failure statistics
            app_config.update_ai_service_status(
                {
                    "failed_generations": app_config.get_ai_service_status().get(
                        "failed_generations", 0
                    )
                    + 1,
                    "last_model_load_error": error_msg,
                }
            )

            # Show user-friendly error based on error type and re-enable button
            if "memory" in str(e).lower() or "insufficient" in str(e).lower():
                self.ai_reflection_component.show_error_state(
                    "Not enough memory available. Try closing other applications and regenerating."
                )
            elif "model" in str(e).lower() or "not found" in str(e).lower():
                self.ai_reflection_component.show_error_state(
                    "AI model not available. Please ensure the AI model is downloaded in settings."
                )
            else:
                self.ai_reflection_component.show_error_state(
                    f"AI analysis temporarily unavailable: {str(e)}"
                )

            # Ensure button is re-enabled in all error cases
            self.ai_reflection_component._set_regenerate_button_loading(False)

    def _save_ai_reflection_to_entry(self, reflection_data: Dict[str, Any]) -> None:
        """Save AI reflection data to the current journal entry."""
        if not self.file_manager:
            return

        try:
            # Load current entry
            entry = self.file_manager.load_entry(self.current_entry_date)
            if entry:
                # Update AI reflection data
                entry.ai_reflection = reflection_data
                entry.modified_at = datetime.now()

                # Save the entry with AI reflection data
                self.file_manager.save_entry(entry)
                print(f"Saved AI reflection for entry: {self.current_entry_date}")
            else:
                print(
                    f"Could not save AI reflection - no entry found for {self.current_entry_date}"
                )
        except Exception as e:
            print(f"Error saving AI reflection: {e}")

    def _load_entry_for_date(self, entry_date) -> None:
        """Load entry content for a specific date."""
        if not self.file_manager:
            return

        # Hide AI reflection when loading a new entry (will be shown if data exists)
        if self.ai_reflection_component:
            self.ai_reflection_component.hide()

        try:
            entry = self.file_manager.load_entry(entry_date)
            if entry:
                self.current_entry_content = entry.content
                self.current_entry_exists = True
                if (
                    self.text_editor
                    and hasattr(self.text_editor, "text_field")
                    and self.text_editor.text_field
                ):
                    self.text_editor.set_content(entry.content)

                # Store AI reflection data and show minimal indicator
                # Let user decide when to view AI insights
                if entry.ai_reflection and self.ai_reflection_component:
                    # Store the reflection data
                    self.ai_reflection_component.current_reflection = (
                        entry.ai_reflection
                    )
                    self.ai_reflection_component._update_content(entry.ai_reflection)
                    # Show minimal indicator that AI reflection is available
                    self.ai_reflection_component.show_available_indicator()
                    # Show the wisdom container
                    if hasattr(self, "wisdom_container"):
                        self.wisdom_container.visible = True
                        self.wisdom_container.update()
                    print(
                        f"Loaded AI reflection data for entry: {entry_date} (showing indicator)"
                    )
            else:
                self.current_entry_content = ""
                self.current_entry_exists = False
                if (
                    self.text_editor
                    and hasattr(self.text_editor, "text_field")
                    and self.text_editor.text_field
                ):
                    self.text_editor.clear()
        except Exception as e:
            print(f"Error loading entry for {entry_date}: {e}")
            self.current_entry_content = ""
            self.current_entry_exists = False
            if (
                self.text_editor
                and hasattr(self.text_editor, "text_field")
                and self.text_editor.text_field
            ):
                self.text_editor.clear()

        # Update delete button visibility
        self._update_entry_delete_button()

    def _save_entry_for_date(self, entry_date, content: str) -> None:
        """Save entry content for a specific date."""
        if not self.file_manager or not content.strip():
            return

        try:
            # Load existing entry or create new one
            entry = self.file_manager.load_entry(entry_date)
            if entry:
                entry.content = content
                self.file_manager.save_entry(entry)
            else:
                self.file_manager.create_entry(entry_date, content=content)

            # Update entry dates in UI components
            self._refresh_entry_dates()

            print(f"Saved entry for {entry_date}")
        except Exception as e:
            print(f"Error saving entry for {entry_date}: {e}")

    def _update_editor_for_date(self, entry_date) -> None:
        """Update text editor for a specific date."""
        if not self.text_editor:
            return

        # Update placeholder text dynamically
        new_placeholder = (
            f"Start writing your thoughts for {entry_date.strftime('%B %d, %Y')}..."
        )
        self.text_editor.update_placeholder(new_placeholder)

        print(f"Editor updated for date: {entry_date}")

    def _refresh_entry_dates(self) -> None:
        """Refresh entry dates in all UI components."""
        if not self.file_manager:
            return

        try:
            entry_dates = self.file_manager.get_entry_dates()

            # Update calendar
            if self.calendar_component:
                self.calendar_component.update_entry_dates(entry_dates)

            # Update file explorer
            if self.file_explorer:
                self.file_explorer.update_entry_dates(entry_dates)

        except Exception as e:
            print(f"Error refreshing entry dates: {e}")

    def _update_entry_delete_button(self) -> None:
        """Update the visibility of the entry delete button."""
        if self.entry_delete_button:
            # Show delete button only if entry exists
            should_show = self.current_entry_exists
            print(
                f"Update delete button: current_entry_exists={self.current_entry_exists}, should_show={should_show}"
            )
            if self.entry_delete_button.visible != should_show:
                self.entry_delete_button.visible = should_show
                try:
                    self.entry_delete_button.update()
                    print(f"Delete button visibility updated to: {should_show}")
                except Exception as e:
                    print(f"Error updating delete button visibility: {e}")

    def _on_delete_current_entry(self, e: ft.ControlEvent) -> None:
        """Handle delete button click for current entry."""
        _ = e
        print(
            f"Delete button clicked. current_entry_exists: {self.current_entry_exists}"
        )
        if not self.current_entry_exists:
            print("No current entry exists, not showing delete dialog")
            return

        # Show simple confirmation overlay (macOS-friendly)
        self._show_delete_confirmation()

    def _show_delete_confirmation(self) -> None:
        """Show delete confirmation using BottomSheet."""
        colors = self.theme_manager.colors
        entry_title = self.current_entry_date.strftime("%B %d, %Y")

        def on_confirm(e):
            """Handle delete confirmation."""
            _ = e
            print("User confirmed deletion")
            self._hide_delete_confirmation()
            # Delete the entry
            self._on_file_deleted(self.current_entry_date)

        def on_cancel(e):
            """Handle delete cancellation."""
            _ = e
            print("User cancelled deletion")
            self._hide_delete_confirmation()

        # Create BottomSheet content
        sheet_content = ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(height=20),
                    ft.Text(
                        "Delete Entry",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                        color=colors.text_primary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=10),
                    ft.Text(
                        f"Delete entry for {entry_title}?",
                        size=16,
                        color=colors.text_secondary,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Text(
                        "This action cannot be undone.",
                        size=14,
                        color=colors.text_muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                    ft.Container(height=30),
                    ft.Row(
                        controls=[
                            ft.Container(
                                content=ft.ElevatedButton(
                                    "Cancel",
                                    on_click=on_cancel,
                                    style=ft.ButtonStyle(
                                        color=colors.text_primary,
                                        bgcolor=colors.surface_variant,
                                    ),
                                    width=120,
                                ),
                                expand=1,
                            ),
                            ft.Container(width=20),
                            ft.Container(
                                content=ft.ElevatedButton(
                                    "Delete",
                                    on_click=on_confirm,
                                    style=ft.ButtonStyle(
                                        color="#FFFFFF",
                                        bgcolor=colors.error,
                                    ),
                                    width=120,
                                ),
                                expand=1,
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                    ft.Container(height=20),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                tight=True,
            ),
            padding=ft.padding.all(20),
            bgcolor=colors.surface,
        )

        # Create BottomSheet
        self.delete_confirmation_sheet = ft.BottomSheet(
            content=sheet_content,
            dismissible=True,
            on_dismiss=lambda _: print("Delete confirmation dismissed"),
        )

        # Show the sheet
        try:
            self.page.open(self.delete_confirmation_sheet)
            print("Delete confirmation sheet shown")
        except Exception as e:
            print(f"Error showing delete confirmation sheet: {e}")

    def _hide_delete_confirmation(self) -> None:
        """Hide delete confirmation sheet."""
        if self.delete_confirmation_sheet:
            try:
                self.page.close(self.delete_confirmation_sheet)
                self.delete_confirmation_sheet = None
                print("Delete confirmation sheet hidden")
            except Exception as e:
                print(f"Error hiding delete confirmation sheet: {e}")

    def run(self) -> None:
        """Run the application."""
        self.page.update()


def main_gui(page: ft.Page) -> None:
    """GUI entry point for Flet app."""
    app = JournalVaultApp(page)
    app.run()


def main() -> None:
    """CLI entry point for the application."""
    import os

    # Get assets directory path
    assets_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets")
    assets_dir = os.path.abspath(assets_dir)

    print("🚀 Starting Dana")
    print(f"📁 Assets directory: {assets_dir}")

    # Run with custom configuration for Dana branding
    ft.app(
        target=main_gui,
        name="Dana",  # App name for system identification
        assets_dir=assets_dir,  # Assets directory for icons and resources
        view=ft.AppView.FLET_APP,  # Use native app view (not web view)
    )


if __name__ == "__main__":
    main()
