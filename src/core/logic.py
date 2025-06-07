# logic.py

import asyncio
# Centralised logger
from src.utils.logger import logger
from typing import Optional, Dict, Any

from PyQt6.QtCore import QObject, pyqtSignal, Qt, pyqtSlot

from src.api.api_calls import (
    get_openai_response,
    get_claude_response,
    get_gemini_response,
)
from src.config.config import (
    SYSTEM_MESSAGE,
    USER_MESSAGE_TEMPLATE,
)
from src.utils.token_cost_utils import calculate_cost, calculate_cost_from_usage
from src.config.constants import DEFAULT_TEMPERATURE
from src.utils.formatters import remove_footnotes, normalize_line_endings, generate_output_filename
from src.utils.validators import is_supported_model

# (handlers configured globally in utils.logger)

class LogicHandler(QObject):
    update_progress = pyqtSignal(int, int)
    update_status = pyqtSignal(str)
    update_revised_text = pyqtSignal(str)
    update_cost_estimate = pyqtSignal(float, int)  # cost, tokens
    session_cost_updated = pyqtSignal(float, int)  # total_cost, request_count

    def __init__(self) -> None:
        super().__init__()
        self.remove_footnotes_enabled = True
        self.temperature = DEFAULT_TEMPERATURE
        self.ui: Optional[Any] = None  # Will be MainWindow type
        self.session_cost = 0.0
        self.session_request_count = 0

    def set_ui(self, ui: Any) -> None:  # ui is MainWindow but avoid circular import
        self.ui = ui

    def on_model_changed(self, model: str) -> None:
        self.update_cost_estimates()

    @pyqtSlot()
    def handle_text_changed(self) -> None:
        self.update_cost_estimates()

    def update_cost_estimates(self) -> None:
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

    def on_improve_button_clicked(self) -> None:
        asyncio.create_task(self.improve_writing())

    def toggle_remove_footnotes(self, state: Qt.CheckState) -> None:
        self.remove_footnotes_enabled = state == Qt.CheckState.Checked
        self.update_cost_estimates()

    async def improve_writing(self) -> None:
        if not self.ui:
            return

        text = self.ui.input_box.toPlainText().strip()
        model = self.ui.model_combo.currentText()
        temperature_value = self.ui.temperature

        if self.remove_footnotes_enabled:
            text = remove_footnotes(text)

        # Normalize line endings
        text = normalize_line_endings(text)

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
        revised_text, actual_cost = await self.process_text(text, model, temperature_value)
        self.update_revised_text.emit(revised_text)
        self.update_progress.emit(1, 1)
        self.update_status.emit("Improvement completed.")
        
        # Update session cost
        self.session_cost += actual_cost
        self.session_request_count += 1
        self.session_cost_updated.emit(self.session_cost, self.session_request_count)

        # Log the operation
        logger.info(
            f"Improvement completed. Model: {model}, "
            f"Estimated cost: ${cost_info['total_cost']:.6f}"
        )

        # Save the output
        filename = generate_output_filename()
        with open(filename, "w") as f:
            f.write(revised_text)

    async def process_text(self, text: str, model: str, temperature: float) -> tuple[str, float]:
        try:
            user_message = USER_MESSAGE_TEMPLATE.format(text=text)
            response_content, input_tokens, output_tokens = await self.send_api_request(
                user_message, SYSTEM_MESSAGE, model, temperature=temperature
            )
            actual_cost = calculate_cost_from_usage(model, input_tokens, output_tokens)
            return response_content.strip(), actual_cost
        except Exception as e:
            logger.error(f"Processing error: {str(e)}")
            return "Processing error occurred. Try again.", 0.0

    async def send_api_request(self, prompt: str, system_message: str, model: str, temperature: float = DEFAULT_TEMPERATURE) -> tuple:
        # Send the API request based on the model
        if not is_supported_model(model):
            raise ValueError(f"Unsupported model: {model}")
            
        if model.startswith(("o1-", "gpt-")):
            response = await get_openai_response(
                prompt, system_message, model, temperature=temperature
            )
        elif model.startswith("claude-"):
            response = await get_claude_response(prompt, system_message, model, temperature=temperature)
        elif model.startswith("gem"):
            response = await get_gemini_response(prompt, system_message, model, temperature=temperature)

        return response


    def calculate_cost_estimate(self, text: str, model: str) -> Dict[str, Any]:
        """Calculate estimated cost for processing the text."""
        cost_info = calculate_cost(model, text, SYSTEM_MESSAGE)
        logger.debug(f"Calculate Cost Estimate - Cost Info: {cost_info}")
        return cost_info