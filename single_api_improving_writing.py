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
    QSplitter,
)
from PyQt6.QtGui import QFont, QKeyEvent, QTextCursor, QColor, QTextBlockFormat
from PyQt6.QtCore import Qt, pyqtSignal
from pydantic import BaseModel
from typing import List
from qasync import QEventLoop, asyncSlot
import nltk
from text_matcher import TextMatcher
from api_calls import get_openai_response  # Importing only necessary API call

nltk.download("punkt", quiet=True)

SYSTEM_MESSAGES = {
    "Writing Assistant": (
        "Review the text for clarity and readability. Simplify overly complex sentences. "
        "Maintain a formal tone, while also ensuring that the style is engaging and not overly dry or dull. "
        "Preserve the author's unique voice while improving the overall flow and style. "
        "Favor straightforward language and active voice. Make absolutely sure to not lose any details. "
        "Do not shorten when a longer sentence is more stylistically pleasing. "
        "Be judicious and do not feel compelled to make unnecessary changes. "
        'Respond with a JSON object following the schema: {"revisions": [{"original": "...", "revised": "..."}]} '
        "Do not include any Markdown formatting or code blocks."
    ),
    "General Assistant": "You are a helpful assistant.",
}


class Revision(BaseModel):
    original: str
    revised: str


class WritingResponse(BaseModel):
    revisions: List[Revision]


class HighlightableTextEdit(QTextEdit):
    highlighted = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.sentences = []
        self.set_line_spacing(150)

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


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Improved Writing Assistant")
        self.setGeometry(100, 100, 1500, 900)
        self.font = "Arial"
        self.font_size = 15
        self.line_spacing = 150  # Updated to match set_line_spacing
        self.text_matcher = TextMatcher()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        top_controls = self.create_top_controls()
        main_layout.addLayout(top_controls)

        splitter = self.create_splitter()
        self.splitter = splitter  # Keep a reference to the splitter
        main_layout.addWidget(splitter)

        button_layout = QHBoxLayout()

        self.send_button = QPushButton("Improve Writing", self)
        self.send_button.setFont(QFont(self.font, self.font_size))
        self.send_button.clicked.connect(self.on_send_button_clicked)
        self.send_button.setFixedHeight(40)
        button_layout.addWidget(self.send_button)

        self.toggle_input_btn = QPushButton("Toggle Input", self)
        self.toggle_input_btn.setFont(QFont(self.font, self.font_size))
        self.toggle_input_btn.clicked.connect(self.toggle_input_visibility)
        self.toggle_input_btn.setFixedHeight(40)
        button_layout.addWidget(self.toggle_input_btn)

        button_layout.addStretch()
        main_layout.addLayout(button_layout)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)

    def create_top_controls(self):
        top_controls = QHBoxLayout()

        # Font size controls
        font_control = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        font_size_label.setFont(QFont(self.font, self.font_size))
        font_control.addWidget(font_size_label)

        self.decrease_font_btn = QPushButton("-")
        self.decrease_font_btn.setFont(QFont(self.font, self.font_size))
        self.decrease_font_btn.clicked.connect(self.decrease_font_size)
        font_control.addWidget(self.decrease_font_btn)

        self.increase_font_btn = QPushButton("+")
        self.increase_font_btn.setFont(QFont(self.font, self.font_size))
        self.increase_font_btn.clicked.connect(self.increase_font_size)
        font_control.addWidget(self.increase_font_btn)

        self.font_size_display = QLabel(str(self.font_size))
        self.font_size_display.setFont(QFont(self.font, self.font_size))
        font_control.addWidget(self.font_size_display)

        top_controls.addLayout(font_control)
        top_controls.addStretch()

        # System message selection
        system_label = QLabel("Select context:")
        system_label.setFont(QFont(self.font, self.font_size))
        self.system_combo = QComboBox()
        self.system_combo.addItems(SYSTEM_MESSAGES.keys())
        self.system_combo.setFont(QFont(self.font, self.font_size))
        self.system_combo.setFixedWidth(200)
        top_controls.addWidget(system_label)
        top_controls.addWidget(self.system_combo)

        return top_controls

    def create_splitter(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Input Area
        input_widget = QWidget()
        self.input_widget = input_widget  # Keep a reference for toggling
        input_layout = QVBoxLayout(input_widget)
        input_layout.addWidget(QLabel("Enter your text here:"))
        self.input_box = HighlightableTextEdit(self)
        self.input_box.setPlaceholderText("Enter your text here...")
        self.input_box.setFont(QFont(self.font, self.font_size))
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box)
        splitter.addWidget(input_widget)

        # Original Text View
        original_widget = QWidget()
        original_layout = QVBoxLayout(original_widget)
        original_layout.addWidget(QLabel("Original Text:"))
        self.original_view = HighlightableTextEdit(self)
        self.original_view.setReadOnly(True)
        self.original_view.setFont(QFont(self.font, self.font_size))
        self.original_view.highlighted.connect(self.highlight_sentences)
        original_layout.addWidget(self.original_view)
        splitter.addWidget(original_widget)

        # Revised Text View
        revised_widget = QWidget()
        revised_layout = QVBoxLayout(revised_widget)
        revised_layout.addWidget(QLabel("Improved Text:"))
        self.revised_view = HighlightableTextEdit(self)
        self.revised_view.setReadOnly(True)
        self.revised_view.setFont(QFont(self.font, self.font_size))
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
        if self.font_size > 8:
            self.font_size -= 1
            self.update_font_size()

    def increase_font_size(self):
        if self.font_size < 24:
            self.font_size += 1
            self.update_font_size()

    def update_font_size(self):
        font = QFont(self.font, self.font_size)
        for widget in [
            self.input_box,
            self.original_view,
            self.revised_view,
            self.font_size_display,
        ]:
            widget.setFont(font)

        # Update line spacing
        for widget in [self.input_box, self.original_view, self.revised_view]:
            widget.set_line_spacing(self.line_spacing)

        self.font_size_display.setText(str(self.font_size))

    async def improve_writing(self):
        text = self.input_box.toPlainText().strip()
        if not text:
            self.original_view.setText("Please enter some text to improve.")
            self.revised_view.setText("")
            return

        system_message = SYSTEM_MESSAGES[self.system_combo.currentText()]

        self.progress_bar.show()
        self.progress_bar.setValue(0)

        try:
            response_content = await get_openai_response(text, system_message)
            # Strip Markdown code block if present
            response_content = self.strip_code_blocks(response_content)
            response_json = json.loads(response_content)
            result = WritingResponse(**response_json)
            if result.revisions:
                revision = result.revisions[0]
                self.display_texts(revision.original, revision.revised)
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
        """
        self.input_widget.setVisible(False)
        # Adjust splitter sizes: original and revised take equal space
        total_width = self.splitter.width()
        self.splitter.setSizes([0, total_width // 2, total_width // 2])

    def show_input(self):
        """
        Shows the input_widget and adjusts splitter sizes.
        """
        self.input_widget.setVisible(True)
        # Adjust splitter sizes: input takes 33%, others take 33% each
        total_width = self.splitter.width()
        self.splitter.setSizes([total_width // 3, total_width // 3, total_width // 3])

    def toggle_input_visibility(self):
        """
        Toggles the visibility of the input_widget.
        """
        if self.input_widget.isVisible():
            self.hide_input()
        else:
            self.show_input()

    def display_texts(self, original, revised):
        original_sentences, revised_sentences, matches, split_sentences = (
            self.text_matcher.match_texts(original, revised)
        )
        changes = self.text_matcher.analyze_changes(
            original_sentences, revised_sentences, matches, split_sentences
        )

        self.populate_text_edit(self.original_view, original_sentences)
        self.populate_text_edit(self.revised_view, revised_sentences)

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

    def populate_text_edit(self, text_edit, sentences):
        text_edit.clear()
        text_edit.sentences = []
        cursor = text_edit.textCursor()
        for sentence in sentences:
            start = cursor.position()
            cursor.insertText(sentence + " ")
            end = cursor.position()
            text_edit.sentences.append((start, end))

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
    app.setStyle("macintosh")
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()
