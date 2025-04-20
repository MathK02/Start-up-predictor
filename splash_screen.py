from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
import time

class SplashScreen(QSplashScreen):
    def __init__(self):
        # Create a basic pixmap
        pixmap = QPixmap(400, 200)
        pixmap.fill(Qt.white)
        super().__init__(pixmap)
        
        # Create layout widget
        layout_widget = QWidget(self)
        layout = QVBoxLayout(layout_widget)
        
        # Add title
        title = QLabel("Aleph One")
        title.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
                color: #2c3e50;
            }
        """)
        title.setAlignment(Qt.AlignCenter)
        
        # Add loading text
        self.loading_label = QLabel("Loading...")
        self.loading_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #34495e;
            }
        """)
        self.loading_label.setAlignment(Qt.AlignCenter)
        
        # Add progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
            }
            QProgressBar::chunk {
                background-color: #3498db;
            }
        """)
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        
        # Add widgets to layout
        layout.addWidget(title)
        layout.addWidget(self.loading_label)
        layout.addWidget(self.progress_bar)
        
        # Center the layout widget
        layout_widget.setGeometry(0, 0, 400, 200)
        
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.loading_label.setText(message) 