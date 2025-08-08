"""
Calendar Component for AI Journal Vault

Interactive calendar view that shows month navigation, entry indicators,
and allows date selection for viewing/creating entries.
"""

import calendar
from datetime import datetime, timedelta
from typing import Set, Callable, Optional
import flet as ft
from ..theme import ThemeManager, ThemedContainer, ThemedText, SPACING, COMPONENT_SIZES


class CalendarComponent:
    """Interactive calendar component with entry indicators and date selection."""
    
    def __init__(
        self, 
        theme_manager: ThemeManager, 
        on_date_selected: Optional[Callable[[datetime], None]] = None,
        entry_dates: Optional[Set[datetime]] = None
    ):
        self.theme_manager = theme_manager
        self.on_date_selected = on_date_selected
        self.entry_dates = entry_dates or set()
        
        # Current calendar state
        self.current_date = datetime.now()
        self.selected_date = datetime.now().date()
        
        # Create main container
        self.container = self._create_calendar_container()
    
    def _create_calendar_container(self) -> ThemedContainer:
        """Create the main calendar container."""
        colors = self.theme_manager.colors
        
        return ThemedContainer(
            self.theme_manager,
            variant="background",
            content=ft.Column(
                controls=[
                    self._create_header(),
                    ft.Container(height=8),  # Reduced spacer
                    self._create_weekday_headers(),
                    self._create_calendar_grid(),
                    ft.Container(height=12),  # Reduced spacer
                    self._create_legend(),
                ],
                spacing=0,
                tight=True
            ),
            padding=ft.padding.all(SPACING["md"])  # Consistent spacing
        )
    
    def _create_header(self) -> ft.Row:
        """Create calendar header with month/year and navigation."""
        colors = self.theme_manager.colors
        
        # Month/Year text - using 3-character month abbreviation like Obsidian
        month_year = ThemedText(
            self.theme_manager,
            self.current_date.strftime("%b %Y"),  # Changed from "%B %Y" to "%b %Y"
            variant="primary",
            size=16,  # Slightly smaller
            weight=ft.FontWeight.W_600
        )
        
        # Navigation buttons
        prev_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_color=colors.text_secondary,
            icon_size=18,  # Smaller icons
            on_click=self._go_previous_month,
            tooltip="Previous month",
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: "transparent",
                    ft.ControlState.HOVERED: colors.hover,
                },
                shape=ft.RoundedRectangleBorder(radius=4)  # Smaller radius
            )
        )
        
        next_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_color=colors.text_secondary,
            icon_size=18,  # Smaller icons
            on_click=self._go_next_month,
            tooltip="Next month",
            style=ft.ButtonStyle(
                bgcolor={
                    ft.ControlState.DEFAULT: "transparent",
                    ft.ControlState.HOVERED: colors.hover,
                },
                shape=ft.RoundedRectangleBorder(radius=4)  # Smaller radius
            )
        )
        
        # Today button
        today_button = ft.TextButton(
            text="Today",
            on_click=self._go_to_today,
            style=ft.ButtonStyle(
                color=colors.primary,
                bgcolor={
                    ft.ControlState.DEFAULT: "transparent",
                    ft.ControlState.HOVERED: colors.hover,
                },
                text_style=ft.TextStyle(size=11, weight=ft.FontWeight.W_500),  # Smaller text
                padding=ft.padding.symmetric(horizontal=8, vertical=4),  # Smaller padding
                shape=ft.RoundedRectangleBorder(radius=4)  # Smaller radius
            )
        )
        
        return ft.Row(
            controls=[
                ft.Row(
                    controls=[prev_button, month_year, next_button],
                    spacing=4,  # Reduced spacing
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                today_button
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _create_weekday_headers(self) -> ft.Row:
        """Create weekday headers."""
        colors = self.theme_manager.colors
        weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        headers = []
        for day in weekdays:
            headers.append(
                ft.Container(
                    content=ThemedText(
                        self.theme_manager,
                        day,
                        variant="muted",
                        size=10,  # Smaller text
                        weight=ft.FontWeight.W_500,
                        text_align=ft.TextAlign.CENTER
                    ),
                    width=32,  # Smaller width
                    height=20,  # Smaller height
                    alignment=ft.alignment.center
                )
            )
        
        return ft.Row(
            controls=headers,
            spacing=2,  # Reduced spacing
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        )
    
    def _create_calendar_grid(self) -> ft.Column:
        """Create the calendar grid with dates."""
        # Get calendar data for current month
        cal = calendar.monthcalendar(self.current_date.year, self.current_date.month)
        
        weeks = []
        for week in cal:
            week_row = self._create_week_row(week)
            weeks.append(week_row)
        
        return ft.Column(
            controls=weeks,
            spacing=1,  # Reduced spacing
            tight=True
        )
    
    def _create_week_row(self, week: list) -> ft.Row:
        """Create a row representing a week."""
        days = []
        
        for day in week:
            day_container = self._create_day_container(day)
            days.append(day_container)
        
        return ft.Row(
            controls=days,
            spacing=1,  # Reduced spacing
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN  # Better alignment
        )
    
    def _create_day_container(self, day: int) -> ft.Container:
        """Create a container for a single day."""
        colors = self.theme_manager.colors
        
        if day == 0:
            # Empty day (previous/next month)
            return ft.Container(width=32, height=28)  # Smaller empty containers
        
        # Create date for this day
        current_date = datetime(self.current_date.year, self.current_date.month, day).date()
        
        # Determine if this day has entries
        has_entry = any(entry_date == current_date for entry_date in self.entry_dates)
        
        # Determine day state
        is_today = current_date == datetime.now().date()
        is_selected = current_date == self.selected_date
        is_current_month = True  # All days in this view are current month
        
        # Set colors based on state
        if is_selected:
            bg_color = colors.primary
            text_color = colors.text_on_primary
            border_color = colors.primary
        elif is_today:
            bg_color = colors.primary + "40"  # Primary with 40% opacity for distinction
            text_color = colors.text_on_primary  # White text for readability
            border_color = colors.primary
        else:
            bg_color = "transparent"
            text_color = colors.text_primary if is_current_month else colors.text_muted
            border_color = "transparent"
        
        # Hover color
        hover_color = colors.hover if not is_selected else colors.primary
        
        # Create day button
        day_button = ft.Container(
            content=ft.Stack(
                controls=[
                    # Day number
                    ft.Container(
                        content=ft.Text(
                            str(day),
                            color=text_color,
                            size=12,  # Smaller text
                            weight=ft.FontWeight.W_500,
                            text_align=ft.TextAlign.CENTER
                        ),
                        alignment=ft.alignment.center,
                        width=32,
                        height=28
                    ),
                    # Entry indicator dot
                    ft.Container(
                        content=ft.Container(
                            width=3,  # Smaller dot
                            height=3,  # Smaller dot
                            border_radius=1.5,
                            bgcolor=colors.accent if not is_selected else colors.text_on_primary,
                        ),
                        alignment=ft.alignment.bottom_center,
                        margin=ft.margin.only(bottom=2),  # Reduced margin
                        width=32,
                        height=28,
                        visible=has_entry
                    )
                ]
            ),
            width=32,  # Smaller width
            height=28,  # Smaller height
            bgcolor=bg_color,
            border=ft.border.all(1, border_color) if border_color != "transparent" else None,
            border_radius=4,  # Smaller radius
            on_click=lambda e, date=current_date: self._select_date(date),
            ink=True,
            animate=ft.Animation(100, ft.AnimationCurve.EASE_OUT),
        )
        
        # Add hover effect
        def on_hover(e, container=day_button):
            if not is_selected:
                container.bgcolor = hover_color if e.data == "true" else bg_color
                container.update()
        
        day_button.on_hover = on_hover
        
        return day_button
    
    def _create_legend(self) -> ft.Row:
        """Create legend showing what the indicators mean."""
        colors = self.theme_manager.colors
        
        return ft.Row(
            controls=[
                # Entry indicator
                ft.Row(
                    controls=[
                        ft.Container(
                            width=4,  # Smaller dot
                            height=4,  # Smaller dot
                            border_radius=2,
                            bgcolor=colors.accent
                        ),
                        ThemedText(
                            self.theme_manager,
                            "Has entry",
                            variant="muted",
                            size=10  # Smaller text
                        )
                    ],
                    spacing=4,  # Reduced spacing
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                ),
                # Today indicator
                ft.Row(
                    controls=[
                        ft.Container(
                            width=4,  # Smaller dot
                            height=4,  # Smaller dot
                            border_radius=2,
                            bgcolor=colors.primary
                        ),
                        ThemedText(
                            self.theme_manager,
                            "Today",
                            variant="muted",
                            size=10  # Smaller text
                        )
                    ],
                    spacing=4,  # Reduced spacing
                    vertical_alignment=ft.CrossAxisAlignment.CENTER
                )
            ],
            spacing=12,  # Reduced spacing
            alignment=ft.MainAxisAlignment.CENTER
        )
    
    def _go_previous_month(self, e) -> None:
        """Navigate to previous month."""
        if self.current_date.month == 1:
            self.current_date = self.current_date.replace(year=self.current_date.year - 1, month=12)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month - 1)
        
        self._refresh_calendar()
    
    def _go_next_month(self, e) -> None:
        """Navigate to next month."""
        if self.current_date.month == 12:
            self.current_date = self.current_date.replace(year=self.current_date.year + 1, month=1)
        else:
            self.current_date = self.current_date.replace(month=self.current_date.month + 1)
        
        self._refresh_calendar()
    
    def _go_to_today(self, e) -> None:
        """Navigate to current month and select today."""
        today = datetime.now()
        self.current_date = today
        self.selected_date = today.date()
        
        self._refresh_calendar()
        
        # Notify date selection
        if self.on_date_selected:
            self.on_date_selected(today)
    
    def _select_date(self, date) -> None:
        """Select a specific date."""
        self.selected_date = date
        self._refresh_calendar()
        
        # Notify date selection
        if self.on_date_selected:
            # Convert date to datetime for consistency
            if isinstance(date, datetime):
                selected_datetime = date
            else:
                selected_datetime = datetime.combine(date, datetime.min.time())
            self.on_date_selected(selected_datetime)
    
    def _refresh_calendar(self) -> None:
        """Refresh the calendar display."""
        # Update header
        self.container.content.controls[0] = self._create_header()
        # Update calendar grid
        self.container.content.controls[3] = self._create_calendar_grid()
        # Update container
        self.container.update()
    
    def update_entry_dates(self, entry_dates: Set[datetime]) -> None:
        """Update the set of dates that have entries."""
        self.entry_dates = entry_dates
        self._refresh_calendar()
    
    def set_selected_date(self, date: datetime) -> None:
        """Set the selected date programmatically."""
        self.selected_date = date.date()
        # Navigate to the month containing this date
        self.current_date = date
        self._refresh_calendar()
    
    def get_container(self) -> ThemedContainer:
        """Get the main calendar container."""
        return self.container


class MiniCalendar(CalendarComponent):
    """Compact version of the calendar for smaller spaces."""
    
    def _create_calendar_container(self) -> ThemedContainer:
        """Create a more compact calendar container."""
        colors = self.theme_manager.colors
        
        return ThemedContainer(
            self.theme_manager,
            variant="surface",
            content=ft.Column(
                controls=[
                    self._create_compact_header(),
                    ft.Container(height=8),  # Reduced spacer
                    self._create_compact_weekday_headers(),
                    self._create_compact_calendar_grid(),
                ],
                spacing=0,
                tight=True
            ),
            padding=ft.padding.all(15),  # Reduced padding
            border=ft.border.all(1, colors.border_subtle),
            border_radius=8
        )
    
    def _create_compact_header(self) -> ft.Row:
        """Create compact calendar header."""
        colors = self.theme_manager.colors
        
        month_year = ThemedText(
            self.theme_manager,
            self.current_date.strftime("%b %Y"),
            variant="primary",
            size=14,
            weight=ft.FontWeight.W_600
        )
        
        prev_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_LEFT,
            icon_color=colors.text_secondary,
            icon_size=16,
            on_click=self._go_previous_month,
            style=ft.ButtonStyle(
                bgcolor={"": "transparent"},
                padding=ft.padding.all(4)
            )
        )
        
        next_button = ft.IconButton(
            icon=ft.Icons.CHEVRON_RIGHT,
            icon_color=colors.text_secondary,
            icon_size=16,
            on_click=self._go_next_month,
            style=ft.ButtonStyle(
                bgcolor={"": "transparent"},
                padding=ft.padding.all(4)
            )
        )
        
        return ft.Row(
            controls=[prev_button, month_year, next_button],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            vertical_alignment=ft.CrossAxisAlignment.CENTER
        )
    
    def _create_compact_weekday_headers(self) -> ft.Row:
        """Create compact weekday headers."""
        weekdays = ['M', 'T', 'W', 'T', 'F', 'S', 'S']
        
        headers = []
        for day in weekdays:
            headers.append(
                ft.Container(
                    content=ThemedText(
                        self.theme_manager,
                        day,
                        variant="muted",
                        size=10,
                        text_align=ft.TextAlign.CENTER
                    ),
                    width=24,
                    height=16,
                    alignment=ft.alignment.center
                )
            )
        
        return ft.Row(
            controls=headers,
            spacing=1,
            alignment=ft.MainAxisAlignment.CENTER
        )
    
    def _create_day_container(self, day: int) -> ft.Container:
        """Create a compact container for a single day."""
        colors = self.theme_manager.colors
        
        if day == 0:
            return ft.Container(width=24, height=24)
        
        current_date = datetime(self.current_date.year, self.current_date.month, day).date()
        has_entry = any(entry_date == current_date for entry_date in self.entry_dates)
        is_today = current_date == datetime.now().date()
        is_selected = current_date == self.selected_date
        
        if is_selected:
            bg_color = colors.primary
            text_color = colors.text_on_primary
        elif is_today:
            bg_color = colors.primary + "40"  # Primary with 40% opacity for distinction
            text_color = colors.text_on_primary  # White text for readability
        else:
            bg_color = "transparent"
            text_color = colors.text_primary
        
        return ft.Container(
            content=ft.Stack(
                controls=[
                    ft.Container(
                        content=ft.Text(
                            str(day),
                            color=text_color,
                            size=11,
                            text_align=ft.TextAlign.CENTER
                        ),
                        alignment=ft.alignment.center,
                        width=24,
                        height=24
                    ),
                    ft.Container(
                        content=ft.Container(
                            width=3,
                            height=3,
                            border_radius=1.5,
                            bgcolor=colors.accent if not is_selected else colors.text_on_primary,
                        ),
                        alignment=ft.alignment.bottom_center,
                        margin=ft.margin.only(bottom=2),
                        width=24,
                        height=24,
                        visible=has_entry
                    )
                ]
            ),
            width=24,
            height=24,
            bgcolor=bg_color,
            border_radius=4,
            on_click=lambda e, date=current_date: self._select_date(date),
            ink=True,
        )