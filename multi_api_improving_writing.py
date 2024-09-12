import sys
import asyncio
from PyQt6.QtWidgets import (QApplication, QVBoxLayout, QPushButton, QTextEdit, 
                             QWidget, QHBoxLayout, QProgressBar,
                             QTabWidget, QComboBox, QLabel, QSplitter)
from PyQt6.QtGui import QFont, QKeyEvent
from PyQt6.QtCore import Qt
from api_calls import get_openai_response, get_claude_response, get_gemini_response
from qasync import QEventLoop, asyncSlot

SYSTEM_MESSAGES = {
    "Writing Assistant": "Review the text for clarity and readability. Simplify overly complex sentences while maintaining the academic tone and rigor. Maintain a formal, academic tone, ensuring that the style is engaging without being overly dry. Preserve the author's unique voice while improving the overall flow and style. Eliminate jargon and unnecessary complexity. Favor straightforward language and active voice.",
    "General Assistant": "You are a helpful assistant."
}

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Multi-API Chat Interface')
        self.setGeometry(100, 100, 900, 900)
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        self.font = ".AppleSystemUIFont"  # Use system font for macOS
        self.font_size = 13  # Standard macOS font size

        # System message selection
        system_layout = QHBoxLayout()
        system_label = QLabel("Select context:")
        system_label.setFont(QFont(self.font, self.font_size))
        self.system_combo = QComboBox()
        self.system_combo.addItems(SYSTEM_MESSAGES.keys())
        self.system_combo.setFont(QFont(self.font, self.font_size))
        system_layout.addWidget(system_label)
        system_layout.addWidget(self.system_combo)
        main_layout.addLayout(system_layout)

        # Create a splitter for input and output areas
        splitter = QSplitter(Qt.Orientation.Vertical)

        # Input area
        input_widget = QWidget()
        input_layout = QVBoxLayout(input_widget)
        self.input_box = QTextEdit(self)
        self.input_box.setPlaceholderText("Enter your query here...")
        self.input_box.setFont(QFont(self.font, self.font_size))
        self.input_box.installEventFilter(self)  # Install event filter for key press events
        input_layout.addWidget(self.input_box)
        self.send_button = QPushButton('Send', self)
        self.send_button.setFont(QFont(self.font, self.font_size))
        self.send_button.clicked.connect(self.on_send_button_clicked)
        input_layout.addWidget(self.send_button)
        splitter.addWidget(input_widget)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 3)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.hide()
        input_layout.addWidget(self.progress_bar)

        # Tab widget for responses
        self.tab_widget = QTabWidget()
        self.tab_widget.setFont(QFont(self.font, self.font_size))
        splitter.addWidget(self.tab_widget)

        # Set the initial sizes of the splitter
        splitter.setSizes([int(self.height() * 0.4), int(self.height() * 0.6)])

        main_layout.addWidget(splitter)

        # Create tabs with separate text boxes
        self.tabs = {}
        for api_name in ["OpenAI GPT-4", "Claude", "Gemini"]:
            tab = QWidget()
            tab_layout = QVBoxLayout(tab)
            result_box = QTextEdit(tab)
            result_box.setReadOnly(True)
            result_box.setFont(QFont(self.font, self.font_size))
            tab_layout.addWidget(result_box)
            self.tab_widget.addTab(tab, api_name)
            self.tabs[api_name] = {"widget": tab, "result_box": result_box}

        self.setLayout(main_layout)

    def eventFilter(self, source, event):
        if (source == self.input_box and event.type() == QKeyEvent.Type.KeyPress 
            and event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.NoModifier):
            asyncio.ensure_future(self.send_query())
            return True
        return super().eventFilter(source, event)

    def on_send_button_clicked(self):
        asyncio.ensure_future(self.send_query())

    @asyncSlot()
    async def send_query(self):
        query = self.input_box.toPlainText()
        if not query:
            for api_name in self.tabs:
                self.tabs[api_name]["result_box"].setText("Please enter a query.")
            return

        system_message = SYSTEM_MESSAGES[self.system_combo.currentText()]

        for api_name in self.tabs:
            self.tabs[api_name]["result_box"].clear()
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        apis = [
            (get_openai_response, "OpenAI GPT-4"),
            (get_claude_response, "Claude"),
            (get_gemini_response, "Gemini")
        ]

        async def wrapped_api_call(api_func, api_name):
            try:
                result = await api_func(query, system_message)
                return api_name, result
            except Exception as e:
                return api_name, f"Error: {str(e)}"

        tasks = [wrapped_api_call(api_func, api_name) for api_func, api_name in apis]
        
        for future in asyncio.as_completed(tasks):
            api_name, result = await future
            self.handle_result(api_name, result)
            self.update_progress()

    def handle_result(self, api_name, result):
        self.tabs[api_name]["result_box"].setText(result)

    def update_progress(self):
        current_value = self.progress_bar.value()
        self.progress_bar.setValue(current_value + 1)
        if current_value + 1 >= 3:
            self.progress_bar.hide()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle('macintosh')
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()

    with loop:
        loop.run_forever()