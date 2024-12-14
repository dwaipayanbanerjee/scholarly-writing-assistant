# logic.py

import asyncio
import re
import logging
from PyQt6.QtCore import QObject, pyqtSignal, Qt, pyqtSlot
from api_calls import (
    get_openai_response,
    get_claude_response,
    get_gemini_response,
)
from config import (
    SYSTEM_MESSAGE,
    USER_MESSAGE_TEMPLATE,
)
from dataclasses import dataclass
from datetime import datetime
from token_cost_utils import calculate_cost

# Configure logging
logger = logging.getLogger("logic_handler")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

@dataclass
class ProcessingStats:
    start_time: datetime
    tokens_processed: int
    total_cost: float
    errors_encountered: int

class LogicHandler(QObject):
    processing_stats_updated = pyqtSignal(ProcessingStats)
    processing_complete = pyqtSignal(ProcessingStats)
    error_occurred = pyqtSignal(str, str)  # error_type, error_message
    update_progress = pyqtSignal(int, int)
    update_status = pyqtSignal(str)
    update_revised_text = pyqtSignal(str)
    update_cost_estimate = pyqtSignal(float, int)  # cost, tokens

    def __init__(self):
        super().__init__()
        self.remove_footnotes_enabled = True
        self.temperature = 0.7
        self.current_model = None
        self.total_cost = 0.0
        self.ui = None
        self.stats = None
        self.processing_cancelled = False

    def start_processing(self):
        """Initialize processing stats"""
        self.stats = ProcessingStats(
            start_time=datetime.now(),
            tokens_processed=0,
            total_cost=0.0,
            errors_encountered=0,
        )
        self.processing_cancelled = False

    def update_processing_stats(self, tokens=0, cost=0.0):
        """Update processing statistics"""
        if self.stats:
            self.stats.tokens_processed += tokens
            self.stats.total_cost += cost
            self.processing_stats_updated.emit(self.stats)

    def cancel_processing(self):
        """Cancel ongoing processing"""
        self.processing_cancelled = True
        self.update_status.emit("Processing cancelled by user")

    def set_ui(self, ui):
        self.ui = ui

    def on_model_changed(self, model):
        self.update_cost_estimates()

    @pyqtSlot()
    def handle_text_changed(self):
        self.update_cost_estimates()

    def update_cost_estimates(self):
        if not self.ui:
            return

        text = self.ui.input_box.toPlainText().strip()
        model = self.ui.model_combo.currentText()

        logger.debug(
            f"Updating cost estimates - Model: {model}, Text Length: {len(text)}"
        )

        cost_info = self.calculate_cost_estimate(text, model)

        logger.debug(
            f"Cost Estimate: ${cost_info['total_cost']:.6f}, "
            f"Tokens: {cost_info['total_tokens']}"
        )

        self.update_cost_estimate.emit(
            cost_info["total_cost"],
            cost_info["total_tokens"]
        )

    def on_improve_button_clicked(self):
        asyncio.create_task(self.improve_writing())

    def toggle_remove_footnotes(self, state):
        self.remove_footnotes_enabled = state == Qt.CheckState.Checked
        self.update_cost_estimates()

    async def improve_writing(self):
        if not self.ui:
            return

        text = self.ui.input_box.toPlainText().strip()
        model = self.ui.model_combo.currentText()
        temperature_value = self.ui.temperature

        if self.remove_footnotes_enabled:
            text = self.remove_footnotes(text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        self.update_progress.emit(0, 1)
        self.update_status.emit("Starting improvement...")

        # Calculate and display cost estimate
        cost_info = self.calculate_cost_estimate(text, model)
        self.update_cost_estimate.emit(
            cost_info["total_cost"],
            cost_info["total_tokens"]
        )

        logger.debug(
            f"Improvement - Estimated Cost: ${cost_info['total_cost']:.6f}, "
            f"Estimated Tokens: {cost_info['total_tokens']}"
        )

        # Process the text
        revised_text = await self.process_text(text, model, temperature_value)
        self.update_revised_text.emit(revised_text)
        self.update_progress.emit(1, 1)
        self.update_status.emit("Improvement completed.")

        # Log the operation
        logging.info(
            f"Improvement completed. Model: {model}, "
            f"Estimated cost: ${cost_info['total_cost']:.6f}"
        )

        # Save the output
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        with open(f"output-{timestamp}.txt", "w") as f:
            f.write(revised_text)

    async def process_text(self, text, model, temperature):
        try:
            user_message = USER_MESSAGE_TEMPLATE.format(text=text)
            response_content, _, _ = await self.send_api_request(
                user_message, SYSTEM_MESSAGE, model, temperature=temperature
            )
            return response_content.strip()
        except Exception as e:
            self.error_occurred.emit("Processing Error", str(e))
            return "Processing error occurred. Try again."

    async def send_api_request(self, prompt, system_message, model, temperature=0.7):
        # Send the API request based on the model
        if model.startswith(("o1-", "gpt-")):
            response = await get_openai_response(
                prompt, system_message, model, temperature=temperature
            )
        elif model.startswith("claude-"):
            response = await get_claude_response(prompt, system_message)
        elif model.startswith("gem"):
            response = await get_gemini_response(prompt, system_message)
        else:
            raise ValueError(f"Unsupported model: {model}")

        return response

    def remove_footnotes(self, text):
        """
        Removes footnotes formatted as [number], [roman numeral], (number), or (roman numeral).
        """
        # Remove [number] or [roman numeral] patterns
        text = re.sub(r"\[(?:\d+|[ivx]+)\]", "", text, flags=re.IGNORECASE)
        # Remove (number) or (roman numeral) patterns
        text = re.sub(r"\((?:\d+|[ivx]+)\)", "", text, flags=re.IGNORECASE)
        # Replace multiple spaces or tabs with a single space
        text = re.sub(r"[ \t]{2,}", " ", text)
        return text.strip()

    def calculate_cost_estimate(self, text: str, model: str):
        """Calculate estimated cost for processing the text."""
        cost_info = calculate_cost(model, text, SYSTEM_MESSAGE)
        logger.debug(f"Calculate Cost Estimate - Cost Info: {cost_info}")
        return cost_info