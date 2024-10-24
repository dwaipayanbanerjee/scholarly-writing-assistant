# main.py
import sys
from PyQt6.QtWidgets import QApplication
from qasync import QEventLoop
from ui import MainWindow
from logic import LogicHandler
import asyncio


def main():
    app = QApplication(sys.argv)

    app.setStyle("Mac")
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    logic_handler = LogicHandler()
    window = MainWindow(logic_handler)
    logic_handler.set_ui(window)  # Set the UI after it's created

    window.show()

    with loop:
        loop.run_forever()


if __name__ == "__main__":
    main()
