# ui.py

# Widgets
from PyQt6.QtWidgets import (
    QMainWindow,
    QWidget,
    QComboBox,
    QCheckBox,
    QSlider,
    QProgressBar,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QPushButton,
    QLabel,
    QGroupBox,
    QStatusBar,
    QApplication,
)
# GUI components
from PyQt6.QtGui import QFont, QTextCursor, QTextBlockFormat
# Core functionality
from PyQt6.QtCore import Qt, pyqtSlot
# Local imports
from src.config.config import MODEL_CHOICES
from src.config.constants import (
    DEFAULT_FONT_FAMILY,
    DEFAULT_FONT_SIZE,
    GUI_FONT_SIZE,
    LINE_SPACING_PERCENT,
    DEFAULT_TEMPERATURE,
    MIN_WINDOW_WIDTH,
    MIN_WINDOW_HEIGHT,
    TEXT_LAYOUT_RATIO,
    CONTROL_PANEL_RATIO,
    SPLITTER_LEFT_SIZE,
    SPLITTER_RIGHT_SIZE,
    TEMPERATURE_MIN,
    TEMPERATURE_MAX,
)

# Custom widget with built-in drag-and-drop for .txt files
from src.ui.custom_widgets import DragTextEdit

class MainWindow(QMainWindow):
    def __init__(self, logic_handler) -> None:
        super().__init__()
        self.logic_handler = logic_handler
        self.default_font_family = DEFAULT_FONT_FAMILY
        self.default_font_size = DEFAULT_FONT_SIZE
        self.gui_font_size = GUI_FONT_SIZE
        self.line_spacing = LINE_SPACING_PERCENT
        self.temperature = DEFAULT_TEMPERATURE  # Initialize to 0.7 (70%)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self) -> None:
        self.setWindowTitle("Writing Assistant")
        self.setMinimumSize(MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT)

        main_layout = QVBoxLayout()

        # Text area layout
        text_layout = QHBoxLayout()
        self.setup_text_areas(text_layout)

        # Control panel layout
        control_panel = QGroupBox("Control Panel")
        control_layout = QVBoxLayout()
        self.setup_control_panel(control_layout)
        control_panel.setLayout(control_layout)

        main_layout.addLayout(text_layout, TEXT_LAYOUT_RATIO)
        main_layout.addWidget(control_panel, CONTROL_PANEL_RATIO)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_text_areas(self, layout: QHBoxLayout) -> None:
        self.input_box = DragTextEdit()
        self.input_box.setFont(QFont(self.default_font_family, self.default_font_size))
        self.input_box.setPlaceholderText("Enter your text here...\n\nDrag & drop .txt files here")
        self.set_line_spacing(self.input_box, self.line_spacing)
        self.input_box.setAcceptRichText(False)
        # Drag & drop is handled natively by DragTextEdit

        # Output panel with copy button
        output_panel = QWidget()
        output_layout = QVBoxLayout()
        output_layout.setContentsMargins(0, 0, 0, 0)
        
        # Copy button row
        button_row = QHBoxLayout()
        button_row.addStretch()
        self.copy_button = QPushButton("📋 Copy")
        self.copy_button.setToolTip("Copy revised text to clipboard")
        self.copy_button.clicked.connect(self.copy_revised_text)
        self.copy_button.setEnabled(False)
        button_row.addWidget(self.copy_button)
        output_layout.addLayout(button_row)
        
        # Revised text area
        self.revised_view = QTextEdit()
        self.revised_view.setFont(QFont(self.default_font_family, self.default_font_size))
        self.revised_view.setPlaceholderText("Revised text will appear here...")
        self.revised_view.setReadOnly(True)
        self.set_line_spacing(self.revised_view, self.line_spacing)
        output_layout.addWidget(self.revised_view)
        
        output_panel.setLayout(output_layout)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.input_box)
        splitter.addWidget(output_panel)
        splitter.setSizes([SPLITTER_LEFT_SIZE, SPLITTER_RIGHT_SIZE])
        layout.addWidget(splitter)

    def set_line_spacing(self, text_edit: QTextEdit, percent: int) -> None:
        block_format = QTextBlockFormat()
        block_format.setLineHeight(
            percent, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
        )
        cursor = text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(block_format)
        text_edit.setTextCursor(cursor)

    def setup_control_panel(self, layout: QVBoxLayout) -> None:
        # Model selection and Temperature control in one line
        model_temp_layout = QHBoxLayout()

        # Model selection (left-aligned)
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_CHOICES)
        self.model_combo.setToolTip("Select the AI model to use for text improvement")
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()

        # Temperature control (right-aligned)
        temp_layout = QHBoxLayout()
        temp_layout.addStretch()
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(TEMPERATURE_MIN, TEMPERATURE_MAX)
        self.temperature_slider.setValue(int(self.temperature * 100))
        self.temperature_slider.setToolTip(
            "Adjust the creativity of the AI (higher values = more creative)"
        )
        temp_layout.addWidget(self.temperature_slider)
        self.temp_label = QLabel(f"{int(self.temperature * 100)}%")
        temp_layout.addWidget(self.temp_label)

        # Add both layouts to the main horizontal layout
        model_temp_layout.addLayout(model_layout)
        model_temp_layout.addLayout(temp_layout)

        layout.addLayout(model_temp_layout)

        # Options
        self.remove_footnotes_checkbox = QCheckBox("Remove Footnotes")
        self.remove_footnotes_checkbox.setChecked(True)
        self.remove_footnotes_checkbox.setToolTip(
            "Remove footnotes from the input text before processing"
        )
        layout.addWidget(self.remove_footnotes_checkbox)

        # Improve button
        self.improve_button = QPushButton("Improve Writing")
        self.improve_button.setToolTip("Process and improve the input text")
        layout.addWidget(self.improve_button)

        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setToolTip("Clear both input and output text areas")
        layout.addWidget(self.clear_button)

        # Loading indicator
        self.loading_label = QLabel()
        self.loading_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.loading_label.hide()
        layout.addWidget(self.loading_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Cost estimate
        self.cost_estimate_label = QLabel("Estimated cost: $0.00\nEstimated tokens: 0")
        layout.addWidget(self.cost_estimate_label)

        # Session cost tracker
        self.session_cost_label = QLabel("Session total: $0.00 (0 requests)")
        self.session_cost_label.setStyleSheet("QLabel { color: #0066cc; font-weight: bold; }")
        layout.addWidget(self.session_cost_label)

        # Text statistics
        stats_layout = QHBoxLayout()
        self.word_count_label = QLabel("Words: 0")
        self.char_count_label = QLabel("Characters: 0")
        self.output_stats_label = QLabel("Output: 0 words, 0 chars")
        stats_layout.addWidget(self.word_count_label)
        stats_layout.addWidget(self.char_count_label)
        stats_layout.addWidget(self.output_stats_label)
        layout.addLayout(stats_layout)

        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def connect_signals(self):
        self.temperature_slider.valueChanged.connect(self.update_temperature)
        self.improve_button.clicked.connect(self.logic_handler.on_improve_button_clicked)
        self.clear_button.clicked.connect(self.clear_text_areas)
        self.remove_footnotes_checkbox.stateChanged.connect(
            self.logic_handler.toggle_remove_footnotes
        )

        # Connect LogicHandler signals to UI update methods
        self.logic_handler.update_status.connect(self.status_bar.showMessage)
        self.logic_handler.update_revised_text.connect(self.on_revised_text_updated)
        self.logic_handler.update_progress.connect(self.set_progress)
        self.logic_handler.update_cost_estimate.connect(self.update_cost_estimate_display)
        self.logic_handler.session_cost_updated.connect(self.update_session_cost_display)

        # Connect text and model changes with cost recalculations
        self.input_box.textChanged.connect(self.logic_handler.handle_text_changed)
        self.input_box.textChanged.connect(self.update_text_stats)
        self.model_combo.currentTextChanged.connect(self.logic_handler.on_model_changed)

    def update_temperature(self, value: int) -> None:
        self.temperature = value / 100  # Convert to 0-1 range
        self.temp_label.setText(f"{value}%")
        self.logic_handler.temperature = self.temperature

    @pyqtSlot(float, int)
    def update_cost_estimate_display(self, cost, tokens):
        self.cost_estimate_label.setText(
            f"Estimated cost: ${cost:.6f}\n"
            f"Estimated tokens: {tokens}"
        )

    def clear_text_areas(self) -> None:
        self.input_box.clear()
        self.revised_view.clear()
        self.logic_handler.update_cost_estimates()

    def set_progress(self, current: int, total: int) -> None:
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        if current < total:
            self.progress_bar.show()
            # Show loading animation
            model = self.model_combo.currentText()
            self.loading_label.setText(f"⏳ Processing with {model}...")
            self.loading_label.show()
            # Disable buttons during processing
            self.improve_button.setEnabled(False)
            self.clear_button.setEnabled(False)
        else:
            self.progress_bar.hide()
            self.loading_label.hide()
            # Re-enable buttons
            self.improve_button.setEnabled(True)
            self.clear_button.setEnabled(True)

    def update_text_stats(self) -> None:
        text = self.input_box.toPlainText()
        word_count = len(text.split())
        char_count = len(text)
        self.word_count_label.setText(f"Words: {word_count}")
        self.char_count_label.setText(f"Characters: {char_count}")
    
    @pyqtSlot(float, int)
    def update_session_cost_display(self, total_cost: float, request_count: int) -> None:
        self.session_cost_label.setText(
            f"Session total: ${total_cost:.4f} ({request_count} request{'s' if request_count != 1 else ''})"
        )
    
    def on_revised_text_updated(self, text: str) -> None:
        self.revised_view.setText(text)
        self.copy_button.setEnabled(bool(text.strip()))
        # Update output stats
        if text:
            word_count = len(text.split())
            char_count = len(text)
            self.output_stats_label.setText(f"Output: {word_count} words, {char_count} chars")
        else:
            self.output_stats_label.setText("Output: 0 words, 0 chars")
    
    def copy_revised_text(self) -> None:
        text = self.revised_view.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.status_bar.showMessage("Text copied to clipboard!", 2000)
    
    # Legacy drag/drop handlers were replaced by ``DragTextEdit``; retained for
    # backward-compatibility but no longer used.