# -*- coding: utf-8 -*-
"""
Job Log Widget - Compact job status rows with tick-on-message progress and full logs in dialog
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QFrame, QHBoxLayout,
    QProgressBar, QPlainTextEdit, QDialog, QDialogButtonBox, QTextEdit,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFontMetrics


# Progress band while running: reserve 100 for terminal state.
_PROGRESS_STEP = 7
_PROGRESS_MIN = 10
_PROGRESS_MAX_RUNNING = 95
_PROGRESS_WRAP = 30


class JobRowWidget(QFrame):
    """Compact single row per job: title, last message, status pill, progress bar, + and X buttons."""

    def __init__(self, box_type, title, parent=None):
        super().__init__(parent)
        self.box_type = box_type
        self.title_text = title
        self.messages = []  # list of (message, level) for full log dialog
        self._progress_value = _PROGRESS_MIN
        self._expected_messages = None
        self._completed_messages = 0
        self._finished = False  # once True, progress stays at 100
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setSpacing(2)
        self.setMinimumHeight(44)

        row = QHBoxLayout()
        row.setSpacing(6)

        self.title_label = QLabel(self.title_text)
        self.title_label.setStyleSheet("font-weight: bold; font-size: 11px; color: black;")
        self.title_label.setMinimumWidth(120)
        row.addWidget(self.title_label)

        self.last_message_label = QLabel("")
        self.last_message_label.setStyleSheet("font-size: 10px; color: #333;")
        self.last_message_label.setMinimumWidth(80)
        self.last_message_label.setSizePolicy(
            self.last_message_label.sizePolicy().horizontalPolicy(),
            self.last_message_label.sizePolicy().verticalPolicy(),
        )
        row.addWidget(self.last_message_label, 1)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet(
            "font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 3px;"
        )
        self.status_label.setMinimumWidth(52)
        row.addWidget(self.status_label)

        self.logs_button = QPushButton("+")
        self.logs_button.setToolTip("Show full logs")
        self.logs_button.setStyleSheet("""
            QPushButton { border: none; background: transparent; font-size: 14px; min-width: 22px; max-width: 22px; }
            QPushButton:hover { background: #E0E0E0; border-radius: 3px; }
        """)
        self.logs_button.clicked.connect(self.open_logs_dialog)
        row.addWidget(self.logs_button)

        self.close_button = QPushButton("\u2715")
        self.close_button.setToolTip("Remove this job row")
        self.close_button.setStyleSheet("""
            QPushButton { border: none; background: transparent; font-size: 14px; min-width: 22px; max-width: 22px; }
            QPushButton:hover { color: #D32F2F; }
        """)
        row.addWidget(self.close_button)

        layout.addLayout(row)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(self._progress_value)
        self.progress_bar.setMinimumHeight(6)
        self.progress_bar.setMaximumHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 1px solid #CCC; border-radius: 2px; text-align: center; }
            QProgressBar::chunk { background: #2196F3; }
        """)
        layout.addWidget(self.progress_bar)

        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("JobRowWidget, QFrame { background-color: #F5F5F5; border: 1px solid #DDD; border-radius: 3px; }")

    def add_message(self, message, level="info", display_message=None):
        if (message, level) in self.messages:
            return
        self.messages.append((message, level))
        text_for_preview = (display_message if display_message is not None else message)
        formatted = f"[{level.upper()}] {text_for_preview}"
        self.last_message_label.setText(self._elide(formatted))
        self.last_message_label.setToolTip(f"[{level.upper()}] {message}")
        if not self._finished and self._expected_messages is None:
            self._progress_value = min(_PROGRESS_MAX_RUNNING, self._progress_value + _PROGRESS_STEP)
            if self._progress_value >= _PROGRESS_MAX_RUNNING:
                self._progress_value = _PROGRESS_WRAP
            self.progress_bar.setValue(self._progress_value)

    def set_expected_messages(self, total):
        """Enable proportional progress mode for this row."""
        if total is None:
            return
        try:
            total = int(total)
        except (TypeError, ValueError):
            return
        if total <= 0:
            return
        self._expected_messages = total
        if self._completed_messages > self._expected_messages:
            self._completed_messages = self._expected_messages
        self._update_progress_from_counts()

    def mark_completed_message(self, increment=1):
        """Mark completed workload unit(s) for proportional progress mode."""
        if self._expected_messages is None:
            return
        if self._finished:
            return
        try:
            increment = int(increment)
        except (TypeError, ValueError):
            increment = 1
        if increment <= 0:
            return
        self._completed_messages = min(
            self._expected_messages, self._completed_messages + increment
        )
        self._update_progress_from_counts()

    def set_completed_messages(self, count):
        """Set absolute completed workload for proportional mode."""
        if self._expected_messages is None:
            return
        try:
            count = int(count)
        except (TypeError, ValueError):
            return
        if count < 0:
            count = 0
        self._completed_messages = min(self._expected_messages, count)
        self._update_progress_from_counts()

    def _update_progress_from_counts(self):
        if self._finished or self._expected_messages is None:
            return
        ratio = min(1.0, self._completed_messages / float(self._expected_messages))
        running_span = _PROGRESS_MAX_RUNNING - _PROGRESS_MIN
        self._progress_value = _PROGRESS_MIN + int(running_span * ratio)
        self.progress_bar.setValue(self._progress_value)

    def _elide(self, text, width=None):
        if width is None:
            width = self.last_message_label.width() if self.last_message_label.width() > 20 else 200
        return QFontMetrics(self.last_message_label.font()).elidedText(
            text, Qt.ElideRight, max(20, width)
        )

    def set_status(self, status_text, color="black"):
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(
            f"font-size: 9px; font-weight: bold; padding: 2px 6px; border-radius: 3px; color: {color};"
        )
        if status_text.upper() in ("SUCCESS", "ERROR"):
            self._finished = True
            self.progress_bar.setValue(100)
            if status_text.upper() == "SUCCESS":
                self.progress_bar.setStyleSheet("""
                    QProgressBar { border: 1px solid #CCC; border-radius: 2px; }
                    QProgressBar::chunk { background: #4CAF50; }
                """)
            else:
                self.progress_bar.setStyleSheet("""
                    QProgressBar { border: 1px solid #CCC; border-radius: 2px; }
                    QProgressBar::chunk { background: #F44336; }
                """)

    def open_logs_dialog(self):
        d = QDialog(self.window())
        d.setWindowTitle(f"Logs — {self.title_text}")
        layout = QVBoxLayout(d)
        te = QPlainTextEdit()
        te.setReadOnly(True)
        te.setStyleSheet("font-family: monospace; font-size: 11px;")
        full_text = "\n".join(f"[{lev.upper()}] {msg}" for msg, lev in self.messages)
        te.setPlainText(full_text or "(no messages)")
        layout.addWidget(te)
        bb = QDialogButtonBox(QDialogButtonBox.Ok)
        bb.accepted.connect(d.accept)
        layout.addWidget(bb)
        d.exec_()


class BaseMessageBox(QWidget):
    """Base class for all message boxes"""
    
    def __init__(self, title, color, prefix, parent=None, is_expanded=True):
        super().__init__(parent)
        self.title = title
        self.color = color
        self.is_expanded = is_expanded
        self.prefix = prefix
        self.messages = []
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI components"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Header frame with title and expand/collapse button
        header_frame = QFrame()
        header_frame.setFrameShape(QFrame.Box)
        header_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {self.color};
                border: 2px solid #CCCCCC;;
                border-radius: 4px;
                padding: 5px;
            }}
        """)
        
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(5, 5, 5, 5)
        
        # Expand/Collapse button
        self.expand_button = QPushButton()
        self.expand_button.setText("▼")
        self.expand_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: black;
                font-size: 12px;
                min-width: 20px;
                max-width: 20px;
            }
        """)

        self.expand_button.clicked.connect(self.toggle_expand)
        header_layout.addWidget(self.expand_button)
        
        # Title label
        self.title_label = QLabel(f"{self.prefix} {self.title}")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 12px; color: black; border: none;")
        header_layout.addWidget(self.title_label)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: black; font-size: 10px; border: none;")
        header_layout.addWidget(self.status_label)

        header_layout.addStretch()

        # Message count
        self.message_count_label = QLabel("0 messages")
        self.message_count_label.setStyleSheet("color: black; font-size: 10px;")
        header_layout.addWidget(self.message_count_label)

        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setStyleSheet("""
            QPushButton {
                border: none;
                background-color: transparent;
                color: black;
                font-size: 16px;
                font-weight: bold;
                min-width: 20px;
                max-width: 20px;
            }
            QPushButton:hover {
                color: #D32F2F;
            }
        """)
        self.close_button.setToolTip("Remove this message box")
        header_layout.addWidget(self.close_button)

        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)

        # Content area (initially visible)
        self.content_frame = QFrame()
        self.content_frame.setFrameShape(QFrame.StyledPanel)
        self.content_frame.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #CCCCCC;
                border-top: none;
            }
        """)

        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        
        # Text area for messages
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setMinimumHeight(100)
        self.message_text.setMaximumHeight(200)
        self.message_text.setStyleSheet("""
            QTextEdit {
                border: 1px solid #DDDDDD;
                border-radius: 3px;
                background-color: #FAFAFA;
                font-family: 'Courier New', monospace;
                font-size: 14px;
            }
        """)
        content_layout.addWidget(self.message_text)

        self.content_frame.setLayout(content_layout)
        self.content_frame.setVisible(True)
        layout.addWidget(self.content_frame)
        
        layout.addStretch()
    
    def toggle_expand(self):
        """Toggle the expanded state"""
        self.is_expanded = not self.is_expanded
        self.content_frame.setVisible(self.is_expanded)
        
        if self.is_expanded:
            self.expand_button.setText("▼")
        else:
            self.expand_button.setText("▲")
    
    def add_message(self, message, level="info"):
        """Add a message to this box (avoids duplicates)"""
        # Check if this exact message already exists
        if (message, level) in self.messages:
            return  # Skip duplicate message
        
        self.messages.append((message, level))
        
        # Update message count
        count = len(self.messages)
        self.message_count_label.setText(f"{count} message{'s' if count != 1 else ''}")
        
        # Update the text area
        formatted_message = f"[{level.upper()}] {message}"
        self.message_text.append(formatted_message)
        
    def update_status(self, status_text, color="black"):
        """Update the status label"""
        self.status_label.setText(status_text)
        self.status_label.setStyleSheet(f"color: {color}; font-size: 10px;")
    
    def get_most_recent_status(self):
        """Get the most recent message status"""
        if self.messages:
            return self.messages[-1]
        return None, "info"


class JobLogWidget(QWidget):
    """Compact job rows (tick-on-message progress) and legacy warning/error boxes; no nested scroll."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.message_boxes = {}  # box_type -> BaseMessageBox or JobRowWidget
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)
        self.setMinimumHeight(140)
        self.setStyleSheet("QWidget { background-color: #FAFAFA; border: 1px solid #E0E0E0; border-radius: 3px; }")
        self.container_layout = layout
        # Placeholder so the log area is visible when empty (avoids collapsing to zero height)
        self.placeholder = QLabel("Job logs will appear here when you run a request.")
        self.placeholder.setStyleSheet("color: #666; font-size: 10px; padding: 8px;")
        self.placeholder.setAlignment(Qt.AlignCenter)
        self.placeholder.setMinimumHeight(80)
        self.container_layout.addWidget(self.placeholder)
        self.container_layout.addStretch()

    def _get_or_create_box(self, box_type="warning", pipeline=None):
        if box_type not in self.message_boxes:
            if box_type == "error":
                color = "#FF746C"
                prefix = "\u2716"
                title = "Errors"
                is_expanded = True
                self.message_boxes[box_type] = BaseMessageBox(
                    title=title, color=color, prefix=prefix, is_expanded=is_expanded
                )
                self.message_boxes[box_type].close_button.clicked.connect(
                    lambda checked, bt=box_type: self.remove_box(bt)
                )
            elif box_type == "warning":
                color = "#FFEE8C"
                prefix = "\u26a0"
                title = "Warnings"
                is_expanded = True
                self.message_boxes[box_type] = BaseMessageBox(
                    title=title, color=color, prefix=prefix, is_expanded=is_expanded
                )
                self.message_boxes[box_type].close_button.clicked.connect(
                    lambda checked, bt=box_type: self.remove_box(bt)
                )
            else:
                title = f"Job {box_type} - {pipeline}" if pipeline else f"Job {box_type}"
                self.message_boxes[box_type] = JobRowWidget(box_type, title)
                self.message_boxes[box_type].close_button.clicked.connect(
                    lambda checked, bt=box_type: self.remove_box(bt)
                )

            insert_pos = 0
            if box_type == "error":
                insert_pos = 0
            elif box_type == "warning":
                insert_pos = 1 if "error" in self.message_boxes else 0
            else:
                insert_pos = sum(1 for k in ["error", "warning"] if k in self.message_boxes)
            self.container_layout.insertWidget(insert_pos, self.message_boxes[box_type])
            self.placeholder.setVisible(False)
        return self.message_boxes[box_type]

    def remove_box(self, box_type="warning"):
        if box_type in self.message_boxes:
            self.container_layout.removeWidget(self.message_boxes[box_type])
            self.message_boxes[box_type].deleteLater()
            del self.message_boxes[box_type]
            if not self.message_boxes:
                self.placeholder.setVisible(True)

    def add_message(self, box_type, message, level="warning", pipeline=None, display_message=None):
        box = self._get_or_create_box(box_type, pipeline=pipeline)
        if isinstance(box, JobRowWidget):
            box.add_message(message, level, display_message=display_message)
        else:
            box.add_message(message, level)

    def set_expected_messages(self, box_type, total):
        box = self._get_or_create_box(box_type)
        if isinstance(box, JobRowWidget):
            box.set_expected_messages(total)

    def mark_completed_message(self, box_type, increment=1):
        if box_type not in self.message_boxes:
            return
        box = self.message_boxes[box_type]
        if isinstance(box, JobRowWidget):
            box.mark_completed_message(increment)

    def set_completed_messages(self, box_type, count):
        if box_type not in self.message_boxes:
            return
        box = self.message_boxes[box_type]
        if isinstance(box, JobRowWidget):
            box.set_completed_messages(count)

    def update_status(self, box_type, status_text, color="black"):
        if box_type not in self.message_boxes:
            return
        w = self.message_boxes[box_type]
        if isinstance(w, JobRowWidget):
            w.set_status(status_text, color)
        else:
            w.update_status(status_text, color)

    def expand_box(self, box_type):
        if box_type in self.message_boxes and hasattr(self.message_boxes[box_type], "toggle_expand"):
            w = self.message_boxes[box_type]
            if not w.is_expanded:
                w.toggle_expand()

    def collapse_box(self, box_type):
        if box_type in self.message_boxes and hasattr(self.message_boxes[box_type], "toggle_expand"):
            w = self.message_boxes[box_type]
            if w.is_expanded:
                w.toggle_expand()

    def clear_box(self, box_type):
        if box_type in self.message_boxes:
            self.container_layout.removeWidget(self.message_boxes[box_type])
            self.message_boxes[box_type].deleteLater()
            del self.message_boxes[box_type]
            if not self.message_boxes:
                self.placeholder.setVisible(True)

    def clear_all_logs(self):
        for box_type in list(self.message_boxes.keys()):
            self.clear_box(box_type)

