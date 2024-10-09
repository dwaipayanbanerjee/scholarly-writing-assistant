import sys
import asyncio
import re
import json
from PyQt6.QtWidgets import (
    QApplication,
    QVBoxLayout,
    QPushButton,
    QTextEdit,
    QWidget,
    QHBoxLayout,
    QProgressBar,
    QComboBox,
    QLabel,
    QSlider,
    QSplitter,
    QStatusBar,
    QCheckBox,
)
from PyQt6.QtGui import QFont, QKeyEvent, QTextCursor, QColor, QTextBlockFormat
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from pydantic import BaseModel
from typing import List
from qasync import QEventLoop, asyncSlot
import nltk
from text_matcher import TextMatcher
from api_calls import (
    get_openai_response,
    get_claude_response,
    get_gemini_response,
    calculate_cost,
)


nltk.download("punkt", quiet=True)

from config import MODEL_CHOICES, MAX_OUTPUT_TOKENS, SYSTEM_MESSAGES


class Revision(BaseModel):
    original: str
    revised: str


class WritingResponse(BaseModel):
    revisions: List[Revision]


class HighlightableTextEdit(QTextEdit):
    highlighted = pyqtSignal(int)

    def __init__(self, parent=None, remove_footnotes_func=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.sentences = []
        self.set_line_spacing(120)
        self.remove_footnotes_func = remove_footnotes_func

    def set_line_spacing(self, percent):
        block_format = QTextBlockFormat()
        block_format.setLineHeight(percent, 1)

        cursor = self.textCursor()
        cursor.select(QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(block_format)
        self.setTextCursor(cursor)

    def mouseMoveEvent(self, e):
        cursor = self.cursorForPosition(e.pos())
        for i, (start, end) in enumerate(self.sentences):
            if start <= cursor.position() <= end:
                self.highlighted.emit(i)
                break
        super().mouseMoveEvent(e)

    def insertFromMimeData(self, source):
        if source.hasText():
            text = source.text()
            if self.remove_footnotes_func:
                text = self.remove_footnotes_func(text)
            self.insertPlainText(text)
        else:
            super().insertFromMimeData(source)


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved Writing Assistant")
        self.setGeometry(100, 100, 1500, 900)
        self.font_family = "Verdana"
        self.text_font_size = 23  # Font size for text boxes
        self.gui_font_size = 14  # Consistent font size for GUI elements
        self.line_spacing = 120  # Updated to match set_line_spacing
        self.text_matcher = TextMatcher()
        self.temperature = 70  # Temperature slider value (0-100)
        self.total_cost = 0
        self.setup_ui()
        self.setup_cost_calculation()
        self.setup_token_limits()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        top_controls = self.create_top_controls()
        main_layout.addLayout(top_controls, stretch=0)  # Minimal space

        splitter = self.create_splitter()
        self.splitter = splitter  # Keep a reference to the splitter
        main_layout.addWidget(splitter, stretch=1)  # Expand to take available space

        button_layout = QHBoxLayout()

        self.send_button = QPushButton("Improve Writing", self)
        self.send_button.setFont(QFont(self.font_family, self.gui_font_size))
        self.send_button.clicked.connect(self.on_send_button_clicked)
        self.send_button.setFixedHeight(40)
        button_layout.addWidget(self.send_button)

        self.toggle_input_btn = QPushButton("Toggle Input", self)
        self.toggle_input_btn.setFont(QFont(self.font_family, self.gui_font_size))
        self.toggle_input_btn.clicked.connect(self.toggle_input_visibility)
        self.toggle_input_btn.setFixedHeight(40)
        button_layout.addWidget(self.toggle_input_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout, stretch=0)  # Minimal space

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        self.progress_bar.setFont(QFont(self.font_family, self.gui_font_size))
        main_layout.addWidget(self.progress_bar, stretch=0)  # Minimal space

        # Add estimated tokens display
        self.estimated_tokens_label = QLabel("Estimated tokens: 0")
        self.estimated_tokens_label.setFont(QFont(self.font_family, self.gui_font_size))
        top_controls.addWidget(self.estimated_tokens_label)

        self.setLayout(main_layout)

        # Add status bar
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)

    def setup_token_limits(self):
        self.max_output_tokens = MAX_OUTPUT_TOKENS
        self.model_combo.currentTextChanged.connect(self.update_token_warning)

    def create_top_controls(self):
        top_controls = QHBoxLayout()

        # Font size controls
        font_control = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        font_size_label.setFont(QFont(self.font_family, self.gui_font_size))
        font_control.addWidget(font_size_label)

        self.decrease_font_btn = QPushButton("-")
        self.decrease_font_btn.setFont(QFont(self.font_family, self.gui_font_size))
        self.decrease_font_btn.clicked.connect(self.decrease_font_size)
        font_control.addWidget(self.decrease_font_btn)

        self.increase_font_btn = QPushButton("+")
        self.increase_font_btn.setFont(QFont(self.font_family, self.gui_font_size))
        self.increase_font_btn.clicked.connect(self.increase_font_size)
        font_control.addWidget(self.increase_font_btn)

        self.font_size_display = QLabel(str(self.text_font_size))
        self.font_size_display.setFont(QFont(self.font_family, self.gui_font_size))
        font_control.addWidget(self.font_size_display)

        # Add 'Remove Footnotes' checkbox
        self.remove_footnotes_checkbox = QCheckBox("Remove Footnotes")
        self.remove_footnotes_checkbox.setFont(
            QFont(self.font_family, self.gui_font_size)
        )
        self.remove_footnotes_checkbox.setChecked(True)  # Checked by default
        top_controls.addWidget(self.remove_footnotes_checkbox)
        top_controls.addLayout(font_control)
        top_controls.addStretch()

        # System message selection
        system_label = QLabel("Select context:")
        system_label.setFont(QFont(self.font_family, self.gui_font_size))
        self.system_combo = QComboBox()
        self.system_combo.addItems(SYSTEM_MESSAGES.keys())
        self.system_combo.setFont(QFont(self.font_family, self.gui_font_size))
        self.system_combo.setFixedWidth(200)
        top_controls.addWidget(system_label)
        top_controls.addWidget(self.system_combo)

        # Model selection
        model_label = QLabel("Select model:")
        model_label.setFont(QFont(self.font_family, self.gui_font_size))
        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_CHOICES)
        self.model_combo.setFont(QFont(self.font_family, self.gui_font_size))
        self.model_combo.setFixedWidth(200)
        self.model_combo.setCurrentText("gpt-4o")  # Set default to 'o1-preview'
        top_controls.addWidget(model_label)
        top_controls.addWidget(self.model_combo)

        # Temperature slider
        temp_label = QLabel("Temperature:")
        temp_label.setFont(QFont(self.font_family, self.gui_font_size))
        top_controls.addWidget(temp_label)

        self.temperature_slider = QSlider(Qt.Orientation.Horizontal)
        self.temperature_slider.setRange(0, 100)
        self.temperature_slider.setValue(self.temperature)
        self.temperature_slider.setTickInterval(10)
        self.temperature_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.temperature_slider.valueChanged.connect(self.update_temperature)
        self.temperature_slider.setFixedWidth(150)
        top_controls.addWidget(self.temperature_slider)

        self.temperature_display = QLabel(f"{self.temperature / 100:.2f}")
        self.temperature_display.setFont(QFont(self.font_family, self.gui_font_size))
        top_controls.addWidget(self.temperature_display)

        return top_controls

    def create_splitter(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Input Area
        input_widget = QWidget()
        self.input_widget = input_widget  # Keep a reference for toggling
        input_layout = QVBoxLayout(input_widget)
        input_label = QLabel("Enter your text here:")
        input_label.setFont(QFont(self.font_family, self.gui_font_size))
        input_layout.addWidget(input_label)
        self.input_box = HighlightableTextEdit(
            self, remove_footnotes_func=self.remove_footnotes
        )
        self.input_box.setPlaceholderText("Enter your text here...")
        self.input_box.setFont(QFont(self.font_family, 16))  # Smaller font for input
        self.input_box.installEventFilter(self)
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box)
        splitter.addWidget(input_widget)

        # Original Text View
        original_widget = QWidget()
        original_layout = QVBoxLayout(original_widget)
        original_label = QLabel("Original Text:")
        original_label.setFont(QFont(self.font_family, self.gui_font_size))
        original_layout.addWidget(original_label)
        self.original_view = HighlightableTextEdit(self)
        self.original_view.setReadOnly(True)
        self.original_view.setFont(QFont(self.font_family, self.text_font_size))
        self.original_view.highlighted.connect(self.highlight_sentences)
        original_layout.addWidget(self.original_view)
        splitter.addWidget(original_widget)

        # Revised Text View
        revised_widget = QWidget()
        revised_layout = QVBoxLayout(revised_widget)
        revised_label = QLabel("Improved Text:")
        revised_label.setFont(QFont(self.font_family, self.gui_font_size))
        revised_layout.addWidget(revised_label)
        self.revised_view = HighlightableTextEdit(self)
        self.revised_view.setReadOnly(True)
        self.revised_view.setFont(QFont(self.font_family, self.text_font_size))
        self.revised_view.highlighted.connect(self.highlight_sentences)
        revised_layout.addWidget(self.revised_view)
        splitter.addWidget(revised_widget)

        splitter.setSizes([int(self.width() * 0.33)] * 3)
        return splitter

    def eventFilter(self, source, event):
        if (
            source == self.input_box
            and event.type() == QKeyEvent.Type.KeyPress
            and event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.on_send_button_clicked()
            return True
        return super().eventFilter(source, event)

    @asyncSlot()
    async def on_send_button_clicked(self):
        await self.improve_writing()

    def decrease_font_size(self):
        if self.text_font_size > 8:
            self.text_font_size -= 1
            self.update_font_size()

    def increase_font_size(self):
        if self.text_font_size < 24:
            self.text_font_size += 1
            self.update_font_size()

    def update_font_size(self):
        # Update font for text boxes
        text_font = QFont(self.font_family, self.text_font_size)
        for widget in [self.input_box, self.original_view, self.revised_view]:
            if widget.isVisible():
                widget.setFont(text_font)
                widget.set_line_spacing(self.line_spacing)

        self.font_size_display.setText(str(self.text_font_size))

    def update_temperature(self, value):
        self.temperature = value
        self.temperature_display.setText(f"{self.temperature / 100:.2f}")

    def setup_cost_calculation(self):
        self.input_box.textChanged.connect(self.update_cost_estimate)
        self.model_combo.currentTextChanged.connect(self.update_cost_estimate)

        # Set up a timer to avoid updating too frequently
        self.cost_update_timer = QTimer()
        self.cost_update_timer.setSingleShot(True)
        self.cost_update_timer.timeout.connect(self.update_cost_estimate)

    def update_cost_estimate(self):
        self.cost_update_timer.start(500)  # Wait for 500ms before updating

        text = self.input_box.toPlainText()
        model = self.model_combo.currentText()
        system_message = SYSTEM_MESSAGES[self.system_combo.currentText()]

        (
            estimated_cost,
            estimated_input_tokens,
            estimated_output_tokens,
            total_estimated_tokens,
        ) = calculate_cost(model, text, system_message)

        max_output = self.max_output_tokens.get(model, 0)

        self.estimated_tokens_label.setText(f"Model Max Output: {max_output}")
        self.update_token_warning(model, estimated_output_tokens)

        status_message = f"Est. output tokens: {estimated_output_tokens} | Est. total tokens: {total_estimated_tokens} | Est. cost: ${estimated_cost:.5f}"
        self.status_bar.showMessage(status_message)

    def update_token_warning(self, model, estimated_output_tokens):
        max_output = self.max_output_tokens.get(model, 0)
        warning_threshold = max_output - 1000

        if estimated_output_tokens > warning_threshold:
            self.estimated_tokens_label.setStyleSheet("color: red;")
            warning_message = f"Warning: Estimated output ({estimated_output_tokens}) exceed limit for {model}: {max_output}"
            self.status_bar.showMessage(warning_message)
        else:
            self.estimated_tokens_label.setStyleSheet("")
            # We don't clear the status bar message here, as it's now used to display token and cost estimates

    def update_token_warning(self, model, estimated_tokens=None):
        if estimated_tokens is None:
            estimated_tokens = int(self.estimated_tokens_label.text().split(": ")[1])

        max_output = self.max_output_tokens.get(model, 0)
        warning_threshold = max_output - 1000

        if estimated_tokens > warning_threshold:
            self.estimated_tokens_label.setStyleSheet("color: red;")
            warning_message = f"Warning: Input tokens ({estimated_tokens}) exceed recommended limit for {model} (max output: {max_output})"
            self.status_bar.showMessage(warning_message)
        else:
            self.estimated_tokens_label.setStyleSheet("")
            self.status_bar.clearMessage()

    async def improve_writing(self):
        text = self.input_box.toPlainText().strip()

        if not text:
            self.original_view.setText("Please enter some text to improve.")
            self.revised_view.setText("")
            return

        # Remove footnotes if checkbox is checked
        if self.remove_footnotes_checkbox.isChecked():
            text = self.remove_footnotes(text)

        system_message = SYSTEM_MESSAGES[self.system_combo.currentText()]
        model = self.model_combo.currentText()

        self.progress_bar.show()
        self.progress_bar.setValue(0)

        try:
            temperature_value = self.temperature / 100  # Convert to 0-1 range

            if model.startswith(("o1-", "gpt-")):
                response_content, input_tokens, output_tokens = (
                    await get_openai_response(
                        text, system_message, model, temperature=temperature_value
                    )
                )
            elif model.startswith("claude-"):
                response_content, input_tokens, output_tokens = (
                    await get_claude_response(text, system_message)
                )
            elif model == "gemini-1.5-pro":
                response_content, input_tokens, output_tokens = (
                    await get_gemini_response(text, system_message)
                )
            else:
                raise ValueError(f"Unsupported model: {model}")

            # Calculate and update cost
            cost = calculate_cost(model, text, response_content)[0]
            self.total_cost += cost
            self.update_cost_display(input_tokens, output_tokens, cost)

            self.update_token_warning(model, input_tokens)

            # Strip Markdown code block if present
            response_content = self.strip_code_blocks(response_content)

            response_json = json.loads(response_content)
            result = WritingResponse(**response_json)
            if result.revisions:
                # Combine all revisions into single original and revised texts
                original_combined = "\n\n".join(
                    [rev.original for rev in result.revisions]
                )
                revised_combined = "\n\n".join(
                    [rev.revised for rev in result.revisions]
                )

                self.display_texts(original_combined, revised_combined)
                self.hide_input()
            else:
                raise ValueError("No revisions returned.")
        except json.JSONDecodeError:
            self.original_view.setText("Error: Received invalid JSON from the API.")
            self.revised_view.setText(response_content)
        except Exception as e:
            self.original_view.setText(f"Error: {str(e)}")
            self.revised_view.setText("")

        self.progress_bar.setValue(1)
        self.progress_bar.hide()

    def remove_footnotes(self, text):
        # Remove footnotes in the format [1], [2], etc.
        text = re.sub(r"\[\d+\]", "", text)

        # Remove footnotes in the format (1), (2), etc.
        text = re.sub(r"\(\d+\)", "", text)

        return text

    def update_cost_display(self, input_tokens, output_tokens, cost):
        status_message = (
            f"Input tokens: {input_tokens} | Output tokens: {output_tokens} | "
        )
        status_message += (
            f"Last call cost: ${cost:.5f} | Total session cost: ${self.total_cost:.5f}"
        )
        self.status_bar.showMessage(status_message)

    def strip_code_blocks(self, text):
        """
        Removes Markdown code block wrappers from the response.
        """
        pattern = r"^```json\s*\n(.*)\n```$"
        match = re.match(pattern, text, re.DOTALL)
        if match:
            return match.group(1)
        return text

    def hide_input(self):
        """
        Hides the input_widget and adjusts splitter sizes.
        Sets original and revised views font size to 24.
        """
        self.input_widget.setVisible(False)
        # Adjust splitter sizes: original and revised take equal space
        total_width = self.splitter.width()
        self.splitter.setSizes([0, total_width // 2, total_width // 2])

        # Set font size to 24 for views
        font = QFont(self.font_family, 24)
        for view in [self.original_view, self.revised_view]:
            view.setFont(font)
            view.set_line_spacing(self.line_spacing)

    def show_input(self):
        """
        Shows the input_widget and adjusts splitter sizes.
        Sets input box font to smaller size.
        """
        self.input_widget.setVisible(True)
        # Adjust splitter sizes: input takes 33%, others take 33% each
        total_width = self.splitter.width()
        self.splitter.setSizes([total_width // 3, total_width // 3, total_width // 3])

        # Restore input box font size
        self.input_box.setFont(QFont(self.font_family, 16))

    def toggle_input_visibility(self):
        """
        Toggles the visibility of the input_widget.
        """
        if self.input_widget.isVisible():
            self.hide_input()
        else:
            self.show_input()

    def display_texts(self, original, revised):
        original_paragraphs, revised_paragraphs, matches, split_sentences = (
            self.text_matcher.match_texts(original, revised)
        )

        changes = self.text_matcher.analyze_changes(
            original_paragraphs, revised_paragraphs, matches, split_sentences
        )

        self.populate_text_edit(self.original_view, original_paragraphs)
        self.populate_text_edit(self.revised_view, revised_paragraphs)

        self.original_view.setExtraSelections([])
        self.revised_view.setExtraSelections([])

        for change_type, orig_index, rev_index in changes:
            if change_type == "modified":
                self.highlight_text(
                    self.original_view, orig_index, QColor(255, 255, 0, 100)
                )  # Yellow
                self.highlight_text(
                    self.revised_view, rev_index, QColor(255, 255, 0, 100)
                )
            elif change_type == "deleted":
                self.highlight_text(
                    self.original_view, orig_index, QColor(255, 200, 200, 100)
                )  # Light red
            elif change_type == "added":
                self.highlight_text(
                    self.revised_view, rev_index, QColor(200, 255, 200, 100)
                )  # Light green
            elif change_type == "split":
                self.highlight_text(
                    self.original_view, orig_index, QColor(173, 216, 230, 100)
                )  # Light blue
                self.highlight_text(
                    self.revised_view, rev_index, QColor(173, 216, 230, 100)
                )

    def populate_text_edit(self, text_edit, paragraphs):
        text_edit.clear()
        text_edit.sentences = []
        cursor = text_edit.textCursor()
        for paragraph in paragraphs:
            for sentence in paragraph:
                start = cursor.position()
                if isinstance(sentence, list):
                    sentence = " ".join(sentence)
                cursor.insertText(sentence + " ")
                end = cursor.position()
                text_edit.sentences.append((start, end))
            cursor.insertBlock()  # Insert a new block (paragraph) after each paragraph
            cursor.insertText("\n")  # Add an extra line break between paragraphs

    def highlight_text(self, text_edit, index, color):
        if 0 <= index < len(text_edit.sentences):
            start, end = text_edit.sentences[index]
            selection = QTextEdit.ExtraSelection()
            selection.format.setBackground(color)
            cursor = text_edit.textCursor()
            cursor.setPosition(start)
            cursor.setPosition(end, QTextCursor.MoveMode.KeepAnchor)
            selection.cursor = cursor
            text_edit.setExtraSelections(text_edit.extraSelections() + [selection])

    def highlight_sentences(self, index):
        self.clear_highlights()
        color = QColor(173, 216, 230, 100)  # Light blue
        for view in [self.original_view, self.revised_view]:
            if 0 <= index < len(view.sentences):
                self.highlight_text(view, index, color)

    def clear_highlights(self):
        for view in [self.original_view, self.revised_view]:
            view.setExtraSelections([])


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
