"""Custom PyQt widgets used by the application."""

from __future__ import annotations

from typing import List

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QTextCursor, QTextBlockFormat, QDragEnterEvent, QDropEvent
from PyQt6.QtWidgets import QTextEdit, QApplication


class DragTextEdit(QTextEdit):
    """QTextEdit subclass with built-in *drag-and-drop* support for *.txt* files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setAcceptDrops(True)

    # ------------------------------------------------------------------
    # Drag & drop events
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event: QDragEnterEvent) -> None:  # noqa: N802
        if event.mimeData().hasUrls() and self._has_txt_file(event.mimeData().urls()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent) -> None:  # noqa: N802
        urls: List[QUrl] = event.mimeData().urls()
        if not urls:
            return

        for url in urls:
            file_path = url.toLocalFile()
            if file_path.endswith(".txt"):
                try:
                    with open(file_path, "r", encoding="utf-8") as fh:
                        self.setText(fh.read())

                    # Update the main window's status bar if present.
                    main_window = self.window()
                    if hasattr(main_window, "status_bar"):
                        main_window.status_bar.showMessage(f"Loaded: {file_path}", 3000)
                except Exception as exc:  # pragma: no cover – rare file errors
                    main_window = self.window()
                    if hasattr(main_window, "status_bar"):
                        main_window.status_bar.showMessage(
                            f"Error loading file: {exc}", 5000
                        )
                finally:
                    break  # Load only the first .txt file

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _has_txt_file(urls: List[QUrl]) -> bool:
        return any(url.toLocalFile().endswith(".txt") for url in urls)
