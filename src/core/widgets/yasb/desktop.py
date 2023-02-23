import logging
import psutil
from humanize import naturalsize
from core.widgets.base import BaseWidget
from core.validation.widgets.yasb.desktop import VALIDATION_SCHEMA
from PyQt6.QtWidgets import QLabel
from pyvda import AppView, get_apps_by_z_order, VirtualDesktop, get_virtual_desktops
 

class DesktopWidget(BaseWidget):
    validation_schema = VALIDATION_SCHEMA

    def __init__(
            self,
            label: str,
            label_alt: str,
            update_interval: int,
            callbacks: dict[str, str],
            memory_thresholds: dict[str, int]
    ):
        super().__init__(update_interval, class_name="desktop-widget")
        self._memory_thresholds = memory_thresholds

        self._show_alt_label = False
        self._label_content = label
        self._label_alt_content = label_alt

        self._label = QLabel()
        self._label_alt = QLabel()
        self._label.setProperty("class", "label")
        self._label_alt.setProperty("class", "label alt")
        self.widget_layout.addWidget(self._label)
        self.widget_layout.addWidget(self._label_alt)

        self.register_callback("toggle_label", self._toggle_label)
        self.register_callback("update_label", self._update_label)

        self.callback_left = callbacks['on_left']
        self.callback_right = callbacks['on_right']
        self.callback_middle = callbacks['on_middle']
        self.callback_timer = "update_label"

        self._label.show()
        self._label_alt.hide()
        self.start_timer()

    def _toggle_label(self):
        self._show_alt_label = not self._show_alt_label

        if self._show_alt_label:
            self._label.hide()
            self._label_alt.show()
        else:
            self._label.show()
            self._label_alt.hide()

        self._update_label()

    def _update_label(self):
        active_label = self._label_alt if self._show_alt_label else self._label
        active_label_content = self._label_alt_content if self._show_alt_label else self._label_content
        active_label_formatted = active_label_content

        try:
            current_desktop = VirtualDesktop.current()
            
            label_options = [
                ("{current_desktop}", current_desktop.number),
            ]

            for fmt_str, value in label_options:
                active_label_formatted = active_label_formatted.replace(fmt_str, str(value))

            alt_class = "alt" if self._show_alt_label else ""
            active_label.setText(active_label_formatted)
            active_label.setStyleSheet('')
        except Exception:
            active_label.setText(active_label_content)
            logging.exception("Failed to retrieve updated memory info")

    def _get_virtual_memory_threshold(self, virtual_memory_percent) -> str:
        if virtual_memory_percent <= self._memory_thresholds['low']:
            return "low"
        elif self._memory_thresholds['low'] < virtual_memory_percent <= self._memory_thresholds['medium']:
            return "medium"
        elif self._memory_thresholds['medium'] < virtual_memory_percent <= self._memory_thresholds['high']:
            return "high"
        elif self._memory_thresholds['high'] < virtual_memory_percent:
            return "critical"
