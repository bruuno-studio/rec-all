import sys
import os
from datetime import datetime
from typing import List, Dict, Optional

import easyocr
import torch
from PIL import ImageGrab
import numpy as np
import cv2
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                            QHBoxLayout, QPushButton, QLabel, QLineEdit,
                            QFileDialog, QScrollArea, QFrame, QDialog, QSlider,
                            QCheckBox, QProgressBar, QSystemTrayIcon, QMenu, QTabWidget, QTextEdit,
                            QLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer, QSize, QPropertyAnimation, QEvent, QEasingCurve, QPoint, QRect, pyqtProperty, QRectF
from PyQt6.QtGui import QPixmap, QPainter, QColor, QPen, QPainterPath, QIcon, QAction
from pathlib import Path
from PyQt6.QtWidgets import QGraphicsOpacityEffect
from PyQt6.QtWidgets import QScroller, QScrollerProperties

try:
    from image_description import ImageDescriptionGenerator
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

def initialize_reader():
    try:
        # Initialize with core languages first
        core_languages = ['en', 'tr']  # Start with English as the base
        
        # Try to add additional languages one by one
        additional_languages = ['fr', 'es', 'de', 'it', 'pt', 'nl']
        supported_languages = ['en', 'tr']  # Start with English
        
        for lang in additional_languages:
            try:
                # Test each language individually
                test_reader = easyocr.Reader([lang])
                supported_languages.append(lang)
            except Exception as lang_error:
                print(f"Language {lang} not supported: {lang_error}")
        
        # Initialize reader with all supported languages
        reader = easyocr.Reader(supported_languages)
        print(f"EasyOCR initialized with languages: {supported_languages}")
        return reader
        
    except Exception as e:
        print(f"Error initializing EasyOCR: {e}")
        # Fallback to English-only if there's an error
        try:
            reader = easyocr.Reader(['en'])
            print("Fallback to English-only OCR")
            return reader
        except Exception as fallback_error:
            print(f"Critical error initializing OCR: {fallback_error}")
            return None

def get_relative_time(timestamp: datetime) -> str:
    return timestamp.strftime('%B %d %A %Y (%H:%M)')

def load_app_icon() -> QIcon:
    """Load the application icon from the ICO file"""
    icon_path = Path(__file__).parent / "icon.ico"
    if icon_path.exists():
        return QIcon(str(icon_path))
    return QIcon()  # Return empty icon if file doesn't exist

class ProcessingIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(200, 100)
        self.angle = 0
        self.status_text = "Processing..."
        self.dots_count = 0
        self.dots_timer = QTimer()
        self.dots_timer.timeout.connect(self.update_dots)
        self.dots_timer.start(500)
        
        # Animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.rotate)
        self.animation_timer.start(50)
        
        self.progress = 0

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Save current state
        painter.save()
        
        # Draw rotating circle
        painter.translate(100, 40)
        painter.rotate(self.angle)
        
        path = QPainterPath()
        path.addEllipse(-15, -15, 30, 30)
        
        pen = QPen(QColor("#1208ff"), 3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.drawPath(path)
        
        # Restore state before drawing text and progress bar
        painter.restore()
        
        # Draw progress bar
        if self.progress > 0:
            bar_width = 160
            bar_height = 4
            x = (self.width() - bar_width) // 2
            y = 65
            
            # Draw background bar
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#333"))
            painter.drawRoundedRect(x, y, bar_width, bar_height, 2, 2)
            
            # Draw progress
            progress_width = int(bar_width * (self.progress / 100))
            if progress_width > 0:
                painter.setBrush(QColor("#1208ff"))
                painter.drawRoundedRect(x, y, progress_width, bar_height, 2, 2)
        
        # Draw status text
        painter.setPen(QColor("#1208ff"))
        dots = "." * self.dots_count
        status_text = f"{self.status_text}{dots}"
        if self.progress > 0:
            status_text += f" ({self.progress}%)"
        painter.drawText(0, 80, self.width(), 20, 
                        Qt.AlignmentFlag.AlignCenter,
                        status_text)

    def rotate(self):
        self.angle = (self.angle + 10) % 360
        self.update()

    def update_dots(self):
        self.dots_count = (self.dots_count + 1) % 4
        self.update()

    def start_animation(self):
        self.show()
        self.animation_timer.start()
        self.dots_timer.start()

    def stop_animation(self):
        self.animation_timer.stop()
        self.dots_timer.stop()
        self.hide()

    def set_progress(self, value):
        self.progress = value
        self.update()

class RecordingStatus(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #333333;
                border-radius: 5px;
                padding: 10px;
                margin: 0px 20px;
            }
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        
        self.record_indicator = BlinkingDot()
        layout.addWidget(self.record_indicator)
        
        text = QLabel("Recording...")
        text.setStyleSheet("color: white; font-size: 14px; font-weight: bold;")
        layout.addWidget(text)
        
        self.features_label = QLabel()
        self.features_label.setStyleSheet("color: #888; font-size: 12px;")
        layout.addWidget(self.features_label)
        
        layout.addStretch()
    
    def start_recording(self, ocr_enabled=False, ai_enabled=False):
        features = []
        if ocr_enabled:
            features.append("OCR")
        if ai_enabled:
            features.append("AI")
        
        if features:
            self.features_label.setText(f"Features enabled: {', '.join(features)}")
        else:
            self.features_label.setText("Basic screen capture")
            
        self.record_indicator.start_blinking()
    
    def stop_recording(self):
        self.record_indicator.stop_blinking()

class BlinkingDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(12, 12)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.toggle_opacity)
        self.is_visible = True
        
    def toggle_opacity(self):
        self.is_visible = not self.is_visible
        self.update()
        
    def start_blinking(self):
        self.timer.start(500)
        
    def stop_blinking(self):
        self.timer.stop()
        self.is_visible = True
        self.update()
        
    def paintEvent(self, event):
        if self.is_visible:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor("#FF0000"))
            painter.drawEllipse(0, 0, self.width(), self.height())

class ProcessingThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    
    def __init__(self, capture_thread):
        super().__init__()
        self.capture_thread = capture_thread
        self.describer = None
        
    def run(self):
        if not AI_AVAILABLE or not self.capture_thread.description_queue:
            self.finished.emit()
            return
            
        try:
            if self.describer is None:
                self.describer = ImageDescriptionGenerator()
            
            total = len(self.capture_thread.description_queue)
            for i, (img_path, desc_path) in enumerate(self.capture_thread.description_queue):
                try:
                    if os.path.exists(img_path):
                        description = self.describer.generate_description(img_path)
                        with open(desc_path, 'w', encoding='utf-8') as f:
                            f.write(description)
                except Exception as e:
                    print(f"Error processing image {img_path}: {e}")
                
                self.progress.emit(int((i + 1) / total * 100))
            
        except Exception as e:
            print(f"Processing thread error: {e}")
        finally:
            self.describer = None
            self.capture_thread.description_queue.clear()
            self.finished.emit()

class ScreenCapture(QThread):
    capture_complete = pyqtSignal(str, str, str)
    initialized = pyqtSignal()  # New signal for initialization complete
    
    def __init__(self, save_path, interval=5.0, use_ocr=False, use_ai=False):
        super().__init__()
        self.save_path = save_path
        self.interval = interval
        self.use_ocr = use_ocr
        self.use_ai = use_ai
        self.running = True
        self.ocr_reader = None
        self.description_queue = []

    def run(self):
        # Initialize OCR if needed
        if self.use_ocr:
            self.ocr_reader = initialize_reader()
            if not self.ocr_reader:
                print("Failed to initialize OCR")
                return
        
        # Signal that initialization is complete
        self.initialized.emit()
        
        self.running = True
        while self.running:
            try:
                timestamp = datetime.now()
                date_str = timestamp.strftime('%Y-%m-%d')
                time_str = timestamp.strftime('%H%M%S')
                
                # Ensure directories exist
                save_dir = os.path.join(self.save_path, date_str)
                img_dir = os.path.join(save_dir, "images")
                text_dir = os.path.join(save_dir, "texts")
                os.makedirs(img_dir, exist_ok=True)
                os.makedirs(text_dir, exist_ok=True)
                
                # Capture screen using PIL and convert to numpy array
                try:
                    screenshot = ImageGrab.grab()
                    img = np.array(screenshot)
                    # Convert RGB to BGR for OpenCV
                    img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
                    
                    # Save image with error handling
                    img_path = os.path.join(img_dir, f"screenshot_{time_str}.jpg")
                    success = cv2.imwrite(img_path, img)
                    
                    if not success:
                        print(f"Failed to save image to {img_path}")
                        continue
                    
                    text_content = ""
                    if self.use_ocr and self.ocr_reader:
                        try:
                            results = self.ocr_reader.readtext(img)
                            text_blocks = []
                            for detection in results:
                                bbox, text, conf = detection
                                if conf > 0.2:
                                    top_left = bbox[0]
                                    x, y = int(top_left[0]), int(top_left[1])
                                    text_blocks.append({
                                        'text': text,
                                        'position': (x, y),
                                        'confidence': conf
                                    })
                            
                            text_blocks.sort(key=lambda x: x['position'][1])
                            formatted_text = []
                            for block in text_blocks:
                                formatted_text.append(f"{block['text']} (Confidence: {block['confidence']:.2f})")
                            
                            text_content = "\n".join(formatted_text)
                            
                            # Save OCR results
                            text_path = os.path.join(text_dir, f"text_{time_str}.txt")
                            with open(text_path, 'w', encoding='utf-8') as f:
                                f.write(text_content)
                                
                        except Exception as e:
                            print(f"OCR Error: {e}")
                            text_content = f"OCR Error: {str(e)}"
                    
                    # Handle AI description
                    desc_path = None
                    if self.use_ai:
                        desc_path = os.path.join(text_dir, f"description_{time_str}.txt")
                        self.description_queue.append((img_path, desc_path))
                    
                    self.capture_complete.emit(img_path, text_content or '', '')
                    
                except Exception as e:
                    print(f"Screenshot capture/save error: {e}")
                
                # Sleep for interval
                self.msleep(int(self.interval * 1000))
                
            except Exception as e:
                print(f"Main capture loop error: {e}")

    def stop(self):
        self.running = False
        
    def generate_description(self, image_path: str) -> str:
        if not AI_AVAILABLE:
            return "AI description not available."
        
        if self.ocr_reader is None:
            self.ocr_reader = initialize_reader()
        
        return self.ocr_reader.generate_description(image_path)
        
    def process_remaining_descriptions(self):
        if not self.description_queue or not AI_AVAILABLE:
            return
            
        try:
            if self.ocr_reader is None:
                self.ocr_reader = initialize_reader()
                
            
            for img_path, desc_path in self.description_queue:
                if os.path.exists(img_path) and not os.path.exists(desc_path):
                    description = self.ocr_reader.generate_description(img_path)
                    with open(desc_path, 'w', encoding='utf-8') as f:
                        f.write(description)
                    
            
            self.description_queue.clear()
            
            
        except Exception as e:
            print(f"Error processing remaining descriptions: {e}")
        finally:
            self.ocr_reader = None

class ResultCard(QFrame):
    def __init__(self, metadata: Dict, index: int, on_click, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.index = index
        self.on_click = on_click
        self.pixmap = None
        self.thumbnail_size = QSize(320, 180)
        
        self.setFixedSize(320, 260)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Pre-load thumbnail
        QTimer.singleShot(0, self.load_thumbnail)
        
        # Setup UI elements
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Image container
        self.image_container = QWidget()
        self.image_container.setFixedSize(self.thumbnail_size)
        layout.addWidget(self.image_container, 0, Qt.AlignmentFlag.AlignCenter)
        
        # Info container
        info_container = QWidget()
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(10, 5, 10, 10)
        info_layout.setSpacing(2)
        
        # Timestamp
        timestamp_text = get_relative_time(self.metadata['timestamp'])
        timestamp = QLabel(timestamp_text)
        timestamp.setStyleSheet("color: #666; font-size: 12px;")
        info_layout.addWidget(timestamp)
        
        # Features indicators
        features_layout = QHBoxLayout()
        features_layout.setSpacing(5)
        
        if self.metadata.get('text_content'):
            ocr_indicator = QLabel("OCR")
            ocr_indicator.setStyleSheet("""
                QLabel {
                    color: #1208ff;
                    font-size: 10px;
                    padding: 2px 6px;
                    background: rgba(18, 8, 255, 0.1);
                    border-radius: 4px;
                }
            """)
            features_layout.addWidget(ocr_indicator)
        
        if self.metadata.get('description_content'):
            ai_indicator = QLabel("AI")
            ai_indicator.setStyleSheet("""
                QLabel {
                    color: #1208ff;
                    font-size: 10px;
                    padding: 2px 6px;
                    background: rgba(18, 8, 255, 0.1);
                    border-radius: 4px;
                }
            """)
            features_layout.addWidget(ai_indicator)
            
        features_layout.addStretch()
        info_layout.addLayout(features_layout)
        
        layout.addWidget(info_container)
        
        # Make card clickable
        self.mousePressEvent = lambda e: self.on_click(self.index)
        
        # Style
        self.setStyleSheet("""
            ResultCard {
                background: #252525;
                border-radius: 8px;
            }
            ResultCard:hover {
                background: #2a2a2a;
            }
        """)

    def load_thumbnail(self):
        if not hasattr(self, 'metadata'):
            return
            
        pixmap = QPixmap(self.metadata['image_path'])
        if not pixmap.isNull():
            self.pixmap = pixmap.scaled(
                self.thumbnail_size,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        if self.pixmap:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Calculate center position for the image
            x = (self.width() - self.pixmap.width()) // 2
            painter.drawPixmap(x, 10, self.pixmap)

class ImagePreview(QDialog):
    def __init__(self, metadata_list: List[Dict], current_index: int, filtered_indices: Optional[List[int]] = None):
        super().__init__()
        self.setWindowTitle("Image Preview")
        self.setMinimumSize(1400, 900)
        
        self.metadata_list = metadata_list
        # Store both filtered and all indices
        self.filtered_indices = filtered_indices if filtered_indices is not None else list(range(len(metadata_list)))
        self.all_indices = list(range(len(metadata_list)))
        
        # Set current index to the actual position in full list
        self.current_actual_index = current_index
        
        # Set window to be frameless and modern
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.setup_ui()
        self.update_display()
        
        # Add these variables for window dragging
        self.dragging = False
        self.drag_position = None

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Main container
        container = QFrame(self)
        container.setStyleSheet("""
            QFrame {
                background: #1a1a1a;
                border-radius: 12px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(15)
        
        # Top bar
        top_bar = QFrame()
        top_bar.setStyleSheet("background: transparent;")
        top_bar.setFixedHeight(50)
        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(20, 0, 20, 0)
        
        # Title
        self.title_label = QLabel("Image Preview")
        self.title_label.setStyleSheet("color: #fff; font-size: 15px;")
        
        # Navigation buttons with minimal design
        nav_widget = QWidget()
        nav_layout = QHBoxLayout(nav_widget)
        nav_layout.setContentsMargins(0, 0, 0, 0)
        nav_layout.setSpacing(8)
        
        self.prev_btn = QPushButton("←")
        self.next_btn = QPushButton("→")
        for btn in [self.prev_btn, self.next_btn]:
            btn.setFixedSize(32, 32)
            btn.setStyleSheet("""
                QPushButton {
                    background: #252525;
                    border-radius: 16px;
                    color: #1208ff;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background: #1208ff;
                    color: white;
                }
                QPushButton:disabled {
                    background: #222;
                    color: #333;
                }
            """)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.next_btn)
        
        # Close button
        close_btn = QPushButton("×")
        close_btn.setFixedSize(32, 32)
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet("""
            QPushButton {
                background: #252525;
                border-radius: 16px;
                color: #888;
                font-size: 20px;
            }
            QPushButton:hover {
                background: #2a2a2a;
                color: #ff4444;
            }
        """)
        
        top_bar_layout.addWidget(self.title_label)
        top_bar_layout.addStretch()
        top_bar_layout.addWidget(nav_widget)
        top_bar_layout.addWidget(close_btn)
        
        # Content area
        content = QHBoxLayout()
        content.setContentsMargins(15, 0, 15, 0)
        content.setSpacing(15)
        
        # Image viewer
        image_container = QFrame()
        image_container.setStyleSheet("""
            QFrame {
                background: #222;
                border-radius: 8px;
            }
        """)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setStyleSheet("background: transparent;")
        image_layout.addWidget(self.image_label)
        
        # Information panel
        info_container = QFrame()
        info_container.setFixedWidth(350)
        info_container.setStyleSheet("""
            QFrame {
                background: #222;
                border-radius: 8px;
            }
        """)
        
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(15, 15, 15, 15)
        info_layout.setSpacing(10)
        
        # Timestamp
        self.timestamp_label = QLabel()
        self.timestamp_label.setStyleSheet("color: #666; font-size: 13px;")
        info_layout.addWidget(self.timestamp_label)
        
        # Minimal tabs
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: #252525;
                border-radius: 6px;
            }
            QTabBar::tab {
                background: transparent;
                color: #666;
                padding: 8px 16px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                color: #1208ff;
            }
            QTabBar::tab:hover:!selected {
                color: #888;
            }
        """)
        
        # OCR Text Tab with minimal design
        ocr_widget = QWidget()
        ocr_layout = QVBoxLayout(ocr_widget)
        self.ocr_content = QTextEdit()
        self.ocr_content.setReadOnly(True)
        self.ocr_content.setStyleSheet("""
            QTextEdit {
                background: #252525;
                color: #fff;
                border: none;
                border-radius: 6px;
                padding: 12px;
                selection-background-color: #1208ff;
                selection-color: #fff;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 6px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #333;
                border-radius: 3px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background: #1208ff;
            }
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        ocr_layout.addWidget(self.ocr_content)
        
        # AI Description Tab
        ai_widget = QWidget()
        ai_layout = QVBoxLayout(ai_widget)
        self.ai_content = QTextEdit()
        self.ai_content.setReadOnly(True)
        self.ai_content.setStyleSheet(self.ocr_content.styleSheet())
        ai_layout.addWidget(self.ai_content)
        
        tabs.addTab(ocr_widget, "OCR Text")
        tabs.addTab(ai_widget, "AI Description")
        info_layout.addWidget(tabs)
        
        content.addWidget(image_container, stretch=2)
        content.addWidget(info_container)
        
        # Minimal bottom bar with slider
        bottom_bar = QFrame()
        bottom_bar.setStyleSheet("background: transparent;")
        bottom_bar.setFixedHeight(50)
        bottom_layout = QVBoxLayout(bottom_bar)
        bottom_layout.setContentsMargins(20, 0, 20, 0)
        
        # Minimal slider design
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMaximum(len(self.metadata_list) - 1)
        self.slider.setValue(self.current_actual_index)
        self.slider.setStyleSheet("""
            QSlider {
                height: 20px;
                background: transparent;
            }
            QSlider::groove:horizontal {
                height: 2px;
                background: #333;
            }
            QSlider::handle:horizontal {
                background: #1208ff;
                width: 10px;
                height: 10px;
                margin: -4px 0;
                border-radius: 5px;
            }
            QSlider::handle:horizontal:hover {
                background: #2318ff;
            }
            QSlider::sub-page:horizontal {
                height: 2px;
                background: #1208ff;
            }
        """)
        
        # Minimal counter label
        self.counter_label = QLabel()
        self.counter_label.setStyleSheet("""
            QLabel {
                color: #1208ff;
                font-size: 12px;
            }
        """)
        self.counter_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        bottom_layout.addWidget(self.slider)
        bottom_layout.addWidget(self.counter_label)
        
        # Add all components
        container_layout.addWidget(top_bar)
        container_layout.addLayout(content)
        container_layout.addWidget(bottom_bar)
        
        main_layout.addWidget(container)
        
        # Connect slider and navigation buttons
        self.slider.valueChanged.connect(self.set_index)
        self.prev_btn.clicked.connect(self.show_previous)
        self.next_btn.clicked.connect(self.show_next)

    def update_display(self):
        metadata = self.metadata_list[self.current_actual_index]
        
        # Update image
        pixmap = QPixmap(metadata['image_path'])
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(
                self.width() - 450,
                self.height() - 120,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.image_label.setPixmap(scaled_pixmap)
        
        # Update text content (OCR without confidence scores)
        self.timestamp_label.setText(get_relative_time(metadata['timestamp']))
        
        # Clean OCR text (remove confidence scores)
        ocr_text = metadata.get('text_content', 'No OCR text available')
        cleaned_ocr = '\n'.join([
            line.split('(Confidence:')[0].strip()
            for line in ocr_text.split('\n')
            if line.strip()
        ])
        self.ocr_content.setText(cleaned_ocr)
        
        self.ai_content.setText(metadata.get('description_content', 'No AI description available'))
        
        # Update counter to show position in filtered list if applicable
        if self.current_actual_index in self.filtered_indices:
            filtered_position = self.filtered_indices.index(self.current_actual_index) + 1
            total_filtered = len(self.filtered_indices)
            counter_text = f"{filtered_position}/{total_filtered}"
            if len(self.filtered_indices) != len(self.metadata_list):
                counter_text += f" (Filtered from {len(self.metadata_list)})"
        else:
            # If current image isn't in filtered results, show absolute position
            counter_text = f"{self.current_actual_index + 1}/{len(self.metadata_list)}"
        
        self.counter_label.setText(counter_text)
        
        # Update navigation buttons
        if self.current_actual_index in self.filtered_indices:
            current_filtered_index = self.filtered_indices.index(self.current_actual_index)
            self.prev_btn.setEnabled(current_filtered_index > 0)
            self.next_btn.setEnabled(current_filtered_index < len(self.filtered_indices) - 1)
        else:
            # If not in filtered list, use full list navigation
            self.prev_btn.setEnabled(self.current_actual_index > 0)
            self.next_btn.setEnabled(self.current_actual_index < len(self.metadata_list) - 1)
        
        # Update title
        self.title_label.setText(os.path.basename(metadata['image_path']))

    def set_index(self, index: int):
        """Handle slider value changes"""
        if index != self.current_actual_index:
            self.current_actual_index = index
            self.update_display()

    def show_previous(self):
        if self.current_actual_index in self.filtered_indices:
            current_filtered_index = self.filtered_indices.index(self.current_actual_index)
            if current_filtered_index > 0:
                new_index = self.filtered_indices[current_filtered_index - 1]
                self.slider.setValue(new_index)
        else:
            if self.current_actual_index > 0:
                self.slider.setValue(self.current_actual_index - 1)

    def show_next(self):
        if self.current_actual_index in self.filtered_indices:
            current_filtered_index = self.filtered_indices.index(self.current_actual_index)
            if current_filtered_index < len(self.filtered_indices) - 1:
                new_index = self.filtered_indices[current_filtered_index + 1]
                self.slider.setValue(new_index)
        else:
            if self.current_actual_index < len(self.metadata_list) - 1:
                self.slider.setValue(self.current_actual_index + 1)

    def keyPressEvent(self, event):
        """Handle keyboard navigation"""
        if event.key() == Qt.Key.Key_Left:
            self.show_previous()
        elif event.key() == Qt.Key.Key_Right:
            self.show_next()
        elif event.key() == Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press events for window dragging"""
        if event.button() == Qt.MouseButton.LeftButton:
            # Only start drag if clicking on the top bar area
            if event.position().y() < 50:  # Height of top bar
                self.dragging = True
                self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
                event.accept()

    def mouseReleaseEvent(self, event):
        """Handle mouse release events"""
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = False
            event.accept()

    def mouseMoveEvent(self, event):
        """Handle mouse move events for window dragging"""
        if self.dragging and event.buttons() & Qt.MouseButton.LeftButton:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

class SmoothScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_smooth_scroll()
        
    def setup_smooth_scroll(self):
        # Enable smooth scrolling using QScroller
        scroller = QScroller.scroller(self.viewport())
        scroller.grabGesture(self.viewport(), QScroller.ScrollerGestureType.TouchGesture)
        
        # Configure scrolling properties
        scroll_props = QScrollerProperties()
        
        # Use the correct enum values for Qt6
        scroll_props.setScrollMetric(QScrollerProperties.ScrollMetric.VerticalOvershootPolicy, 1)
        scroll_props.setScrollMetric(QScrollerProperties.ScrollMetric.DecelerationFactor, 0.1)
        scroll_props.setScrollMetric(QScrollerProperties.ScrollMetric.MaximumVelocity, 0.6)
        scroll_props.setScrollMetric(QScrollerProperties.ScrollMetric.AcceleratingFlickMaximumTime, 0.4)
        scroll_props.setScrollMetric(QScrollerProperties.ScrollMetric.DragStartDistance, 0.001)
        
        scroller.setScrollerProperties(scroll_props)
    
    def wheelEvent(self, event):
        # Calculate pixels to scroll
        num_pixels = event.angleDelta().y()
        
        # Current position
        current_pos = self.verticalScrollBar().value()
        target_pos = current_pos - num_pixels
        
        # Create smooth animation
        self.scroll_animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        self.scroll_animation.setDuration(150)
        self.scroll_animation.setStartValue(current_pos)
        self.scroll_animation.setEndValue(target_pos)
        self.scroll_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.scroll_animation.start()
        
        event.accept()

class PulsingButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        # Property to store current pulse state
        self._pulse = 0.0  # Initialize _pulse here, at the start
        
        self.setStyleSheet("""
            QPushButton {
                background: #1208ff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2318ff;
            }
        """)
        
        # Setup color animation
        self.animation = QPropertyAnimation(self, b"pulse_color", self)
        self.animation.setDuration(1000)  # 1 second for one pulse
        self.animation.setLoopCount(-1)   # Infinite loop
        self.animation.setStartValue(0.0)
        self.animation.setEndValue(1.0)
        
        # Start pulsing
        self.animation.start()
        
    def get_pulse_color(self):
        return self._pulse
        
    def set_pulse_color(self, value):
        self._pulse = value
        # Interpolate between normal and lighter color
        color = QColor("#1208ff")
        light_color = QColor("#4538ff")
        interpolated_color = QColor(
            int(color.red() + (light_color.red() - color.red()) * value),
            int(color.green() + (light_color.green() - color.green()) * value),
            int(color.blue() + (light_color.blue() - color.blue()) * value)
        )
        self.setStyleSheet(f"""
            QPushButton {{
                background: {interpolated_color.name()};
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background: #2318ff;
            }}
        """)
        
    pulse_color = pyqtProperty(float, get_pulse_color, set_pulse_color)
    
    def stop_pulse(self):
        self.animation.stop()
        self.setStyleSheet("""
            QPushButton {
                background: #1208ff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2318ff;
            }
        """)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("rec-all")
        self.setMinimumSize(1200, 800)
        
        # Initialize opacity effect but don't set it yet
        self._opacity = 1.0  # Start fully visible
        self.opacity_effect = None
        
        self.save_path = None
        self.capture_thread = None
        self.processing_thread = None
        self.metadata_list = []
        self.filtered_indices = []
        self.is_processing = False
        
        # Set application icon
        app_icon = load_app_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)
        
        # Initialize system tray
        self.setup_system_tray()
        
        self.setup_ui()
        self.apply_styles()

    def prepare_fade_in(self):
        """Setup fade in effect just before showing"""
        if self.opacity_effect is None:
            self.opacity_effect = QGraphicsOpacityEffect(self)
            self.setGraphicsEffect(self.opacity_effect)
            self.opacity_effect.setOpacity(0)
            
            # Create fade-in animation
            self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
            self.fade_in.setDuration(500)
            self.fade_in.setStartValue(0.0)
            self.fade_in.setEndValue(1.0)
            self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)

    def showEvent(self, event):
        super().showEvent(event)
        # Start fade in animation
        if hasattr(self, 'fade_in'):
            self.fade_in.start()

    def setup_system_tray(self):
        """Initialize system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        
        # Use the app icon for the tray
        app_icon = load_app_icon()
        if not app_icon.isNull():
            self.tray_icon.setIcon(app_icon)
        
        # Create tray menu
        self.tray_menu = QMenu()
        self.tray_menu.setStyleSheet("""
            QMenu {
                background-color: #333;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                color: #fff;
                padding: 5px 20px;
                border-radius: 3px;
            }
            QMenu::item:selected {
                background-color: #1208ff;
            }
            QMenu::item:disabled {
                color: #666;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 5px 0px;
            }
        """)
        
        # Add menu actions
        show_action = self.tray_menu.addAction("Show")
        show_action.triggered.connect(self.show_from_tray)
        
        # Add recording status action (disabled by default)
        self.recording_action = self.tray_menu.addAction("Not Recording")
        self.recording_action.setEnabled(False)
        
        self.tray_menu.addSeparator()
        
        quit_action = self.tray_menu.addAction("Quit")
        quit_action.triggered.connect(self.quit_application)
        
        # Set the menu for the tray icon
        self.tray_icon.setContextMenu(self.tray_menu)
        
        # Handle tray icon clicks
        self.tray_icon.activated.connect(self.tray_icon_activated)
        
        # Show the tray icon
        self.tray_icon.show()
        
        # Set tooltip
        self.tray_icon.setToolTip("rec-all")

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_from_tray()

    def show_from_tray(self):
        """Show window from tray"""
        self.showNormal()
        self.activateWindow()

    def quit_application(self):
        """Properly quit the application"""
        # Stop any running processes
        if self.capture_thread and self.capture_thread.isRunning():
            self.stop_capture()
            self.capture_thread.wait()
        
        if self.processing_thread and self.processing_thread.isRunning():
            self.processing_thread.wait()
        
        # Remove tray icon
        self.tray_icon.hide()
        
        # Quit application
        QApplication.quit()

    def changeEvent(self, event):
        """Handle window state changes"""
        if event.type() == QEvent.Type.WindowStateChange:
            if self.windowState() & Qt.WindowState.WindowMinimized:
                event.ignore()
                self.hide()
                
                # Show notification with app icon
                self.tray_icon.showMessage(
                    "rec-all",
                    "Application minimized to tray",
                    QIcon(str(Path(__file__).parent / "icon.svg")),
                    2000
                )
    
    def setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)
        
        # Enhanced top bar with search and refresh
        top = QHBoxLayout()
        
        # Search bar with icon
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(5, 5, 5, 5)
        search_layout.setSpacing(5)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("color: #888; font-size: 14px;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search captures by text or description...")
        self.search_input.textChanged.connect(self.search_content)
        search_layout.addWidget(self.search_input)
        
        # Clear search button
        clear_btn = QPushButton("✕")
        clear_btn.setFixedSize(20, 20)
        clear_btn.clicked.connect(lambda: self.search_input.clear())
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #888;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover {
                color: #fff;
            }
        """)
        search_layout.addWidget(clear_btn)
        
        search_container.setStyleSheet("""
            QWidget {
                background: #444;
                border-radius: 5px;
            }
        """)
        
        top.addWidget(search_container, stretch=1)
        
        # Create refresh button before adding to layout
        self.refresh_btn = QPushButton("⟳ Refresh")
        self.refresh_btn.clicked.connect(self.refresh_content)
        self.refresh_btn.setFixedWidth(100)
        
        # Add re-caption button next to refresh button in the top bar
        self.recaption_btn = QPushButton("🔄 Re-caption")
        self.recaption_btn.setFixedWidth(120)
        self.recaption_btn.clicked.connect(self.start_recaption)
        self.recaption_btn.setEnabled(False)  # Disabled by default
        
        # Update merge button with lightning icon
        self.merge_btn = QPushButton("⚡ Merge")
        self.merge_btn.setStyleSheet("""
            QPushButton {
                background: #1208ff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
                text-align: center;
            }
            QPushButton:hover {
                background: #2318ff;
            }
            QPushButton:pressed {
                background: #0a04d1;
            }
            QPushButton:disabled {
                background: #333;
                color: #666;
            }
            QPushButton::menu-indicator {
                width: 0px;
            }
        """)

        # Create and style the menu
        merge_menu = QMenu(self)
        merge_menu.setStyleSheet("""
            QMenu {
                background-color: #333;
                border: 1px solid #444;
                border-radius: 5px;
                padding: 5px;
            }
            QMenu::item {
                background-color: transparent;
                color: white;
                padding: 8px 20px;
                border-radius: 3px;
                margin: 2px 5px;
            }
            QMenu::item:selected {
                background-color: #1208ff;
            }
            QMenu::separator {
                height: 1px;
                background: #444;
                margin: 5px 0px;
            }
        """)

        # Add menu actions with icons
        text_action = QAction("Export as Text", self)
        text_action.triggered.connect(self.merge_as_text)
        
        video_action = QAction("Export as Video", self)
        video_action.triggered.connect(self.merge_as_video)

        merge_menu.addAction(text_action)
        merge_menu.addAction(video_action)

        self.merge_btn.setMenu(merge_menu)
        
        # Add manifesto button before merge button
        self.manifesto_btn = QPushButton(" Manifesto")
        self.manifesto_btn.setStyleSheet("""
            QPushButton {
                background: #1208ff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
                text-align: center;
            }
            QPushButton:hover {
                background: #2318ff;
            }
        """)
        self.manifesto_btn.clicked.connect(self.show_manifesto)
        top.addWidget(self.manifesto_btn)
        top.addWidget(self.merge_btn)
        
        top.addWidget(self.refresh_btn)
        
        layout.addLayout(top)
        
        # Control buttons and features
        controls = QHBoxLayout()
        controls.setSpacing(10)
        
        # Left side - buttons
        buttons_layout = QHBoxLayout()
        
        # Replace PulsingButton with normal QPushButton
        self.select_btn = QPushButton("📁 Select Folder")
        buttons_layout.addWidget(self.select_btn)
        
        # Other buttons with normal style
        self.import_btn = QPushButton("Import Folder")
        self.start_btn = QPushButton("Start")
        self.stop_btn = QPushButton("Stop")
        
        for btn in [self.import_btn, self.start_btn, self.stop_btn]:
            buttons_layout.addWidget(btn)
            btn.setEnabled(False)  # Initially disabled
        
        # Middle - interval selection with text box
        interval_layout = QHBoxLayout()
        interval_label = QLabel("Capture Interval:")
        interval_label.setStyleSheet("color: #bbb; font-size: 14px;")
        interval_layout.addWidget(interval_label)
        
        self.interval_input = QLineEdit()
        self.interval_input.setPlaceholderText("5")  # Default value hint
        self.interval_input.setFixedWidth(60)
        self.interval_input.setStyleSheet("""
            QLineEdit {
                background: #444;
                color: #fff;
                border: none;
                padding: 5px 10px;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        interval_layout.addWidget(self.interval_input)
        
        seconds_label = QLabel("seconds")
        seconds_label.setStyleSheet("color: #bbb; font-size: 14px;")
        interval_layout.addWidget(seconds_label)
        
        # Right side - features
        features_layout = QHBoxLayout()
        
        # Update OCR checkbox with fixed width
        self.ocr_checkbox = QCheckBox("Enable OCR")
        self.ocr_checkbox.setChecked(True)
        self.ocr_checkbox.setFixedWidth(100)  # Adjust this value as needed
        
        self.ai_checkbox = QCheckBox("Enable AI Description")
        self.ai_checkbox.setEnabled(AI_AVAILABLE)
        self.ai_checkbox.setFixedWidth(160)  # Adjust this value as needed
        
        if not AI_AVAILABLE:
            self.ai_checkbox.setToolTip("AI features not available. Install required packages.")
        
        features_layout.addWidget(self.ocr_checkbox)
        features_layout.addWidget(self.ai_checkbox)
        
        controls.addLayout(buttons_layout)
        controls.addStretch()
        controls.addLayout(interval_layout)
        controls.addStretch()
        controls.addLayout(features_layout)
        
        self.select_btn.clicked.connect(self.select_folder)
        self.import_btn.clicked.connect(self.import_folder)
        self.start_btn.clicked.connect(self.start_capture)
        self.stop_btn.clicked.connect(self.stop_capture)
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(False)
        
        layout.addLayout(controls)
        
        # Recording status (hidden by default)
        self.recording_status = RecordingStatus()
        self.recording_status.hide()
        layout.addWidget(self.recording_status)
        
        # Processing indicator (hidden by default)
        self.processing_indicator = ProcessingIndicator()
        self.processing_indicator.hide()
        processing_layout = QHBoxLayout()
        processing_layout.addStretch()
        processing_layout.addWidget(self.processing_indicator)
        processing_layout.addStretch()
        layout.addLayout(processing_layout)
        
        # Results area
        self.scroll = SmoothScrollArea()
        self.scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: transparent;
            }
            QWidget#scrollContents {
                background: transparent;
            }
            QScrollBar:vertical {
                background: #2a2a2a;
                width: 8px;
                margin: 0;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical {
                background: #1208ff;
                min-height: 30px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2318ff;
            }
            QScrollBar::add-line:vertical, 
            QScrollBar::sub-line:vertical {
                height: 0;
            }
        """)
        
        # Create a widget to hold the flow layout
        self.scroll_widget = QWidget()
        self.scroll_widget.setObjectName("scrollContents")
        self.scroll_layout = FlowLayout(self.scroll_widget, margin=20, spacing=10)
        self.scroll.setWidget(self.scroll_widget)
        self.scroll.setWidgetResizable(True)
        layout.addWidget(self.scroll)
        
        # Add status bar
        self.statusBar().showMessage("Ready")
        self.statusBar().setStyleSheet("""
            QStatusBar {
                background: #333;
                color: #888;
                padding: 5px;
            }
        """)

    def apply_styles(self):
        # Update color scheme from #1DB954 to #1208ff
        additional_styles = """
            QMainWindow {
                background: #222;
            }
            QLineEdit {
                background: transparent;
                color: #fff;
                border: none;
                padding: 8px;
                font-size: 14px;
            }
            QPushButton {
                background: #1208ff;
                color: white;
                border: none;
                padding: 8px 15px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #2318ff;
            }
            QPushButton:pressed {
                background: #0a04d1;
            }
            QPushButton:disabled {
                background: #333;
                color: #666;
            }
            QScrollBar:vertical {
                background: #333;
                width: 10px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1208ff;
                min-height: 30px;
                border-radius: 5px;
            }
            QScrollBar::handle:vertical:hover {
                background: #2318ff;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;
            }
            QToolTip {
                background: #444;
                color: #fff;
                border: none;
                padding: 5px;
            }
        """
        self.setStyleSheet(self.styleSheet() + additional_styles)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Directory")
        if folder:
            self.save_path = folder
            self.start_btn.setEnabled(True)
            self.import_btn.setEnabled(True)
            
    def import_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Import Directory")
        if folder:
            self.load_folder_data(folder)

    def start_capture(self):
        if not self.save_path:
            return
        
        # Get and validate interval value
        try:
            interval_text = self.interval_input.text().strip()
            interval = float(interval_text) if interval_text else 5.0
            
            # Ensure interval is positive
            if interval <= 0:
                interval = 5.0
                self.interval_input.setText("5")
        except ValueError:
            # If conversion fails, use default
            interval = 5.0
            self.interval_input.setText("5")
        
        # Create and start capture thread
        self.capture_thread = ScreenCapture(
            self.save_path,
            interval=interval,
            use_ocr=self.ocr_checkbox.isChecked(),
            use_ai=self.ai_checkbox.isChecked()
        )
        self.capture_thread.capture_complete.connect(self.handle_capture)
        self.capture_thread.start()
        
        # Update UI state
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.recording_status.show()
        self.recording_status.start_recording(
            ocr_enabled=self.ocr_checkbox.isChecked(),
            ai_enabled=self.ai_checkbox.isChecked()
        )
        self.search_input.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.ocr_checkbox.setEnabled(False)
        self.ai_checkbox.setEnabled(False)
        self.interval_input.setEnabled(False)
        
        # Update tray icon status
        self.recording_action.setText("Recording...")
        
        # Show notification
        self.tray_icon.showMessage(
            "rec-all",
            f"Screen recording started (Interval: {interval} seconds)",
            QIcon(str(Path(__file__).parent / "icon.svg")),
            2000
        )

    def stop_capture(self):
        if self.capture_thread:
            self.stop_btn.setEnabled(False)
            self.is_processing = True
            
            # Show processing indicator
            features = []
            if self.capture_thread.use_ocr:
                features.append("OCR")
            if self.capture_thread.use_ai:
                features.append("AI")
                
            if features:
                self.processing_indicator.start_animation()
                self.processing_indicator.status_text = f"Processing {' & '.join(features)}"
                self.processing_indicator.show()
            
            # Schedule UI cleanup for next event loop iteration
            QTimer.singleShot(100, self._cleanup_and_continue_stop)

    def _cleanup_and_continue_stop(self):
        # Clear current display while processing
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Schedule the next step
        QTimer.singleShot(100, self._finish_stop_capture)

    def _finish_stop_capture(self):
        # Stop and wait for capture thread
        self.capture_thread.stop()
        self.capture_thread.wait()
        
        self.recording_status.hide()
        
        # Process remaining work
        if self.capture_thread.use_ai and self.capture_thread.description_queue:
            if self.processing_thread:
                self.processing_thread.wait()
            
            self.processing_thread = ProcessingThread(self.capture_thread)
            self.processing_thread.progress.connect(self.update_processing_progress)
            self.processing_thread.finished.connect(self._complete_stop_capture)
            self.processing_thread.start()
        else:
            self._complete_stop_capture()

    def _complete_stop_capture(self):
        if self.processing_thread:
            self.processing_thread.wait()
            self.processing_thread = None
        
        self.processing_indicator.stop_animation()
        self.processing_indicator.hide()
        
        if self.capture_thread:
            self.capture_thread = None
        
        # Re-enable controls
        self.start_btn.setEnabled(True)
        self.recording_status.stop_recording()
        self.recording_status.hide()
        self.search_input.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.ocr_checkbox.setEnabled(True)
        self.ai_checkbox.setEnabled(AI_AVAILABLE)
        self.interval_input.setEnabled(True)
        
        # Reset processing flag
        self.is_processing = False
        
        # Update tray icon status
        self.recording_action.setText("Not Recording")
        
        # Show notification
        self.tray_icon.showMessage(
            "rec-all",
            "Screen recording stopped",
            QIcon(str(Path(__file__).parent / "icon.svg")),
            2000
        )
        
        # Load folder data with batched processing
        if self.save_path:
            self.statusBar().showMessage("Loading folder content...")
            QTimer.singleShot(100, lambda: self._load_folder_batch(0))

    def _load_folder_batch(self, start_index=0, batch_size=50):
        if start_index == 0:
            # First batch: initialize lists
            self.metadata_list.clear()
            self.filtered_indices.clear()
            self._temp_image_paths = []
            
            # Collect all image paths first
            for root, _, files in os.walk(self.save_path):
                for file in files:
                    if file.endswith(".jpg"):
                        self._temp_image_paths.append((root, file))
            
            if not self._temp_image_paths:
                self._show_no_content_message()
                return
        
        # Process current batch
        end_index = min(start_index + batch_size, len(self._temp_image_paths))
        current_batch = self._temp_image_paths[start_index:end_index]
        
        for root, file in current_batch:
            try:
                img_path = os.path.join(root, file)
                date_str = os.path.basename(os.path.dirname(os.path.dirname(img_path)))
                time_str = file.split("_")[1].split(".")[0]
                
                timestamp = datetime.strptime(
                    f"{date_str} {time_str}",
                    "%Y-%m-%d %H%M%S"
                )
                
                text_path = os.path.join(
                    os.path.dirname(os.path.dirname(img_path)),
                    "texts",
                    f"text_{time_str}.txt"
                )
                desc_path = os.path.join(
                    os.path.dirname(os.path.dirname(img_path)),
                    "texts",
                    f"description_{time_str}.txt"
                )
                
                text_content = ""
                if os.path.exists(text_path):
                    try:
                        with open(text_path, 'r', encoding='utf-8') as f:
                            text_content = f.read()
                    except Exception as e:
                        print(f"Error reading text file {text_path}: {e}")
                
                desc_content = ""
                if os.path.exists(desc_path):
                    try:
                        with open(desc_path, 'r', encoding='utf-8') as f:
                            desc_content = f.read()
                    except Exception as e:
                        print(f"Error reading description file {desc_path}: {e}")
                
                self.metadata_list.append({
                    "image_path": img_path,
                    "text_content": text_content,
                    "description_content": desc_content,
                    "timestamp": timestamp,
                    "relative_time": get_relative_time(timestamp)
                })
            
            except Exception as e:
                print(f"Error processing file {file}: {e}")
                continue
        
        # Update progress
        progress = min(100, int(end_index / len(self._temp_image_paths) * 100))
        self.statusBar().showMessage(f"Loading folder content... {progress}%")
        
        # Schedule next batch or finish
        if end_index < len(self._temp_image_paths):
            QTimer.singleShot(50, lambda: self._load_folder_batch(end_index))
        else:
            QTimer.singleShot(50, self._finish_loading_folder)

    def _finish_loading_folder(self):
        # Clean up temporary storage
        if hasattr(self, '_temp_image_paths'):
            del self._temp_image_paths
        
        # Sort and update display
        self.metadata_list.sort(key=lambda x: x['timestamp'], reverse=True)
        self.filtered_indices = list(range(len(self.metadata_list)))
        self.update_results()
        
        # Update status and enable buttons
        self.statusBar().showMessage(f"Loaded {len(self.metadata_list)} images", 3000)
        self.recaption_btn.setEnabled(bool(self.metadata_list) and AI_AVAILABLE)
        self.merge_btn.setEnabled(bool(self.metadata_list))

    def _show_no_content_message(self):
        no_content = QWidget()
        no_content_layout = QVBoxLayout(no_content)
        
        icon_label = QLabel("📁")
        icon_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 48px;
                margin-bottom: 10px;
            }
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        message_label = QLabel("No images found in this folder")
        message_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 16px;
                margin-bottom: 5px;
            }
        """)
        message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        hint_label = QLabel("Start capturing or select a different folder")
        hint_label.setStyleSheet("""
            QLabel {
                color: #666;
                font-size: 14px;
            }
        """)
        hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        no_content_layout.addStretch()
        no_content_layout.addWidget(icon_label)
        no_content_layout.addWidget(message_label)
        no_content_layout.addWidget(hint_label)
        no_content_layout.addStretch()
        
        self.scroll_layout.addWidget(no_content)
        self.statusBar().showMessage("No images found in folder", 3000)

    def handle_capture(self, img_path: str, text_content: Optional[str], desc_content: Optional[str]):
        timestamp = datetime.now()
        
        metadata = {
            "image_path": img_path,
            "text_content": text_content,
            "description_content": desc_content,
            "timestamp": timestamp,
            "relative_time": get_relative_time(timestamp)
        }
        
        self.metadata_list.insert(0, metadata)
        # Only update display if not processing
        if not self.is_processing:
            self.update_results()
        
        # Update status bar with capture info
        self.statusBar().showMessage(f"Captured: {os.path.basename(img_path)}", 3000)

    def load_folder_data(self, folder: str):
        if not folder:
            return
        
        # Clear existing content first
        self.metadata_list.clear()
        self.filtered_indices.clear()
        
        # Clear the UI
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        # Add a loading message to the status bar
        self.statusBar().showMessage("Loading folder content...")
        QApplication.processEvents()  # Force UI update
        
        try:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    if file.endswith(".jpg"):
                        img_path = os.path.join(root, file)
                        
                        # Extract timestamp from filename
                        try:
                            # Parse date from parent folder (YYYY-MM-DD)
                            date_str = os.path.basename(os.path.dirname(os.path.dirname(img_path)))
                            # Parse time from filename (HHMMSS)
                            time_str = file.split("_")[1].split(".")[0]
                            
                            timestamp = datetime.strptime(
                                f"{date_str} {time_str}",
                                "%Y-%m-%d %H%M%S"
                            )
                        except Exception as e:
                            print(f"Error parsing timestamp for {file}: {e}")
                            continue
                        
                        text_path = os.path.join(
                            os.path.dirname(os.path.dirname(img_path)),
                            "texts",
                            f"text_{time_str}.txt"
                        )
                        desc_path = os.path.join(
                            os.path.dirname(os.path.dirname(img_path)),
                            "texts",
                            f"description_{time_str}.txt"
                        )
                        
                        text_content = ""
                        if os.path.exists(text_path):
                            try:
                                with open(text_path, 'r', encoding='utf-8') as f:
                                    text_content = f.read()
                            except Exception as e:
                                print(f"Error reading text file {text_path}: {e}")
                        
                        desc_content = ""
                        if os.path.exists(desc_path):
                            try:
                                with open(desc_path, 'r', encoding='utf-8') as f:
                                    desc_content = f.read()
                            except Exception as e:
                                print(f"Error reading description file {desc_path}: {e}")
                        
                        self.metadata_list.append({
                            "image_path": img_path,
                            "text_content": text_content,
                            "description_content": desc_content,
                            "timestamp": timestamp,
                            "relative_time": get_relative_time(timestamp)
                        })
            
            if not self.metadata_list:
                # Create and add a "no content" message widget
                no_content = QWidget()
                no_content_layout = QVBoxLayout(no_content)
                
                icon_label = QLabel("📁")
                icon_label.setStyleSheet("""
                    QLabel {
                        color: #666;
                        font-size: 48px;
                        margin-bottom: 10px;
                    }
                """)
                icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                message_label = QLabel("No images found in this folder")
                message_label.setStyleSheet("""
                    QLabel {
                        color: #888;
                        font-size: 16px;
                        margin-bottom: 5px;
                    }
                """)
                message_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                hint_label = QLabel("Start capturing or select a different folder")
                hint_label.setStyleSheet("""
                    QLabel {
                        color: #666;
                        font-size: 14px;
                    }
                """)
                hint_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                
                no_content_layout.addStretch()
                no_content_layout.addWidget(icon_label)
                no_content_layout.addWidget(message_label)
                no_content_layout.addWidget(hint_label)
                no_content_layout.addStretch()
                
                self.scroll_layout.addWidget(no_content)
                self.statusBar().showMessage("No images found in folder", 3000)
                return
                
            # If we have content, sort and display it
            self.metadata_list.sort(key=lambda x: x['timestamp'], reverse=True)
            self.filtered_indices = list(range(len(self.metadata_list)))
            self.update_results()
            self.statusBar().showMessage(f"Loaded {len(self.metadata_list)} images", 3000)
            
            # Enable re-caption button if content is loaded and AI is available
            self.recaption_btn.setEnabled(bool(self.metadata_list) and AI_AVAILABLE)
            self.merge_btn.setEnabled(bool(self.metadata_list))
            
        except Exception as e:
            # Handle any unexpected errors
            error_widget = QLabel(f"Error loading folder content: {str(e)}")
            error_widget.setStyleSheet("""
                QLabel {
                    color: #ff4444;
                    padding: 20px;
                    font-size: 14px;
                }
            """)
            self.scroll_layout.addWidget(error_widget)
            self.statusBar().showMessage("Error loading folder content", 3000)

    def search_content(self):
        search_text = self.search_input.text().lower().strip()
        
        try:
            if search_text:
                # Store original indices of matching items
                self.filtered_indices = []
                for i, m in enumerate(self.metadata_list):
                    # Safely get text content
                    text_content = m.get('text_content', '').lower() if m.get('text_content') else ''
                    desc_content = m.get('description_content', '').lower() if m.get('description_content') else ''
                    
                    # Check if search text is in either content
                    if (search_text in text_content or search_text in desc_content):
                        self.filtered_indices.append(i)
                
                # Sort filtered_indices to maintain chronological order
                self.filtered_indices.sort(reverse=True)
                
                # Update status bar with search results
                result_count = len(self.filtered_indices)
                self.statusBar().showMessage(
                    f"Found {result_count} {'match' if result_count == 1 else 'matches'}", 
                    3000
                )
            else:
                self.filtered_indices = list(range(len(self.metadata_list)))
                self.statusBar().clearMessage()
            
            self.update_results()
            
        except Exception as e:
            print(f"Search error: {e}")
            # Reset to show all items in case of error
            self.filtered_indices = list(range(len(self.metadata_list)))
            self.statusBar().showMessage("Search error occurred", 3000)
            self.update_results()

    def update_results(self):
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for i in self.filtered_indices:
            item = ResultCard(self.metadata_list[i], i, self.show_preview)
            self.scroll_layout.addWidget(item)

    def show_preview(self, index: int):
        dialog = ImagePreview(
            self.metadata_list,
            index,
            self.filtered_indices
        )
        dialog.exec()

    def closeEvent(self, event):
        """Handle application closing"""
        event.ignore()  # Ignore the close event
        self.hide()     # Hide the window instead
        
        # Show notification with app icon
        self.tray_icon.showMessage(
            "rec-all",
            "Application minimized to tray",
            QIcon(str(Path(__file__).parent / "icon.svg")),
            2000
        )

    def update_processing_progress(self, progress: int):
        self.processing_indicator.set_progress(progress)
        # Don't update display during processing

    def refresh_content(self):
        # Create rotation animation
        self.refresh_btn.setEnabled(False)
        self.refresh_btn.setText("⟳ Refreshing...")
        
        # Use QTimer to simulate async refresh
        QTimer.singleShot(100, lambda: self.load_folder_data(self.save_path))
        QTimer.singleShot(1000, lambda: self.finish_refresh())

    def finish_refresh(self):
        self.refresh_btn.setEnabled(True)
        self.refresh_btn.setText("⟳ Refresh")
        self.statusBar().showMessage("Content refreshed", 3000)

    def start_recaption(self):
        """Start the re-captioning process for all loaded images"""
        if not self.metadata_list:
            self.statusBar().showMessage("No images to process", 3000)
            return
        
        # Check if any feature is enabled
        use_ocr = self.ocr_checkbox.isChecked()
        use_ai = self.ai_checkbox.isChecked() and AI_AVAILABLE
        
        if not use_ocr and not use_ai:
            self.statusBar().showMessage("Please enable OCR and/or AI description", 3000)
            return
        
        try:
            # Disable buttons during processing
            self.recaption_btn.setEnabled(False)
            self.refresh_btn.setEnabled(False)
            self.import_btn.setEnabled(False)
            
            # Show processing indicator with active features
            features = []
            if use_ocr:
                features.append("OCR")
            if use_ai:
                features.append("AI")
            self.processing_indicator.status_text = f"Processing {' & '.join(features)}"
            self.processing_indicator.start_animation()
            self.processing_indicator.show()
            
            # Create processing thread for re-captioning
            self.processing_thread = RecaptionThread(
                self.metadata_list,
                use_ocr=use_ocr,
                use_ai=use_ai
            )
            self.processing_thread.progress.connect(self.update_processing_progress)
            self.processing_thread.finished.connect(self.finish_recaption)
            self.processing_thread.error.connect(self.handle_recaption_error)
            self.processing_thread.start()
            
        except Exception as e:
            print(f"Error starting recaption: {e}")
            self.handle_recaption_error(str(e))

    def finish_recaption(self):
        """Handle completion of re-captioning process"""
        if self.processing_thread:
            self.processing_thread.wait()
            self.processing_thread = None
        
        # Stop and hide processing indicator
        self.processing_indicator.stop_animation()
        self.processing_indicator.hide()
        
        # Re-enable buttons
        self.recaption_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        
        # Reload folder data to show new captions
        if self.save_path:
            self.load_folder_data(self.save_path)
        
        # Show completion message
        self.statusBar().showMessage("Re-captioning completed", 3000)

    def handle_recaption_error(self, error_msg: str):
        """Handle errors during recaption process"""
        print(f"Recaption error: {error_msg}")
        self.statusBar().showMessage(f"Re-caption error: {error_msg}", 5000)
        self.processing_indicator.stop_animation()
        self.processing_indicator.hide()
        self.recaption_btn.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.import_btn.setEnabled(True)

    def export_daily_texts(self):
        """Export all texts from the current day into a single file"""
        if not self.metadata_list:
            self.statusBar().showMessage("No content to export", 3000)
            return
        
        try:
            # Group metadata by date
            date_groups = {}
            for metadata in self.metadata_list:
                date_str = metadata['timestamp'].strftime('%Y-%m-%d')
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append(metadata)
            
            # Sort dates
            sorted_dates = sorted(date_groups.keys(), reverse=True)
            
            for date_str in sorted_dates:
                entries = date_groups[date_str]
                # Sort entries by timestamp
                entries.sort(key=lambda x: x['timestamp'], reverse=True)
                
                # Create merged content for each day
                merged_content = []
                merged_content.append(f"=== Merged Texts for {date_str} ===\n")
                
                for entry in entries:
                    time_str = entry['timestamp'].strftime('%H:%M:%S')
                    merged_content.append(f"\n[{time_str}]\n")
                    
                    # Add OCR content if exists
                    if entry.get('text_content'):
                        merged_content.append("OCR Results:")
                        merged_content.append(entry['text_content'].strip())
                        merged_content.append("")
                    
                    # Add AI description if exists
                    if entry.get('description_content'):
                        merged_content.append("AI Description:")
                        merged_content.append(entry['description_content'].strip())
                        merged_content.append("")
                
                if merged_content:
                    # Save to texts directory with merged_ prefix
                    base_dir = os.path.dirname(entries[0]['image_path'])
                    text_dir = os.path.join(os.path.dirname(base_dir), "texts")
                    merged_path = os.path.join(text_dir, f"merged_{date_str}.txt")
                    
                    with open(merged_path, 'w', encoding='utf-8') as f:
                        f.write("\n".join(merged_content))
            
            self.statusBar().showMessage("Texts merged successfully", 3000)
            
        except Exception as e:
            print(f"Merge error: {e}")
            self.statusBar().showMessage(f"Merge failed: {str(e)}", 5000)

    def create_video_from_screenshots(self):
        """Create a video from the day's screenshots"""
        if not self.metadata_list:
            self.statusBar().showMessage("No screenshots to process", 3000)
            return
        
        try:
            # Group screenshots by date
            date_groups = {}
            for metadata in self.metadata_list:
                date_str = metadata['timestamp'].strftime('%Y-%m-%d')
                if date_str not in date_groups:
                    date_groups[date_str] = []
                date_groups[date_str].append(metadata)
            
            for date_str, entries in date_groups.items():
                # Sort entries by timestamp
                entries.sort(key=lambda x: x['timestamp'])
                
                if not entries:
                    continue
                
                # Get first image to determine dimensions
                first_img = cv2.imread(entries[0]['image_path'])
                height, width = first_img.shape[:2]
                
                # Create video writer
                base_dir = os.path.dirname(entries[0]['image_path'])
                video_dir = os.path.join(os.path.dirname(base_dir), "videos")
                os.makedirs(video_dir, exist_ok=True)
                
                video_path = os.path.join(video_dir, f"timelapse_{date_str}.mp4")
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(video_path, fourcc, 2.0, (width, height))  # 2 FPS
                
                # Show progress in status bar
                total_frames = len(entries)
                
                for i, entry in enumerate(entries):
                    try:
                        img = cv2.imread(entry['image_path'])
                        if img is not None:
                            # Add timestamp to frame
                            timestamp = entry['timestamp'].strftime('%H:%M:%S')
                            cv2.putText(img, timestamp, (10, height - 20), 
                                      cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
                            out.write(img)
                            
                            # Update progress
                            progress = int((i + 1) / total_frames * 100)
                            self.statusBar().showMessage(f"Creating video: {progress}%")
                            QApplication.processEvents()  # Keep UI responsive
                            
                    except Exception as e:
                        print(f"Error processing frame {entry['image_path']}: {e}")
                
                out.release()
                self.statusBar().showMessage(f"Video created: {video_path}", 3000)
        
        except Exception as e:
            print(f"Video creation error: {e}")
            self.statusBar().showMessage(f"Video creation failed: {str(e)}", 5000)

    def merge_as_text(self):
        """Merge selected screenshots as text file"""
        if not self.metadata_list:
            return
            
        # Get save path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Text File",
            "",
            "Text Files (*.txt);;All Files (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for metadata in self.metadata_list:
                    # Write timestamp
                    f.write(f"\n=== {get_relative_time(metadata['timestamp'])} ===\n\n")
                    
                    # Write OCR text if available
                    if metadata.get('text_content'):
                        # Clean OCR text (remove confidence scores)
                        ocr_text = '\n'.join([
                            line.split('(Confidence:')[0].strip()
                            for line in metadata['text_content'].split('\n')
                            if line.strip()
                        ])
                        f.write(f"OCR Text:\n{ocr_text}\n\n")
                    
                    # Write AI description if available
                    if metadata.get('description_content'):
                        f.write(f"AI Description:\n{metadata['description_content']}\n\n")
                    
                    f.write("-" * 80 + "\n")  # Separator
                    
        except Exception as e:
            print(f"Error merging text: {e}")

    def merge_as_video(self):
        """Merge selected screenshots as video"""
        if not self.metadata_list:
            return
            
        # Get save path from user
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Video File",
            "",
            "MP4 Files (*.mp4);;All Files (*.*)"
        )
        
        if not file_path:
            return
            
        try:
            # Get first image to determine dimensions
            first_img = cv2.imread(self.metadata_list[0]['image_path'])
            height, width = first_img.shape[:2]
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(file_path, fourcc, 1.0, (width, height))
            
            # Write each frame
            for metadata in self.metadata_list:
                img = cv2.imread(metadata['image_path'])
                if img is not None:
                    out.write(img)
                    
            out.release()
            
        except Exception as e:
            print(f"Error merging video: {e}")

    def show_manifesto(self):
        """Show the manifesto in a styled dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("rec-all Manifesto")
        dialog.setMinimumSize(800, 600)
        
        layout = QVBoxLayout(dialog)
        
        # Create scrollable text area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("""
            QScrollArea {
                border: none;
                background: #222;
            }
            QScrollBar:vertical {
                background: #333;
                width: 8px;
                margin: 0;
            }
            QScrollBar::handle:vertical {
                background: #1208ff;
                min-height: 30px;
                border-radius: 4px;
            }
        """)
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        
        # Add manifesto text with styled sections
        manifesto_text = QTextEdit()
        manifesto_text.setReadOnly(True)
        manifesto_text.setStyleSheet("""
            QTextEdit {
                background: #222;
                color: #fff;
                border: none;
                font-size: 15px;
                line-height: 1.6;
                padding: 20px;
            }
        """)
        
        # Format manifesto with HTML styling
        manifesto = f"""
        <div style="font-family: system-ui, -apple-system, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
            <h1 style="color: #1208ff; font-size: 28px; margin-bottom: 30px; text-align: center;">
                A Manifesto for Memory:<br>Owning Time, Owning Self
            </h1>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                In the Age of Fragmentation, Own Your Story
            </h2>
            <p style="margin-bottom: 20px;">
                We live in a world saturated by fleeting moments—notifications that vanish, 
                conversations lost to time, memories displaced by the next demand for attention. 
                In this era of ephemera, there is a quiet rebellion: reclaiming not just the right 
                to our data but to our existence as a continuous narrative.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                Introducing rec-all: A Time Machine for the Everyday
            </h2>
            <p style="margin-bottom: 20px;">
                rec-all is not just software; it is a revolution. Imagine every moment of your 
                digital life meticulously preserved—not as a voyeur, but as a loyal historian. 
                With rec-all, your computer becomes a time machine, archiving the mundane and 
                the monumental alike, creating a personal atlas of memory. Powered by advanced 
                artificial intelligence, rec-all transforms raw data into an indexed, searchable 
                experience. Your moments are not just saved; they are liberated.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                Why Open Source? Why Ownership?
            </h2>
            <p style="margin-bottom: 20px;">
                rec-all is open source because freedom demands transparency. The sanctity of 
                memory belongs to no corporation, no algorithmic overlord. When you use rec-all, 
                you use a tool that is yours—not a product, not a service, but an extension of 
                your own agency. The source code lies bare, unshackled by gatekeepers, ready 
                to be adapted, challenged, improved.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                The Philosophy of Remembering
            </h2>
            <p style="margin-bottom: 20px;">
                To remember is to resist oblivion. To record is to rebel against the fleeting 
                nature of time. But this act must be ethical. Memory is power, and power demands 
                responsibility. rec-all does not monetize your data, nor does it presume to know 
                what you value. It simply gives you the ability to decide.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                What rec-all Is Not
            </h2>
            <p style="margin-bottom: 20px;">
                rec-all is not a surveillance tool. It is not an arbiter of worth, nor a judge 
                of which moments deserve preservation. It is neutral, impartial, and empowering. 
                It does not hoard your memories in some distant server; they remain with you, 
                on your machine, where they belong.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                The Human in the Loop
            </h2>
            <p style="margin-bottom: 20px;">
                AI powers rec-all, but it does not control it. You remain the master of your 
                archive. The AI is your assistant, not your ruler���its role is to illuminate 
                patterns, reveal connections, and make your recorded history accessible without 
                dictating its importance.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                Towards a Decentralized Future
            </h2>
            <p style="margin-bottom: 20px;">
                We envision a world where every individual owns their digital shadow. Where 
                data is not the currency of surveillance capitalism but the fabric of personal 
                sovereignty. rec-all is our contribution to that world: a tool for those who 
                wish to live deliberately, remembering deeply, and owning fully.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                The Poetic Struggle of Memory
            </h2>
            <p style="margin-bottom: 20px;">
                This is not just code. It is a love letter to the human condition—a tribute 
                to our yearning to be remembered, to leave traces, to find meaning in the 
                seemingly insignificant. rec-all whispers: "Your moments matter. Even the 
                quiet ones."
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                An Invitation to Co-Create
            </h2>
            <p style="margin-bottom: 20px;">
                rec-all is for everyone who refuses to be forgotten, for those who believe 
                in the sanctity of their narrative. It is a canvas, a tool, a movement. 
                Take it, use it, and shape it into something even greater.
            </p>

            <h2 style="color: #1208ff; font-size: 22px; margin-top: 30px; margin-bottom: 15px;">
                In Closing
            </h2>
            <p style="margin-bottom: 20px;">
                Time is fleeting, but memory is eternal—if we choose to preserve it. rec-all 
                is your time machine, your archive, your monument to the life you live. 
                Own it. Embrace it. Reclaim the power of your narrative.
            </p>

            <p style="text-align: center; color: #1208ff; font-size: 20px; margin-top: 40px; margin-bottom: 20px;">
                Welcome to the revolution of remembering.<br>
                Welcome to rec-all.
            </p>
        </div>
        """
        
        manifesto_text.setHtml(manifesto)
        content_layout.addWidget(manifesto_text)
        
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        # Add close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #1208ff;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-size: 14px;
                margin: 10px;
            }
            QPushButton:hover {
                background: #2318ff;
            }
        """)
        close_btn.clicked.connect(dialog.close)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(close_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        dialog.exec()

class RecaptionThread(QThread):
    progress = pyqtSignal(int)
    finished = pyqtSignal()
    error = pyqtSignal(str)
    
    def __init__(self, metadata_list: List[Dict], use_ocr: bool = False, use_ai: bool = False):
        super().__init__()
        self.metadata_list = metadata_list
        self.use_ocr = use_ocr
        self.use_ai = use_ai
        self.describer = None
        self.ocr_reader = None
    
    def run(self):
        try:
            # Initialize required tools
            if self.use_ocr:
                self.ocr_reader = initialize_reader()
                if not self.ocr_reader:
                    self.error.emit("Failed to initialize OCR")
                    return
                    
            if self.use_ai:
                if not AI_AVAILABLE:
                    self.error.emit("AI features not available")
                    return
                self.describer = ImageDescriptionGenerator()
            
            total = len(self.metadata_list)
            print(f"Processing {total} images")
            
            for i, metadata in enumerate(self.metadata_list):
                try:
                    img_path = metadata['image_path']
                    if not os.path.exists(img_path):
                        continue
                        
                    base_dir = os.path.dirname(os.path.dirname(img_path))
                    text_dir = os.path.join(base_dir, "texts")
                    time_str = os.path.splitext(os.path.basename(img_path))[0].split('_')[1]
                    
                    # Process OCR if enabled
                    if self.use_ocr:
                        try:
                            img = cv2.imread(img_path)
                            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                            results = self.ocr_reader.readtext(img)
                            
                            # Format OCR text
                            text_blocks = []
                            for detection in results:
                                bbox, text, conf = detection
                                if conf > 0.2:
                                    text_blocks.append(f"{text} (Confidence: {conf:.2f})")
                            
                            text_content = "\n".join(text_blocks)
                            
                            # Save OCR results
                            text_path = os.path.join(text_dir, f"text_{time_str}.txt")
                            os.makedirs(text_dir, exist_ok=True)
                            with open(text_path, 'w', encoding='utf-8') as f:
                                f.write(text_content)
                        except Exception as e:
                            print(f"OCR Error for {img_path}: {e}")
                    
                    # Process AI description if enabled
                    if self.use_ai:
                        try:
                            description = self.describer.generate_description(img_path)
                            desc_path = os.path.join(text_dir, f"description_{time_str}.txt")
                            os.makedirs(text_dir, exist_ok=True)
                            with open(desc_path, 'w', encoding='utf-8') as f:
                                f.write(description)
                        except Exception as e:
                            print(f"AI Description Error for {img_path}: {e}")
                    
                except Exception as e:
                    print(f"Error processing image {img_path}: {e}")
                    self.error.emit(f"Error processing image: {str(e)}")
                
                self.progress.emit(int((i + 1) / total * 100))
            
        except Exception as e:
            print(f"Re-caption thread error: {e}")
            self.error.emit(f"Re-caption error: {str(e)}")
        finally:
            self.describer = None
            self.ocr_reader = None
            self.finished.emit()

class FlowLayout(QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        self.itemList = []
        self.margin = margin
        self.spacing = spacing
        
    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)
    
    def addItem(self, item):
        self.itemList.append(item)
    
    def count(self):
        return len(self.itemList)
    
    def itemAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList[index]
        return None
    
    def takeAt(self, index):
        if 0 <= index < len(self.itemList):
            return self.itemList.pop(index)
        return None
    
    def expandingDirections(self):
        return Qt.Orientation(0)
    
    def hasHeightForWidth(self):
        return True
    
    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height
    
    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)
    
    def sizeHint(self):
        return self.minimumSize()
    
    def minimumSize(self):
        size = QSize()
        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())
        size += QSize(2 * self.margin, 2 * self.margin)
        return size
    
    def doLayout(self, rect, testOnly):
        x = rect.x() + self.margin
        y = rect.y() + self.margin
        lineHeight = 0
        
        for item in self.itemList:
            nextX = x + item.sizeHint().width() + self.spacing
            if nextX - self.spacing > rect.right() and lineHeight > 0:
                x = rect.x() + self.margin
                y = y + lineHeight + self.spacing
                nextX = x + item.sizeHint().width() + self.spacing
                lineHeight = 0
            
            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))
            
            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())
        
        return y + lineHeight - rect.y() + self.margin

class SplashScreen(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        # Get screen size
        screen = QApplication.primaryScreen().geometry()
        screen_center = screen.center()
        
        # Set splash screen size
        splash_size = 600  # Reduced from 800 to 600
        self.setFixedSize(splash_size, splash_size)
        
        # Center splash screen on screen
        self.move(
            screen_center.x() - (splash_size // 2),
            screen_center.y() - (splash_size // 2)
        )
        
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        # Create label for icon
        self.icon_label = QLabel(self)
        self.icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Load and set icon
        icon_path = str(Path(__file__).parent / "icon.svg")
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path)
            scaled_pixmap = pixmap.scaled(
                400, 400,  # Reduced from 600 to 400
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.icon_label.setPixmap(scaled_pixmap)
        
        layout.addWidget(self.icon_label)
        
        # Add app name label
        name_label = QLabel("rec-all", self)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 48px;
                font-weight: bold;
                margin-top: 0px;
            }
        """)
        layout.addWidget(name_label)
        
        # Setup opacity effect
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0)
        
        # Create fade in animation
        self.fade_in = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_in.setDuration(1000)
        self.fade_in.setStartValue(0)
        self.fade_in.setEndValue(1)
        self.fade_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Create fade out animation
        self.fade_out = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_out.setDuration(800)
        self.fade_out.setStartValue(1)
        self.fade_out.setEndValue(0)
        self.fade_out.setEasingCurve(QEasingCurve.Type.InCubic)
        
        # Connect fade out animation finished signal
        self.fade_out.finished.connect(self.close)
        
    def paintEvent(self, event):
        """Override paint event to create rounded corners and background"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Create rounded rectangle path
        path = QPainterPath()
        # Convert QRect to QRectF
        rect = QRectF(self.rect())
        path.addRoundedRect(rect, 20, 20)
        
        # Set background color
        painter.fillPath(path, QColor("#222222"))

def main():
    app = QApplication(sys.argv)
    
    # Set application-wide icon
    app_icon = load_app_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    
    # Create splash screen
    splash = SplashScreen()
    splash.show()
    
    # Create main window but don't show it yet
    main_window = MainWindow()
    
    # Start fade in animation for splash
    splash.fade_in.start()
    
    # Create timer to start fade out after 2 seconds
    QTimer.singleShot(2000, lambda: handle_splash_transition(splash, main_window))
    
    return app.exec()

def handle_splash_transition(splash, main_window):
    # Start fade out animation
    splash.fade_out.start()
    
    # Show main window after fade out animation completes
    splash.fade_out.finished.connect(lambda: complete_transition(main_window))

def complete_transition(main_window):
    # Prepare fade in effect for main window
    main_window.prepare_fade_in()
    # Show main window
    main_window.show()

if __name__ == '__main__':
    main()
