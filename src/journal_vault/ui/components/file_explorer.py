"""
File Explorer Component for AI Journal Vault

A sidebar file browser that integrates with the storage system to show
journal entries organized by date and folder structure.
"""

import os
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Callable, Set
import flet as ft
from ..theme import (
    ThemeManager, ThemedContainer, ThemedText, ThemedCard,
    SPACING, COMPONENT_SIZES, TYPO_SCALE
)
from ...storage import FileManager, JournalEntry


class FileTreeNode:
    """Represents a node in the file tree structure."""
    
    def __init__(self, name: str, path: Path, is_file: bool = False, entry_date: date = None):
        self.name = name
        self.path = path
        self.is_file = is_file
        self.entry_date = entry_date
        self.children: List[FileTreeNode] = []
        self.expanded = False
        self.parent: Optional[FileTreeNode] = None
    
    def add_child(self, child: 'FileTreeNode') -> None:
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
        on_create_entry: Optional[Callable[[date], None]] = None
    ):
        self.theme_manager = theme_manager
        self.file_manager = file_manager
        self.on_file_select = on_file_select
        self.on_create_entry = on_create_entry
        
        # State
        self.file_tree: Optional[FileTreeNode] = None
        self.selected_date: Optional[date] = None
        self.entry_dates: Set[date] = set()
        
        # UI components
        self.tree_view: Optional[ft.Column] = None
        self.search_field: Optional[ft.TextField] = None
        self.search_results: Optional[ft.Column] = None
        self.showing_search = False
        
        # Load initial data
        self._load_entry_dates()
        self._build_file_tree()
        
        # Build the component
        self.container = self._build_component()
    
    def _build_component(self) -> ft.Control:
        """Build the file explorer UI."""
        colors = self.theme_manager.colors
        
        # Search field
        self.search_field = ft.TextField(
            hint_text="Search entries...",
            border=ft.InputBorder.OUTLINE,
            border_color=colors.border_subtle,
            focused_border_color=colors.primary,
            hint_style=ft.TextStyle(color=colors.text_muted, size=TYPO_SCALE["caption"]),
            text_style=ft.TextStyle(color=colors.text_primary, size=TYPO_SCALE["body_sm"]),
            height=36,
            content_padding=ft.padding.symmetric(horizontal=SPACING["sm"], vertical=SPACING["xs"]),
            on_change=self._on_search_change,
            on_submit=self._on_search_submit
        )
        
        # File tree view
        self.tree_view = ft.Column(
            controls=[],
            spacing=SPACING["xs"],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        )
        
        # Search results view
        self.search_results = ft.Column(
            controls=[],
            spacing=SPACING["xs"],
            scroll=ft.ScrollMode.AUTO,
            expand=True,
            visible=False
        )
        
        # Header with title and new entry button
        header = ft.Row(
            controls=[
                ThemedText(
                    self.theme_manager,
                    "Files",
                    variant="primary",
                    typography="body_lg",
                    weight="medium"
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
                        overlay_color=colors.hover
                    )
                ),
                ft.IconButton(
                    icon=ft.Icons.REFRESH,
                    tooltip="Refresh",
                    icon_size=COMPONENT_SIZES["icon_sm"],
                    icon_color=colors.text_muted,
                    on_click=self._on_refresh,
                    style=ft.ButtonStyle(
                        shape=ft.RoundedRectangleBorder(radius=6),
                        overlay_color=colors.hover
                    )
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
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
                        controls=[
                            self.tree_view,
                            self.search_results
                        ],
                        expand=True
                    )
                ],
                spacing=0,
                expand=True
            ),
            padding=SPACING["md"],
            expand=True
        )
    
    def _load_entry_dates(self) -> None:
        """Load all entry dates from the file manager."""
        try:
            self.entry_dates = self.file_manager.get_entry_dates()
        except Exception as e:
            print(f"Error loading entry dates: {e}")
            self.entry_dates = set()
    
    def _build_file_tree(self) -> None:
        """Build the file tree structure from entry dates."""
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
                    str(year),
                    self.file_manager.entries_path / str(year)
                )
                year_nodes[year] = year_node
                self.file_tree.add_child(year_node)
            
            # Create month node if needed
            month_key = (year, month)
            if month_key not in month_nodes:
                month_name = entry_date.strftime("%B")  # Full month name
                month_node = FileTreeNode(
                    f"{month:02d} - {month_name}",
                    self.file_tree.path / str(year) / f"{month:02d}"
                )
                month_nodes[month_key] = month_node
                year_nodes[year].add_child(month_node)
            
            # Create entry node
            entry_name = entry_date.strftime("%d - %A")  # "01 - Monday"
            entry_node = FileTreeNode(
                entry_name,
                self.file_manager._get_entry_file_path(entry_date),
                is_file=True,
                entry_date=entry_date
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
    
    def _update_tree_view(self) -> None:
        """Update the tree view display."""
        if not self.tree_view or not self.file_tree:
            return
        
        self.tree_view.controls.clear()
        self._add_tree_nodes(self.file_tree.children, self.tree_view)
        self.tree_view.update()
    
    def _add_tree_nodes(self, nodes: List[FileTreeNode], container: ft.Column) -> None:
        """Recursively add tree nodes to the container."""
        for node in nodes:
            container.controls.append(self._create_tree_node_control(node))
            
            # Add children if expanded
            if node.expanded and node.children:
                child_container = ft.Column(
                    controls=[],
                    spacing=SPACING["xs"]
                )
                self._add_tree_nodes(node.children, child_container)
                container.controls.append(
                    ft.Container(
                        content=child_container,
                        margin=ft.margin.only(left=SPACING["lg"])
                    )
                )
    
    def _create_tree_node_control(self, node: FileTreeNode) -> ft.Control:
        """Create a control for a tree node."""
        colors = self.theme_manager.colors
        depth = node.get_depth()
        
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
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4))
            )
        else:
            expand_button = ft.Container(width=24)  # Spacer
        
        # Node content
        node_content = ft.Row(
            controls=[
                expand_button,
                ft.Icon(
                    icon,
                    size=COMPONENT_SIZES["icon_sm"],
                    color=icon_color
                ),
                ThemedText(
                    self.theme_manager,
                    node.name,
                    variant="primary" if not node.is_file else "secondary",
                    typography="body_sm",
                    weight="medium" if not node.is_file else "normal"
                )
            ],
            alignment=ft.MainAxisAlignment.START,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=SPACING["xs"]
        )
        
        # Clickable container
        is_selected = (node.is_file and node.entry_date == self.selected_date)
        
        return ft.Container(
            content=node_content,
            padding=ft.padding.symmetric(
                horizontal=SPACING["sm"],
                vertical=SPACING["xs"]
            ),
            border_radius=6,
            bgcolor=colors.surface_variant if is_selected else "transparent",
            on_click=lambda _, n=node: self._on_node_click(n),
            ink=True,
            ink_color=colors.hover
        )
    
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
        
        colors = self.theme_manager.colors
        self.search_results.controls.clear()
        
        if not results:
            # No results message
            self.search_results.controls.append(
                ft.Container(
                    content=ThemedText(
                        self.theme_manager,
                        f"No entries found for '{query}'",
                        variant="muted",
                        typography="body_sm"
                    ),
                    padding=ft.padding.all(SPACING["md"]),
                    alignment=ft.alignment.center
                )
            )
        else:
            # Results header
            self.search_results.controls.append(
                ThemedText(
                    self.theme_manager,
                    f"Found {len(results)} entries for '{query}'",
                    variant="muted",
                    typography="caption"
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
        preview = entry.content[:100] + "..." if len(entry.content) > 100 else entry.content
        
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Row(
                        controls=[
                            ft.Icon(
                                ft.Icons.DESCRIPTION,
                                size=COMPONENT_SIZES["icon_sm"],
                                color=colors.primary
                            ),
                            ft.Column(
                                controls=[
                                    ThemedText(
                                        self.theme_manager,
                                        entry.title,
                                        variant="primary",
                                        typography="body_sm",
                                        weight="medium"
                                    ),
                                    ThemedText(
                                        self.theme_manager,
                                        date_str,
                                        variant="muted",
                                        typography="caption"
                                    )
                                ],
                                spacing=SPACING["xs"],
                                expand=True
                            )
                        ],
                        spacing=SPACING["sm"],
                        vertical_alignment=ft.CrossAxisAlignment.START
                    ),
                    *([ThemedText(
                        self.theme_manager,
                        preview,
                        variant="secondary",
                        typography="caption",
                        max_lines=2
                    )] if preview.strip() else [])
                ],
                spacing=SPACING["xs"]
            ),
            padding=ft.padding.all(SPACING["sm"]),
            border_radius=6,
            bgcolor=colors.surface_variant if entry.date == self.selected_date else "transparent",
            on_click=lambda _, e=entry: self._on_search_result_click(e),
            ink=True,
            ink_color=colors.hover
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
        today = date.today()
        if self.on_create_entry:
            self.on_create_entry(today)
    
    def _on_refresh(self, e: ft.ControlEvent) -> None:
        """Handle refresh request."""
        self.refresh()
    
    # Public methods
    
    def refresh(self) -> None:
        """Refresh the file explorer."""
        self._load_entry_dates()
        self._build_file_tree()
        
        if self.showing_search and self.search_field and self.search_field.value:
            self._perform_search(self.search_field.value)
    
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
    
    def get_container(self) -> ft.Control:
        """Get the main container for the file explorer."""
        return self.container