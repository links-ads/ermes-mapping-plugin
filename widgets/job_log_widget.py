# -*- coding: utf-8 -*-
"""
Job Log Widget - Custom widget for displaying job status with expandable logs
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QHBoxLayout, QTextEdit
)
from PyQt5.QtCore import Qt


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
    """Main widget for displaying all job logs with expandable boxes"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.message_boxes = {}  # job_id -> ExpandableJobBox
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Set minimum height for the widget
        self.setMinimumHeight(300)
        
        # Create scroll area for the job boxes
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Container widget for job boxes
        self.container = QWidget()
        self.container_layout = QVBoxLayout()
        self.container_layout.setContentsMargins(5, 5, 5, 5)
        #self.container_layout.setSpacing(5)
        self.container_layout.addStretch()
        
        self.container.setLayout(self.container_layout)
        scroll_area.setWidget(self.container)
        
        layout.addWidget(scroll_area)
    
    def _get_or_create_box(self, box_type="warning"):
        """Get or create a message box"""
 
        if box_type not in self.message_boxes:
            if box_type == "error":
                color = "#FF746C"
                prefix = "❌"
                title = "Errors"
                is_expanded = True
            elif box_type == "warning":
                color = "#FFEE8C"
                prefix = "⚠️"
                title = "Warnings"
                is_expanded = True
            else:
                # Job box
                color = "#F5F5F5"
                prefix = "📋"
                title = f"Job {box_type}"
                is_expanded = False
            
            self.message_boxes[box_type] = BaseMessageBox(
                title=title, 
                color=color, 
                prefix=prefix,
                is_expanded=is_expanded
            )
            self.message_boxes[box_type].close_button.clicked.connect(
                lambda bt=box_type: self.remove_box(bt)
            )
            
            # Insert at the appropriate position
            insert_pos = 0
            # Errors at top
            if box_type == "error":
                insert_pos = 0
            # Warnings after errors
            elif box_type == "warning":
                if "error" in self.message_boxes:
                    insert_pos = 1
                else:
                    insert_pos = 0
            # Jobs after warnings and errors
            else:
                for key in ["error", "warning"]:
                    if key in self.message_boxes:
                        insert_pos += 1
            
            self.container_layout.insertWidget(insert_pos, self.message_boxes[box_type])
            
        return self.message_boxes[box_type]
    
    def remove_box(self, box_type="warning"):
        """Remove a specific box"""
        if box_type in self.message_boxes:
            self.container_layout.removeWidget(self.message_boxes[box_type])
            self.message_boxes[box_type].deleteLater()
            del self.message_boxes[box_type]
    
    def add_message(self, box_type, message, level="warning"):
        """Add a message to a specific box"""
        box = self._get_or_create_box(box_type)
        box.add_message(message, level)
    
    def update_status(self, box_type, status_text, color="black"):
        """Update the status of a specific box"""
        if box_type in self.message_boxes:
            self.message_boxes[box_type].update_status(status_text, color)
    
    def expand_box(self, box_type):
        """Expand a specific box"""
        if box_type in self.message_boxes and not self.message_boxes[box_type].is_expanded:
            self.message_boxes[box_type].toggle_expand()
    
    def collapse_box(self, box_type):
        """Collapse a specific box""" 
        if box_type in self.message_boxes and self.message_boxes[box_type].is_expanded:
            self.message_boxes[box_type].toggle_expand()
    
    def clear_box(self, box_type):
        """Clear logs for a specific box"""
        if box_type in self.message_boxes:
            self.container_layout.removeWidget(self.message_boxes[box_type])
            self.message_boxes[box_type].deleteLater()
            del self.message_boxes[box_type]
    
    def clear_all_logs(self):
        """Clear all boxes"""
        for box_type in list(self.message_boxes.keys()):
            self.clear_box(box_type)

