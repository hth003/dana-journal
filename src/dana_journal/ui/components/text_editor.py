"""
Enhanced Text Editor Component for Dana - safe journal space

A sophisticated markdown-aware text editor with auto-save and
formatting shortcuts.
"""

import asyncio
import threading
from typing import Callable, Optional
import flet as ft
from ..theme import ThemeManager, ThemedCard, SPACING, COMPONENT_SIZES, TYPO_SCALE


class AutoSaveManager:
    """Manage auto-save functionality with debouncing."""

    def __init__(
        self, save_callback: Callable[[str], None], delay_seconds: float = 2.0
    ):
        self.save_callback = save_callback
        self.delay_seconds = delay_seconds
        self._save_task: Optional[asyncio.Task] = None
        self._last_content = ""

    async def schedule_save(self, content: str) -> None:
        """Schedule a save operation with debouncing."""
        if content == self._last_content:
            return

        # Cancel existing save task
        if self._save_task and not self._save_task.done():
            self._save_task.cancel()

        # Schedule new save
        self._save_task = asyncio.create_task(self._delayed_save(content))

    async def _delayed_save(self, content: str) -> None:
        """Execute delayed save operation."""
        try:
            await asyncio.sleep(self.delay_seconds)
            self.save_callback(content)
            self._last_content = content
        except asyncio.CancelledError:
            pass  # Task was cancelled, which is expected


class MarkdownHelper:
    """Helper for markdown formatting shortcuts."""

    @staticmethod
    def get_markdown_shortcuts() -> dict[str, str]:
        """Get available markdown formatting shortcuts."""
        return {
            "Ctrl+B": "**Bold**",
            "Ctrl+I": "*Italic*",
            "Ctrl+K": "[Link](url)",
            "Ctrl+1": "# Heading 1",
            "Ctrl+2": "## Heading 2",
            "Ctrl+3": "### Heading 3",
        }

    @staticmethod
    def apply_bold(
        text: str, selection_start: int, selection_end: int
    ) -> tuple[str, int, int]:
        """Apply bold formatting to selected text."""
        if selection_start == selection_end:
            # No selection - insert bold placeholder
            before = text[:selection_start]
            after = text[selection_start:]
            new_text = before + "**bold text**" + after
            return new_text, selection_start + 2, selection_start + 11
        else:
            # Has selection - wrap in bold
            before = text[:selection_start]
            selected = text[selection_start:selection_end]
            after = text[selection_end:]
            new_text = before + f"**{selected}**" + after
            return new_text, selection_start + 2, selection_end + 2

    @staticmethod
    def apply_italic(
        text: str, selection_start: int, selection_end: int
    ) -> tuple[str, int, int]:
        """Apply italic formatting to selected text."""
        if selection_start == selection_end:
            # No selection - insert italic placeholder
            before = text[:selection_start]
            after = text[selection_start:]
            new_text = before + "*italic text*" + after
            return new_text, selection_start + 1, selection_start + 12
        else:
            # Has selection - wrap in italic
            before = text[:selection_start]
            selected = text[selection_start:selection_end]
            after = text[selection_end:]
            new_text = before + f"*{selected}*" + after
            return new_text, selection_start + 1, selection_end + 1


class EnhancedTextEditor:
    """Enhanced text editor with markdown support and auto-save."""

    def __init__(
        self,
        theme_manager: ThemeManager,
        on_content_change: Optional[Callable[[str], None]] = None,
        on_save: Optional[Callable[[str], None]] = None,
        on_ai_generate: Optional[Callable[[str], None]] = None,
        placeholder_text: str = "Start writing your thoughts...",
        auto_save_delay: float = 2.0,
    ):
        self.theme_manager = theme_manager
        self.on_content_change = on_content_change
        self.on_save = on_save
        self.on_ai_generate = on_ai_generate
        self.placeholder_text = placeholder_text
        self.auto_save_delay = auto_save_delay

        # Content state
        self._content = ""
        self._last_saved_content = ""
        self._is_dirty = False
        self._save_timer = None  # NEW

        # Auto-save manager
        self.auto_save_manager = AutoSaveManager(
            save_callback=self._handle_auto_save, delay_seconds=auto_save_delay
        )

        # UI Components
        self.text_field = None
        self.toolbar = None
        self.save_indicator = None
        self.container = None

        # Build the component
        self.container = self._build_component()

    def _build_component(self) -> ft.Control:
        """Build the enhanced text editor UI."""
        colors = self.theme_manager.colors

        # Create toolbar with formatting shortcuts
        self.toolbar = self._create_toolbar()

        # Create main text field
        self.text_field = ft.TextField(
            hint_text=self.placeholder_text,
            multiline=True,
            min_lines=20,
            max_lines=None,
            border=ft.InputBorder.NONE,
            hint_style=ft.TextStyle(color=colors.text_muted, size=TYPO_SCALE["body"]),
            text_style=ft.TextStyle(
                color=colors.text_primary,
                size=TYPO_SCALE["body"],
                height=1.7,  # Improved line height for better readability
                font_family="-apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif",  # Better system fonts
            ),
            bgcolor="transparent",
            on_change=self._on_text_change,
            on_focus=self._on_focus,
            on_blur=self._on_blur,
            expand=True,
            cursor_color=colors.primary,
            selection_color=colors.primary + "40",  # Primary with opacity
            keyboard_type=ft.KeyboardType.MULTILINE,
        )

        # Main container
        container = ThemedCard(
            self.theme_manager,
            elevation="md",
            content=ft.Column(
                controls=[
                    self.toolbar,
                    ft.Container(
                        height=1,
                        bgcolor=colors.border_subtle,
                        margin=ft.margin.symmetric(vertical=SPACING["sm"]),
                    ),
                    ft.Container(
                        content=self.text_field,
                        expand=True,
                        padding=ft.padding.all(SPACING["md"]),
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            spacing="none",
            expand=True,
        )

        return container

    def _create_toolbar(self) -> ft.Row:
        """Create formatting toolbar."""
        colors = self.theme_manager.colors

        def create_format_button(
            icon: str, tooltip: str, on_click: Callable, icon_color: str = None
        ) -> ft.IconButton:
            return ft.IconButton(
                icon=icon,
                tooltip=tooltip,
                icon_size=COMPONENT_SIZES["icon_sm"],
                icon_color=icon_color or colors.text_muted,
                on_click=on_click,
                style=ft.ButtonStyle(
                    shape=ft.RoundedRectangleBorder(radius=6),
                    overlay_color=colors.hover,
                ),
            )

        return ft.Row(
            controls=[
                # Formatting buttons
                create_format_button(
                    ft.Icons.FORMAT_BOLD, "Bold (Ctrl+B)", lambda _: self._apply_bold()
                ),
                create_format_button(
                    ft.Icons.FORMAT_ITALIC,
                    "Italic (Ctrl+I)",
                    lambda _: self._apply_italic(),
                ),
                create_format_button(
                    ft.Icons.LINK, "Link (Ctrl+K)", lambda _: self._apply_link()
                ),
                # Separator
                ft.Container(
                    width=1,
                    height=20,
                    bgcolor=colors.border_subtle,
                    margin=ft.margin.symmetric(horizontal=SPACING["sm"]),
                ),
                # Heading buttons
                create_format_button(
                    ft.Icons.LOOKS_ONE,
                    "Heading 1 (Ctrl+1)",
                    lambda _: self._apply_heading(1),
                ),
                create_format_button(
                    ft.Icons.LOOKS_TWO,
                    "Heading 2 (Ctrl+2)",
                    lambda _: self._apply_heading(2),
                ),
                create_format_button(
                    ft.Icons.LOOKS_3,
                    "Heading 3 (Ctrl+3)",
                    lambda _: self._apply_heading(3),
                ),
                # Separator
                ft.Container(
                    width=1,
                    height=20,
                    bgcolor=colors.border_subtle,
                    margin=ft.margin.symmetric(horizontal=SPACING["sm"]),
                ),
                # AI Button (NEW)
                create_format_button(
                    ft.Icons.NATURE_PEOPLE,  # Same icon as Dana's Wisdom
                    "Request Dana's Wisdom",
                    lambda _: self._on_ai_button_clicked(),
                    colors.accent,  # Sage green accent color
                ),
                # Spacer
                ft.Container(expand=True),
                # Subtle save indicator (Obsidian-style)
                ft.Container(
                    content=ft.Icon(
                        ft.Icons.CIRCLE,
                        size=8,
                        color=colors.text_muted if self._is_dirty else colors.success,
                    ),
                    padding=ft.padding.symmetric(horizontal=SPACING["sm"]),
                    tooltip="Unsaved changes" if self._is_dirty else "Saved",
                ),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACING["xs"],
        )

    def _on_ai_button_clicked(self) -> None:
        """Handle AI button click."""
        if self.on_ai_generate:
            content = self.get_content()
            if content.strip():  # Only generate if there's content
                self.on_ai_generate(content)

    def _on_text_change(self, e: ft.ControlEvent) -> None:
        """Handle text content changes."""
        new_content = e.control.value or ""
        self._content = new_content
        self._is_dirty = new_content != self._last_saved_content

        # Update save indicator
        self._update_save_indicator()

        # Schedule debounced save using threading
        self._schedule_debounced_save(new_content)

        # Notify content change
        if self.on_content_change:
            self.on_content_change(new_content)

        # Update UI

    def _on_content_changed(self) -> None:
        """Helper method to handle content changes without event."""
        self._is_dirty = self._content != self._last_saved_content

        # Update save indicator
        self._update_save_indicator()

        # Schedule debounced save using threading
        self._schedule_debounced_save(self._content)

        # Notify content change
        if self.on_content_change:
            self.on_content_change(self._content)

    def _on_focus(self, _: ft.ControlEvent) -> None:
        """Handle text field focus."""
        # Could add focus-specific behavior here
        pass

    def _on_blur(self, _: ft.ControlEvent) -> None:
        """Handle text field blur."""
        # Trigger immediate save on blur if there are unsaved changes
        if self._is_dirty and self.on_save:
            self.on_save(self._content)
            self._last_saved_content = self._content
            self._is_dirty = False
            self._update_save_indicator()

    def _handle_auto_save(self, content: str) -> None:
        """Handle auto-save callback."""
        if self.on_save:
            self.on_save(content)
            self._last_saved_content = content
            self._is_dirty = False
            self._update_save_indicator()

    def _schedule_debounced_save(self, content: str) -> None:
        """Schedule a debounced save operation."""
        if not self.on_save or content == self._last_saved_content:
            return

        # Use a simple timer-based approach
        if (
            hasattr(self, "_save_timer")
            and self._save_timer
            and self._save_timer.is_alive()
        ):
            self._save_timer.cancel()

        self._save_timer = threading.Timer(
            self.auto_save_delay, self._perform_save, args=[content]
        )
        self._save_timer.start()

    def _perform_save(self, content: str) -> None:
        """Perform the actual save operation."""
        if self.on_save and content != self._last_saved_content:
            self.on_save(content)
            self._last_saved_content = content
            self._is_dirty = False
            # Update indicator in main thread using page update
            if (
                hasattr(self, "text_field")
                and self.text_field
                and hasattr(self.text_field, "page")
                and self.text_field.page
            ):
                self.text_field.page.add(ft.Container())  # Trigger update
                self._update_save_indicator()
                self.text_field.page.update()

    def _update_save_indicator(self) -> None:
        """Update the save status indicator."""
        if not self.toolbar:
            return

        # Find the save indicator container (last control in toolbar)
        save_container = self.toolbar.controls[-1]
        if hasattr(save_container, "content") and hasattr(
            save_container.content, "color"
        ):
            icon_control = save_container.content
            colors = self.theme_manager.colors

            # Show small dot: muted when dirty, green when saved
            if self._is_dirty:
                icon_control.color = colors.text_muted
                save_container.tooltip = "Unsaved changes"
            else:
                icon_control.color = colors.success
                save_container.tooltip = "Saved"

            # Update the control
            try:
                icon_control.update()
                save_container.update()
            except Exception:
                pass  # Ignore update errors

    def _apply_bold(self) -> None:
        """Apply bold formatting."""
        if not self.text_field:
            return

        # Get current text and cursor position
        current_text = self.text_field.value or ""
        cursor_pos = len(current_text)  # Simplified - insert at end

        # Insert bold formatting
        before = current_text[:cursor_pos]
        after = current_text[cursor_pos:]
        new_text = before + "**bold text**" + after

        self.text_field.value = new_text
        self.text_field.update()

        # Trigger change event
        self._content = new_text
        self._on_content_changed()

    def _apply_italic(self) -> None:
        """Apply italic formatting."""
        if not self.text_field:
            return

        # Get current text and cursor position
        current_text = self.text_field.value or ""
        cursor_pos = len(current_text)

        # Insert italic formatting
        before = current_text[:cursor_pos]
        after = current_text[cursor_pos:]
        new_text = before + "*italic text*" + after

        self.text_field.value = new_text
        self.text_field.update()

        # Trigger change event
        self._content = new_text
        self._on_content_changed()

    def _apply_link(self) -> None:
        """Apply link formatting."""
        if not self.text_field:
            return

        # Get current text and cursor position
        current_text = self.text_field.value or ""
        cursor_pos = len(current_text)

        # Insert link formatting
        before = current_text[:cursor_pos]
        after = current_text[cursor_pos:]
        new_text = before + "[link text](url)" + after

        self.text_field.value = new_text
        self.text_field.update()

        # Trigger change event
        self._content = new_text
        self._on_content_changed()

    def _apply_heading(self, level: int) -> None:
        """Apply heading formatting."""
        if not self.text_field:
            return

        # Get current text and cursor position
        current_text = self.text_field.value or ""
        cursor_pos = len(current_text)

        # Insert heading formatting
        heading_prefix = "#" * level + " "
        before = current_text[:cursor_pos]
        after = current_text[cursor_pos:]

        # Add newline before heading if needed
        if before and not before.endswith("\n"):
            heading_text = f"\n{heading_prefix}Heading {level}"
        else:
            heading_text = f"{heading_prefix}Heading {level}"

        new_text = before + heading_text + after

        self.text_field.value = new_text
        self.text_field.update()

        # Trigger change event
        self._content = new_text
        self._on_content_changed()

    # Public methods

    def set_content(self, content: str) -> None:
        """Set the editor content."""
        self._content = content
        self._last_saved_content = content
        self._is_dirty = False

        if (
            self.text_field
            and hasattr(self.text_field, "page")
            and self.text_field.page
        ):
            self.text_field.value = content
            self.text_field.update()

        self._update_save_indicator()

    def get_content(self) -> str:
        """Get the current editor content."""
        return self._content

    def clear(self) -> None:
        """Clear the editor content."""
        self.set_content("")

    def focus(self) -> None:
        """Focus the text editor."""
        if self.text_field:
            self.text_field.focus()

    def save_now(self) -> None:
        """Trigger immediate save."""
        if self.on_save and self._is_dirty:
            self.on_save(self._content)
            self._last_saved_content = self._content
            self._is_dirty = False
            self._update_save_indicator()

    def update_placeholder(self, new_placeholder: str) -> None:
        """Update the placeholder text."""
        self.placeholder_text = new_placeholder
        if (
            self.text_field
            and hasattr(self.text_field, "page")
            and self.text_field.page
        ):
            self.text_field.hint_text = new_placeholder
            self.text_field.update()

    def get_container(self) -> ft.Control:
        """Get the main container for the text editor."""
        return self.container
