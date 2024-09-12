import sys
import asyncio
from PyQt6.QtWidgets import (QApplication, QVBoxLayout, QPushButton, QTextEdit, 
                             QWidget, QHBoxLayout, QProgressBar,
                             QComboBox, QLabel, QSplitter)
from PyQt6.QtGui import QFont, QKeyEvent, QTextCursor, QColor, QTextBlockFormat
from PyQt6.QtCore import Qt, pyqtSignal
from openai import OpenAI
from pydantic import BaseModel
from typing import List
from qasync import QEventLoop, asyncSlot
import nltk
nltk.download('punkt', quiet=True)
from nltk.tokenize import sent_tokenize
from text_matcher import TextMatcher

client = OpenAI()

SYSTEM_MESSAGES = {
    "Writing Assistant": "Review the text for clarity and readability. Simplify overly complex sentences. Maintain a formal tone, while also ensuring that the style is engaging and not overly dry or dull. Preserve the author's unique voice while improving the overall flow and style. Favor straightforward language and active voice. Make absolutely sure to not lose any details. Do not shorten when a longer sentence is more stylistically pleasing. Be judicious and do not feel compelling to make unnecessary changes.",
    "General Assistant": "You are a helpful assistant."
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
        self.set_line_spacing(150)  # Set line spacing to 150%

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
        self.setWindowTitle('Improved Writing Assistant')
        self.setGeometry(100, 100, 1500, 900)
        self.font = "Arial"
        self.font_size = 15
        self.line_spacing = 125  # 150% line spacing
        self.text_matcher = TextMatcher()
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(20)  # Increased spacing
        main_layout.setContentsMargins(20, 20, 20, 20)  # Added margins

        # Top controls layout
        top_controls = QHBoxLayout()
        
        # Font size control
        font_control_layout = QHBoxLayout()
        font_size_label = QLabel("Font Size:")
        font_size_label.setFont(QFont(self.font, self.font_size))
        font_control_layout.addWidget(font_size_label)

        self.decrease_font_btn = QPushButton("-")
        self.decrease_font_btn.setFont(QFont(self.font, self.font_size))
        self.decrease_font_btn.clicked.connect(self.decrease_font_size)
        font_control_layout.addWidget(self.decrease_font_btn)

        self.increase_font_btn = QPushButton("+")
        self.increase_font_btn.setFont(QFont(self.font, self.font_size))
        self.increase_font_btn.clicked.connect(self.increase_font_size)
        font_control_layout.addWidget(self.increase_font_btn)

        self.font_size_display = QLabel(str(self.font_size))
        self.font_size_display.setFont(QFont(self.font, self.font_size))
        font_control_layout.addWidget(self.font_size_display)

        top_controls.addLayout(font_control_layout)
        top_controls.addStretch()

        # System message selection
        system_label = QLabel("Select context:")
        system_label.setFont(QFont(self.font, self.font_size))
        self.system_combo = QComboBox()
        self.system_combo.addItems(SYSTEM_MESSAGES.keys())
        self.system_combo.setFont(QFont(self.font, self.font_size))
        self.system_combo.setFixedWidth(200)  # Set a fixed width for the combo box
        top_controls.addWidget(system_label)
        top_controls.addWidget(self.system_combo)

        main_layout.addLayout(top_controls)

        # Create a horizontal splitter for three vertical columns
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # First column: Input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        input_layout.addWidget(QLabel("Enter your text here:"))
        self.input_box = HighlightableTextEdit(self)
        self.input_box.setPlaceholderText("Enter your text here...")
        self.input_box.setFont(QFont(self.font, self.font_size))
        self.input_box.installEventFilter(self)
        input_layout.addWidget(self.input_box)
        splitter.addWidget(input_widget)

        # Second column: Original text view
        original_widget = QWidget()
        original_layout = QVBoxLayout(original_widget)
        original_layout.addWidget(QLabel("Original Text:"))
        self.original_view = HighlightableTextEdit(self)
        self.original_view.setReadOnly(True)
        self.original_view.setFont(QFont(self.font, self.font_size))
        self.original_view.highlighted.connect(self.highlight_sentences)
        original_layout.addWidget(self.original_view)
        splitter.addWidget(original_widget)

        # Third column: Revised text view
        revised_widget = QWidget()
        revised_layout = QVBoxLayout(revised_widget)
        revised_layout.addWidget(QLabel("Improved Text:"))
        self.revised_view = HighlightableTextEdit(self)
        self.revised_view.setReadOnly(True)
        self.revised_view.setFont(QFont(self.font, self.font_size))
        self.revised_view.highlighted.connect(self.highlight_sentences)
        revised_layout.addWidget(self.revised_view)
        splitter.addWidget(revised_widget)

        # Set the initial sizes of the splitter
        splitter.setSizes([int(self.width() * 0.33), int(self.width() * 0.33), int(self.width() * 0.33)])

        main_layout.addWidget(splitter)

        # Add Improve Writing button below the splitter
        self.send_button = QPushButton('Improve Writing', self)
        self.send_button.setFont(QFont(self.font, self.font_size))
        self.send_button.clicked.connect(self.on_send_button_clicked)
        self.send_button.setFixedHeight(40)  # Make the button taller
        main_layout.addWidget(self.send_button)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 1)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        main_layout.addWidget(self.progress_bar)

        self.setLayout(main_layout)

    def eventFilter(self, source, event):
        if (source == self.input_box and event.type() == QKeyEvent.Type.KeyPress 
            and event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier):
            self.on_send_button_clicked()
            return True
        return super().eventFilter(source, event)

    def on_send_button_clicked(self):
        asyncio.ensure_future(self.improve_writing())

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
        self.input_box.setFont(font)
        self.original_view.setFont(font)
        self.revised_view.setFont(font)
        self.font_size_display.setText(str(self.font_size))
        self.font_size_display.setFont(font)
        
        # Update line spacing when font size changes
        self.input_box.set_line_spacing(self.line_spacing)
        self.original_view.set_line_spacing(self.line_spacing)
        self.revised_view.set_line_spacing(self.line_spacing)

    @asyncSlot()
    async def improve_writing(self):
        text = self.input_box.toPlainText()
        if not text:
            self.original_view.setText("Please enter some text to improve.")
            self.revised_view.setText("")
            return

        system_message = SYSTEM_MESSAGES[self.system_combo.currentText()]

        self.progress_bar.show()
        self.progress_bar.setValue(0)

        try:
            completion = await asyncio.to_thread(
                client.beta.chat.completions.parse,
                model="gpt-4o-2024-08-06",
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": f"Improve this text and provide the result as a JSON object: {text}"}
                ],
                response_format=WritingResponse
            )

            result = completion.choices[0].message.parsed

            self.display_texts(result.revisions[0].original, result.revisions[0].revised)

        except Exception as e:
            self.original_view.setText(f"Error: {str(e)}")
            self.revised_view.setText("")

        self.progress_bar.setValue(1)
        self.progress_bar.hide()

    def display_texts(self, original, revised):
        original_sentences, revised_sentences, matches, split_sentences = self.text_matcher.match_texts(original, revised)
        changes = self.text_matcher.analyze_changes(original_sentences, revised_sentences, matches, split_sentences)

        self.original_view.clear()
        self.revised_view.clear()
        
        self.original_view.sentences = []
        self.revised_view.sentences = []
        
        cursor_original = self.original_view.textCursor()
        cursor_revised = self.revised_view.textCursor()
        
        for i, sentence in enumerate(original_sentences):
            start_original = cursor_original.position()
            cursor_original.insertText(sentence + " ")
            end_original = cursor_original.position()
            self.original_view.sentences.append((start_original, end_original))
        
        for j, sentence in enumerate(revised_sentences):
            start_revised = cursor_revised.position()
            cursor_revised.insertText(sentence + " ")
            end_revised = cursor_revised.position()
            self.revised_view.sentences.append((start_revised, end_revised))

        # Clear existing highlights
        self.original_view.setExtraSelections([])
        self.revised_view.setExtraSelections([])

        # Highlight changes
        for change_type, orig_index, rev_index in changes:
            if change_type == "modified":
                self.highlight_text(self.original_view, orig_index, QColor(255, 255, 0, 100))  # Yellow
                self.highlight_text(self.revised_view, rev_index, QColor(255, 255, 0, 100))  # Yellow
            elif change_type == "deleted":
                self.highlight_text(self.original_view, orig_index, QColor(255, 200, 200, 100))  # Light red
            elif change_type == "added":
                self.highlight_text(self.revised_view, rev_index, QColor(200, 255, 200, 100))  # Light green
            elif change_type == "split":
                self.highlight_text(self.original_view, orig_index, QColor(173, 216, 230, 100))  # Light blue
                self.highlight_text(self.revised_view, rev_index, QColor(173, 216, 230, 100))  # Light blue


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
        self.original_view.setExtraSelections([])
        self.revised_view.setExtraSelections([])
        
        if 0 <= index < len(self.original_view.sentences):
            self.highlight_text(self.original_view, index, QColor(173, 216, 230, 100))  # Light blue
        
        if 0 <= index < len(self.revised_view.sentences):
            self.highlight_text(self.revised_view, index, QColor(173, 216, 230, 100))  # Light blue

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('macintosh')
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()