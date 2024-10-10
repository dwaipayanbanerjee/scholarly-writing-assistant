# ui.py

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
)
from PyQt6.QtGui import QFont, QTextCursor, QTextBlockFormat
from PyQt6.QtCore import Qt, pyqtSlot
from config import MODEL_CHOICES, SYSTEM_MESSAGES


class MainWindow(QMainWindow):
    def __init__(self, logic_handler):
        super().__init__()
        self.logic_handler = logic_handler
        self.default_font_family = "Verdana"
        self.default_font_size = 16
        self.gui_font_size = 10
        self.line_spacing = 120
        self.temperature = 0.7  # Initialize to 0.7 (70%)

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.setWindowTitle("Simplified Writing Assistant")
        self.setMinimumSize(1000, 700)

        main_layout = QVBoxLayout()

        # Text area layout
        text_layout = QHBoxLayout()
        self.setup_text_areas(text_layout)

        # Control panel layout
        control_panel = QGroupBox("Control Panel")
        control_layout = QVBoxLayout()
        self.setup_control_panel(control_layout)
        control_panel.setLayout(control_layout)

        main_layout.addLayout(text_layout, 7)
        main_layout.addWidget(control_panel, 3)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

    def setup_text_areas(self, layout):
        self.input_box = QTextEdit()
        self.input_box.setFont(QFont(self.default_font_family, self.default_font_size))
        self.input_box.setPlaceholderText("Enter your text here...")
        self.set_line_spacing(self.input_box, self.line_spacing)
        self.input_box.setAcceptRichText(False)

        self.revised_view = QTextEdit()
        self.revised_view.setFont(
            QFont(self.default_font_family, self.default_font_size)
        )
        self.revised_view.setPlaceholderText("Revised text will appear here...")
        self.revised_view.setReadOnly(True)
        self.set_line_spacing(self.revised_view, self.line_spacing)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.input_box)
        splitter.addWidget(self.revised_view)
        splitter.setSizes([500, 500])
        layout.addWidget(splitter)

    def set_line_spacing(self, text_edit, percent):
        block_format = QTextBlockFormat()
        block_format.setLineHeight(
            percent, QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
        )
        cursor = text_edit.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(block_format)
        text_edit.setTextCursor(cursor)

    def setup_control_panel(self, layout):
        # Model selection and Temperature control in one line
        model_temp_layout = QHBoxLayout()

        # Model selection (left-aligned)
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Model:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_CHOICES)
        self.model_combo.setToolTip("Select the AI model to use for text improvement")
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()  # This pushes the model selector to the left

        # Temperature control (right-aligned)
        temp_layout = QHBoxLayout()
        temp_layout.addStretch()  # This pushes the temperature control to the right
        temp_layout.addWidget(QLabel("Temperature:"))
        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 100)
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

        # Action buttons
        button_layout = QHBoxLayout()
        self.improve_button = QPushButton("Improve Writing")
        self.improve_button.setToolTip("Process the input text once")
        self.recursive_button = QPushButton("Recursive Improvement")
        self.recursive_button.setToolTip(
            "Process the input text multiple times for deeper improvement"
        )
        button_layout.addWidget(self.improve_button)
        button_layout.addWidget(self.recursive_button)
        layout.addLayout(button_layout)

        # Clear button
        self.clear_button = QPushButton("Clear")
        self.clear_button.setToolTip("Clear both input and output text areas")
        layout.addWidget(self.clear_button)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Cost estimate
        self.cost_label = QLabel(
            "Estimated cost: $0.00 (Non-recursive) / $0.00 (Recursive)"
        )
        layout.addWidget(self.cost_label)

        # Word count
        self.word_count_label = QLabel("Word count: 0")
        layout.addWidget(self.word_count_label)

        # Status bar
        self.status_bar = QStatusBar()
        layout.addWidget(self.status_bar)

    def connect_signals(self):
        # Connect UI elements to LogicHandler methods
        self.remove_footnotes_checkbox.stateChanged.connect(
            self.on_remove_footnotes_changed
        )
        self.temperature_slider.valueChanged.connect(self.update_temperature)
        self.improve_button.clicked.connect(self.logic_handler.on_send_button_clicked)
        self.recursive_button.clicked.connect(
            self.logic_handler.on_recursive_button_clicked
        )
        self.input_box.textChanged.connect(self.update_word_count)
        self.input_box.textChanged.connect(self.logic_handler.calculate_cost_estimate)
        self.model_combo.currentTextChanged.connect(self.logic_handler.on_model_changed)
        self.clear_button.clicked.connect(self.clear_text_areas)

        # Connect LogicHandler signals to UI update methods
        self.logic_handler.update_status.connect(self.status_bar.showMessage)
        self.logic_handler.update_revised_text.connect(self.revised_view.setText)
        self.logic_handler.update_cost_estimate.connect(self.update_cost_estimate)
        self.logic_handler.update_progress.connect(self.set_progress)

    def on_remove_footnotes_changed(self, state):
        self.logic_handler.remove_footnotes_enabled = state == Qt.CheckState.Checked
        self.logic_handler.calculate_cost_estimate()

    def update_temperature(self, value):
        self.temperature = value / 100  # Convert to 0-1 range
        self.temp_label.setText(f"{value}%")
        self.logic_handler.temperature = self.temperature
        self.logic_handler.calculate_cost_estimate()

    @pyqtSlot(float, int, int, float, int, int)
    def update_cost_estimate(
        self,
        non_recursive_cost,
        non_recursive_input_tokens,
        non_recursive_output_tokens,
        recursive_cost,
        recursive_input_tokens,
        recursive_output_tokens,
    ):
        total_input = non_recursive_input_tokens + recursive_input_tokens
        total_output = non_recursive_output_tokens + recursive_output_tokens
        self.cost_label.setText(
            f"Estimated cost: ${non_recursive_cost:.4f} (Non-recursive) / ${recursive_cost:.4f} (Recursive)\n"
            f"Total tokens: {total_input} input, {total_output} output"
        )

    def set_progress(self, current, total):
        self.progress_bar.setRange(0, total)
        self.progress_bar.setValue(current)
        if current < total:
            self.progress_bar.show()
        else:
            self.progress_bar.hide()

    def update_word_count(self):
        text = self.input_box.toPlainText()
        word_count = len(text.split())
        self.word_count_label.setText(f"Word count: {word_count}")

    def clear_text_areas(self):
        self.input_box.clear()
        self.revised_view.clear()
        self.logic_handler.calculate_cost_estimate()
