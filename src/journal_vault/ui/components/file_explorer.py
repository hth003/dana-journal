"""
File Explorer Component for Dana - safe journal space

A sidebar file browser that integrates with the storage system to show
journal entries organized by date and folder structure.
"""

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
import flet as ft
from ..theme import (
    ThemeManager,
    ThemedContainer,
    ThemedText,
    SPACING,
    COMPONENT_SIZES,
    TYPO_SCALE,
)
from ...storage import FileManager, JournalEntry


class FileTreeNode:
    """Represents a node in the file tree structure."""

    def __init__(
        self, name: str, path: Path, is_file: bool = False, entry_date: date = None
    ):
        self.name = name
        self.path = path
        self.is_file = is_file
        self.entry_date = entry_date
        self.children: List[FileTreeNode] = []
        self.expanded = False
        self.parent: Optional[FileTreeNode] = None

    def add_child(self, child: "FileTreeNode") -> None:
        """Add a child node."""
        child.parent = self
        self.children.append(child)

    def get_depth(self) -> int:
        """Get the depth of this node in the tree."""
        depth = 0
        parent = self.parent
        while parent is not None:
            depth += 1
            parent = parent.parent
        return depth


class FileExplorer:
    """File explorer component for browsing journal entries."""

    def __init__(
        self,
        theme_manager: ThemeManager,
        file_manager: FileManager,
        on_file_select: Optional[Callable[[date, JournalEntry], None]] = None,
        on_create_entry: Optional[Callable[[date], None]] = None,
        on_delete_entry: Optional[Callable[[date], None]] = None,
    ):
        self.theme_manager = theme_manager
        self.file_manager = file_manager
        self.on_file_select = on_file_select
        self.on_create_entry = on_create_entry
        self.on_delete_entry = on_delete_entry

        # State
        self.file_tree: Optional[FileTreeNode] = None
        self.selected_date: Optional[date] = None
        self.entry_dates: Set[date] = set()

        # UI components
        self.tree_view: Optional[ft.Column] = None
        self.search_field: Optional[ft.TextField] = None
        self.search_results: Optional[ft.Column] = None
        self.showing_search = False

        # Build the component first
        self.container = self._build_component()

        # Load initial data after UI is built
        self._initialize_data()

    def _build_component(self) -> ft.Control:
        """Build the file explorer UI."""
        colors = self.theme_manager.colors

        # Search field
        self.search_field = ft.TextField(
            hint_text="Search entries...",
            border=ft.InputBorder.OUTLINE,
            border_color=colors.border_subtle,
            focused_border_color=colors.primary,
            hint_style=ft.TextStyle(
                color=colors.text_muted, size=TYPO_SCALE["caption"]
            ),
            text_style=ft.TextStyle(
                color=colors.text_primary, size=TYPO_SCALE["body_sm"]
            ),
            height=36,
            content_padding=ft.padding.symmetric(
                horizontal=SPACING["sm"], vertical=SPACING["xs"]
            ),
            on_change=self._on_search_change,
            on_submit=self._on_search_submit,
        )

        # File tree view
        self.tree_view = ft.Column(
            controls=[], spacing=SPACING["xs"], scroll=ft.ScrollMode.AUTO, expand=True
        )

        # Search results view
        self.search_results = ft.Column(
            controls=[],
            spacing=SPACING["xs"],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            visible=False,
        )

        # Header with title and new entry button
        header = ft.Row(
            controls=[
                ThemedText(
                    self.theme_manager,
                    "Files",
                    variant="primary",
                    typography="body_lg",
                    weight="medium",
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    tooltip="New Entry",
                    icon_size=COMPONENT_SIZES["icon_sm"],
                    icon_color=colors.text_muted,
                    on_click=self._on_new_entry,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        overlay_color=colors.hover,
                    ),
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh",
                    icon_size=COMPONENT_SIZES["icon_sm"],
                    icon_color=colors.text_muted,
                    on_click=self._on_refresh,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        overlay_color=colors.hover,
                    ),
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
        )

        # Main container
        return ThemedContainer(
            self.theme_manager,
            content=ft.Column(
                controls=[
                    header,
                    ft.Container(height=SPACING["sm"]),
                    self.search_field,
                    ft.Container(height=SPACING["sm"]),
                    ft.Stack(
                        controls=[self.tree_view, self.search_results], expand=True
                    ),
                ],
                spacing=0,
                expand=True,
            ),
            padding=SPACING["md"],
            expand=True,
        )

    def _initialize_data(self) -> None:
        """Initialize file explorer data after UI is built."""
        try:
            # First, scan existing files to populate the database
            print("FileExplorer: Scanning existing files...")
            scanned_count = self.file_manager.scan_existing_files()
            print(f"FileExplorer: Scanned {scanned_count} files")

            # Then load entry dates
            self._load_entry_dates()

            # Build the file tree
            self._build_file_tree()

        except Exception as e:
            print(f"Error initializing FileExplorer data: {e}")
            self.entry_dates = set()
            self._build_empty_tree()

    def _load_entry_dates(self) -> None:
        """Load all entry dates from the file manager."""
        try:
            self.entry_dates = self.file_manager.get_entry_dates()
            print(f"FileExplorer: Loaded {len(self.entry_dates)} entry dates")
        except Exception as e:
            print(f"Error loading entry dates: {e}")
            self.entry_dates = set()

    def _build_file_tree(self) -> None:
        """Build the file tree structure from entry dates."""
        if not self.entry_dates:
            print("FileExplorer: No entry dates found, building empty tree")
            self._build_empty_tree()
            return

        print(f"FileExplorer: Building tree with {len(self.entry_dates)} entries")

        # Create root node
        self.file_tree = FileTreeNode("Entries", self.file_manager.entries_path)

        # Group entries by year and month
        year_nodes: Dict[int, FileTreeNode] = {}
        month_nodes: Dict[tuple[int, int], FileTreeNode] = {}

        # Sort dates in descending order (newest first)
        sorted_dates = sorted(self.entry_dates, reverse=True)

        for entry_date in sorted_dates:
            year = entry_date.year
            month = entry_date.month

            # Create year node if needed
            if year not in year_nodes:
                year_node = FileTreeNode(
                    str(year), self.file_manager.entries_path / str(year)
                )
                year_nodes[year] = year_node
                self.file_tree.add_child(year_node)

            # Create month node if needed
            month_key = (year, month)
            if month_key not in month_nodes:
                month_name = entry_date.strftime("%B")  # Full month name
                month_node = FileTreeNode(
                    f"{month:02d} - {month_name}",
                    self.file_tree.path / str(year) / f"{month:02d}",
                )
                month_nodes[month_key] = month_node
                year_nodes[year].add_child(month_node)

            # Create entry node
            entry_name = entry_date.strftime("%d - %a")  # "01 - Mon" (shortened to avoid overflow)
            entry_node = FileTreeNode(
                entry_name,
                self.file_manager._get_entry_file_path(entry_date),
                is_file=True,
                entry_date=entry_date,
            )
            month_nodes[month_key].add_child(entry_node)

        # Expand current month by default
        today = date.today()
        current_year = today.year
        current_month = today.month

        if current_year in year_nodes:
            year_nodes[current_year].expanded = True
            if (current_year, current_month) in month_nodes:
                month_nodes[(current_year, current_month)].expanded = True

        # Update tree view
        self._update_tree_view()
        print(
            f"FileExplorer: Tree built with {len(year_nodes)} years and {len(month_nodes)} months"
        )

    def _build_empty_tree(self) -> None:
        """Build an empty file tree when no entries exist."""
        self.file_tree = FileTreeNode("Entries", self.file_manager.entries_path)
        self._update_tree_view()

    def _update_tree_view(self) -> None:
        """Update the tree view display."""
        if not self.tree_view:
            print("FileExplorer: Tree view not available for update")
            return

        if not self.file_tree:
            print("FileExplorer: No file tree to display")
            return

        print(
            f"FileExplorer: Updating tree view with {len(self.file_tree.children)} top-level nodes"
        )

        self.tree_view.controls.clear()

        if not self.file_tree.children:
            # Show empty state message
            colors = self.theme_manager.colors
            self.tree_view.controls.append(
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Icon(
                                ft.Icons.FOLDER_OPEN_OUTLINED,
                                size=48,
                                color=colors.text_muted,
                            ),
                            ThemedText(
                                self.theme_manager,
                                "No entries found",
                                variant="muted",
                                typography="body_sm",
                            ),
                            ThemedText(
                                self.theme_manager,
                                "Create your first entry to get started",
                                variant="muted",
                                typography="caption",
                            ),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=SPACING["sm"],
                    ),
                    padding=ft.padding.all(SPACING["lg"]),
                    alignment=ft.alignment.center,
                )
            )
        else:
            self._add_tree_nodes(self.file_tree.children, self.tree_view)

        try:
            self.tree_view.update()
            print("FileExplorer: Tree view updated successfully")
        except Exception as e:
            print(f"Error updating tree view: {e}")

    def _add_tree_nodes(self, nodes: List[FileTreeNode], container: ft.Column) -> None:
        """Recursively add tree nodes to the container."""
        for node in nodes:
            container.controls.append(self._create_tree_node_control(node))

            # Add children if expanded
            if node.expanded and node.children:
                child_container = ft.Column(controls=[], spacing=SPACING["xs"])
                self._add_tree_nodes(node.children, child_container)
                container.controls.append(
                    ft.Container(
                        content=child_container,
                        margin=ft.margin.only(left=SPACING["lg"]),
                    )
                )

    def _create_tree_node_control(self, node: FileTreeNode) -> ft.Control:
        """Create a control for a tree node."""
        colors = self.theme_manager.colors
        # depth = node.get_depth()  # Not currently used but may be needed for indentation

        # Determine icon
        if node.is_file:
            icon = ft.Icons.DESCRIPTION
            icon_color = colors.primary
        elif node.expanded:
            icon = ft.Icons.FOLDER_OPEN
            icon_color = colors.warning
        else:
            icon = ft.Icons.FOLDER
            icon_color = colors.text_muted

        # Create expand/collapse button for folders
        expand_button = None
        if not node.is_file and node.children:
            expand_button = ft.IconButton(
                icon=ft.Icons.EXPAND_MORE if node.expanded else ft.Icons.CHEVRON_RIGHT,
                icon_size=COMPONENT_SIZES["icon_xs"],
                icon_color=colors.text_muted,
                on_click=lambda _, n=node: self._toggle_node_expansion(n),
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4)),
            )
        else:
            expand_button = ft.Container(width=24)  # Spacer

        # Removed delete button from file explorer to avoid confusion
        # Delete functionality is available in the main editor area
        delete_button = None
        is_selected = node.is_file and node.entry_date == self.selected_date

        # Node content - clean layout, delete button only for selected entries
        node_content = ft.Row(
            controls=[
                expand_button,
                ft.Icon(icon, size=COMPONENT_SIZES["icon_sm"], color=icon_color),
                ft.Container(
                    content=ThemedText(
                        self.theme_manager,
                        node.name,
                        variant="primary" if not node.is_file else "secondary",
                        typography="body_sm",
                        weight="medium" if not node.is_file else "normal",
                    ),
                    expand=True,
                ),
                delete_button if delete_button else ft.Container(width=0),
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACING["xs"],
        )

        # Clickable container (is_selected already calculated above)

        container = ft.Container(
            content=node_content,
            padding=ft.padding.symmetric(
                horizontal=SPACING["sm"], vertical=SPACING["xs"]
            ),
            border_radius=6,
            bgcolor=colors.surface_variant if is_selected else "transparent",
            on_click=lambda _, n=node: self._on_node_click(n),
            ink=True,
            ink_color=colors.hover,
        )

        # Add right-click context menu for file entries
        if node.is_file:
            container.on_long_press = lambda _, n=node: self._show_context_menu(n)
            # Also support right-click for desktop users (Flet doesn't have native right-click, so we'll use long press)
            # In a real desktop app, you'd implement proper right-click detection

        return container

    def _toggle_node_expansion(self, node: FileTreeNode) -> None:
        """Toggle expansion state of a folder node."""
        node.expanded = not node.expanded
        self._update_tree_view()

    def _on_node_click(self, node: FileTreeNode) -> None:
        """Handle node click."""
        if node.is_file and node.entry_date:
            # Load and select the entry
            self.selected_date = node.entry_date
            entry = self.file_manager.load_entry(node.entry_date)

            if entry and self.on_file_select:
                self.on_file_select(node.entry_date, entry)

            # Update tree view to show selection
            self._update_tree_view()
        else:
            # Toggle folder expansion
            self._toggle_node_expansion(node)

    def _on_search_change(self, e: ft.ControlEvent) -> None:
        """Handle search input changes."""
        query = e.control.value.strip()

        if not query:
            self._show_tree_view()
            return

        # Debounce search (simple implementation)
        # In a real app, you'd want proper debouncing
        if len(query) >= 2:
            self._perform_search(query)

    def _on_search_submit(self, e: ft.ControlEvent) -> None:
        """Handle search submission."""
        query = e.control.value.strip()
        if query:
            self._perform_search(query)

    def _perform_search(self, query: str) -> None:
        """Perform search and show results."""
        try:
            # Search entries using file manager
            search_results = self.file_manager.search_entries(query, limit=20)

            # Update search results view
            self._update_search_results(search_results, query)
            self._show_search_results()

        except Exception as e:
            print(f"Error performing search: {e}")

    def _update_search_results(self, results: List[JournalEntry], query: str) -> None:
        """Update the search results display."""
        if not self.search_results:
            return

        # colors = self.theme_manager.colors  # Colors available from theme_manager if needed
        self.search_results.controls.clear()

        if not results:
            # No results message
            self.search_results.controls.append(
                ft.Container(
                    content=ThemedText(
                        self.theme_manager,
                        f"No entries found for '{query}'",
                        variant="muted",
                        typography="body_sm",
                    ),
                    padding=ft.padding.all(SPACING["md"]),
                    alignment=ft.alignment.center,
                )
            )
        else:
            # Results header
            self.search_results.controls.append(
                ThemedText(
                    self.theme_manager,
                    f"Found {len(results)} entries for '{query}'",
                    variant="muted",
                    typography="caption",
                )
            )

            # Add result items
            for entry in results:
                result_item = self._create_search_result_item(entry, query)
                self.search_results.controls.append(result_item)

        self.search_results.update()

    def _create_search_result_item(self, entry: JournalEntry, query: str) -> ft.Control:
        """Create a search result item."""
        colors = self.theme_manager.colors

        # Format date
        date_str = entry.date.strftime("%B %d, %Y")

        # Create preview text (first 100 chars)
        preview = (
            entry.content[:100] + "..." if len(entry.content) > 100 else entry.content
        )
        _ = query  # Keep query parameter for potential highlighting in future

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.DESCRIPTION,
                                size=COMPONENT_SIZES["icon_sm"],
                                color=colors.primary,
                            ),
                            ft.Column(
                                controls=[
                                    ThemedText(
                                        self.theme_manager,
                                        entry.title,
                                        variant="primary",
                                        typography="body_sm",
                                        weight="medium",
                                    ),
                                    ThemedText(
                                        self.theme_manager,
                                        date_str,
                                        variant="muted",
                                        typography="caption",
                                    ),
                                ],
                                spacing=SPACING["xs"],
                                expand=True,
                            ),
                        ],
                        spacing=SPACING["sm"],
                        vertical_alignment=ft.CrossAxisAlignment.START,
                    ),
                    *(
                        [
                            ThemedText(
                                self.theme_manager,
                                preview,
                                variant="secondary",
                                typography="caption",
                                max_lines=2,
                            )
                        ]
                        if preview.strip()
                        else []
                    ),
                ],
                spacing=SPACING["xs"],
            ),
            padding=ft.padding.all(SPACING["sm"]),
            border_radius=6,
            bgcolor=(
                colors.surface_variant
                if entry.date == self.selected_date
                else "transparent"
            ),
            on_click=lambda _, e=entry: self._on_search_result_click(e),
            ink=True,
            ink_color=colors.hover,
        )

    def _on_search_result_click(self, entry: JournalEntry) -> None:
        """Handle search result click."""
        self.selected_date = entry.date

        if self.on_file_select:
            self.on_file_select(entry.date, entry)

        # Clear search and return to tree view
        if self.search_field:
            self.search_field.value = ""
            self.search_field.update()

        self._show_tree_view()

        # Update tree view to show selection
        self._update_tree_view()

    def _show_tree_view(self) -> None:
        """Show the tree view and hide search results."""
        if self.tree_view and self.search_results:
            self.tree_view.visible = True
            self.search_results.visible = False
            self.showing_search = False
            self.tree_view.update()
            self.search_results.update()

    def _show_search_results(self) -> None:
        """Show the search results and hide tree view."""
        if self.tree_view and self.search_results:
            self.tree_view.visible = False
            self.search_results.visible = True
            self.showing_search = True
            self.tree_view.update()
            self.search_results.update()

    def _on_new_entry(self, e: ft.ControlEvent) -> None:
        """Handle new entry creation."""
        _ = e  # Parameter required by Flet event signature
        today = date.today()
        if self.on_create_entry:
            self.on_create_entry(today)

    def _on_refresh(self, e: ft.ControlEvent) -> None:
        """Handle refresh request."""
        _ = e  # Parameter required by Flet event signature
        self.refresh()

    # Public methods

    def refresh(self) -> None:
        """Refresh the file explorer."""
        print("FileExplorer: Refreshing...")
        self._initialize_data()

        if self.showing_search and self.search_field and self.search_field.value:
            self._perform_search(self.search_field.value)

    def update_entry_dates(self, entry_dates: Set[date]) -> None:
        """Update entry dates and refresh the file tree."""
        self.entry_dates = entry_dates
        self._build_file_tree()
        self._update_tree_view()

    def select_date(self, selected_date: date) -> None:
        """Select a specific date in the file explorer."""
        self.selected_date = selected_date

        # Expand the path to the selected date
        if selected_date in self.entry_dates:
            self._expand_path_to_date(selected_date)

        self._update_tree_view()

    def _expand_path_to_date(self, target_date: date) -> None:
        """Expand the tree path to show the given date."""
        if not self.file_tree:
            return

        # Find and expand year node
        year = target_date.year
        year_node = None
        for node in self.file_tree.children:
            if node.name == str(year):
                year_node = node
                node.expanded = True
                break

        if not year_node:
            return

        # Find and expand month node
        month = target_date.month
        month_name = target_date.strftime("%B")
        month_display = f"{month:02d} - {month_name}"

        for node in year_node.children:
            if node.name == month_display:
                node.expanded = True
                break

    def get_selected_date(self) -> Optional[date]:
        """Get the currently selected date."""
        return self.selected_date

    def has_entry(self, check_date: date) -> bool:
        """Check if an entry exists for the given date."""
        return check_date in self.entry_dates

    def select_entry_by_date(self, entry_date: date) -> None:
        """Select an entry by date."""
        self.selected_date = entry_date
        self._update_tree_view()

    def _show_context_menu(self, node: FileTreeNode) -> None:
        """Show context menu for file entry."""
        if not node.is_file or not node.entry_date:
            return

        colors = self.theme_manager.colors
        entry_title = node.entry_date.strftime("%B %d, %Y")

        # Context menu options
        def on_delete_selected(e):
            """Handle delete option from context menu."""
            _ = e
            context_menu.open = False
            self.container.page.update()
            self._confirm_delete_entry(node)

        def on_open_selected(e):
            """Handle open option from context menu."""
            _ = e
            context_menu.open = False
            self.container.page.update()
            self._on_node_click(node)

        def on_dismiss(e):
            """Handle context menu dismissal."""
            _ = e
            context_menu.open = False
            self.container.page.update()

        # Create context menu as dialog
        context_menu = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                f"Entry: {entry_title}",
                color=colors.text_primary,
                size=16,
                weight=ft.FontWeight.W_500,
            ),
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.OPEN_IN_NEW, size=20, color=colors.primary
                                ),
                                ft.Container(width=8),
                                ft.Text(
                                    "Open Entry", color=colors.text_primary, size=14
                                ),
                            ]
                        ),
                        padding=ft.padding.all(8),
                        border_radius=4,
                        ink=True,
                        on_click=on_open_selected,
                    ),
                    ft.Container(
                        content=ft.Row(
                            controls=[
                                ft.Icon(
                                    ft.Icons.DELETE_OUTLINE, size=20, color=colors.error
                                ),
                                ft.Container(width=8),
                                ft.Text("Delete Entry", color=colors.error, size=14),
                            ]
                        ),
                        padding=ft.padding.all(8),
                        border_radius=4,
                        ink=True,
                        on_click=on_delete_selected,
                    ),
                ],
                tight=True,
                spacing=4,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=on_dismiss,
                    style=ft.ButtonStyle(
                        color=colors.text_muted, overlay_color=colors.hover
                    ),
                )
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors.surface,
            title_text_style=ft.TextStyle(color=colors.text_primary),
            content_padding=ft.padding.all(12),
        )

        # Show context menu
        try:
            page = self._get_page()
            if page:
                page.dialog = context_menu
                context_menu.open = True
                page.update()
            else:
                print("FileExplorer: Could not access page for context menu")
        except Exception as e:
            print(f"Error showing context menu: {e}")

    def _confirm_delete_entry(self, node: FileTreeNode) -> None:
        """Show delete confirmation dialog."""
        if not node.is_file or not node.entry_date:
            print("_confirm_delete_entry: Invalid node or no entry date")
            return

        print(f"_confirm_delete_entry: Creating dialog for {node.entry_date}")

        colors = self.theme_manager.colors
        entry_title = node.entry_date.strftime("%B %d, %Y")

        def on_confirm(e):
            """Handle delete confirmation."""
            _ = e
            dialog.open = False
            page = self._get_page()
            if page:
                page.update()

            # Call the delete callback if available
            if self.on_delete_entry:
                self.on_delete_entry(node.entry_date)
            else:
                # Fallback: delete directly if no callback
                try:
                    if self.file_manager.delete_entry(node.entry_date):
                        # Remove from entry dates and refresh
                        self.entry_dates.discard(node.entry_date)
                        self._build_file_tree()
                        print(f"Deleted entry for {node.entry_date}")
                    else:
                        print(f"Failed to delete entry for {node.entry_date}")
                except Exception as ex:
                    print(f"Error deleting entry: {ex}")

        def on_cancel(e):
            """Handle delete cancellation."""
            _ = e
            dialog.open = False
            page = self._get_page()
            if page:
                page.update()

        # Create confirmation dialog
        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(
                "Delete Entry",
                color=colors.text_primary,
                size=18,
                weight=ft.FontWeight.W_500,
            ),
            content=ft.Text(
                f"Delete entry for {entry_title}?\nThis action cannot be undone.",
                color=colors.text_secondary,
                size=14,
            ),
            actions=[
                ft.TextButton(
                    "Cancel",
                    on_click=on_cancel,
                    style=ft.ButtonStyle(
                        color=colors.text_muted, overlay_color=colors.hover
                    ),
                ),
                ft.TextButton(
                    "Delete",
                    on_click=on_confirm,
                    style=ft.ButtonStyle(
                        color=colors.error, overlay_color=colors.error_subtle
                    ),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            bgcolor=colors.surface,
            title_text_style=ft.TextStyle(color=colors.text_primary),
            content_text_style=ft.TextStyle(color=colors.text_secondary),
        )

        # Show dialog
        try:
            page = self._get_page()
            if page:
                page.dialog = dialog
                dialog.open = True
                page.update()
            else:
                print("FileExplorer: Could not access page for delete confirmation")
        except Exception as e:
            print(f"Error showing delete confirmation: {e}")

    def _get_page(self) -> ft.Page:
        """Get the page reference, handling potential access issues."""
        try:
            # Try to get page from container
            if hasattr(self.container, "page") and self.container.page:
                return self.container.page

            # Try to get page from tree_view
            if hasattr(self.tree_view, "page") and self.tree_view.page:
                return self.tree_view.page

            # Try to access via any control that might have page reference
            for control in [
                self.container,
                self.tree_view,
                self.search_field,
                self.search_results,
            ]:
                if control and hasattr(control, "page") and control.page:
                    return control.page

            print("FileExplorer: Could not find page reference")
            return None

        except Exception as e:
            print(f"Error getting page reference: {e}")
            return None

    def get_container(self) -> ft.Control:
        """Get the main container for the file explorer."""
        return self.container

    def _on_delete_entry_click(self, e: ft.ControlEvent, node: FileTreeNode) -> None:
        """Handle delete button click with event stopping."""
        _ = e  # Parameter required by Flet event signature
        # Stop event from propagating to parent container by handling it immediately
        print(f"Delete button clicked for entry: {node.entry_date}")
        self._on_delete_entry(node)

    def _on_delete_entry(self, node: FileTreeNode) -> None:
        """Handle delete entry request - kept for backward compatibility."""
        self._confirm_delete_entry(node)
