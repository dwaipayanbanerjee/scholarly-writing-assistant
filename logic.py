# logic.py

import asyncio
import re
import json
import logging  # Import logging
from PyQt6.QtCore import QObject, pyqtSignal, Qt
from pydantic import BaseModel
from typing import List
from api_calls import (
    get_openai_response,
    get_claude_response,
    get_gemini_response,
)
from config import SYSTEM_MESSAGES
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

from token_cost_utils import calculate_cost


class WritingResponse(BaseModel):
    revisions: List[str]


class LogicHandler(QObject):
    update_progress = pyqtSignal(int, int)
    update_status = pyqtSignal(str)
    update_revised_text = pyqtSignal(str)
    update_cost_estimate = pyqtSignal(float, int, int, float, int, int)

    def __init__(self):
        super().__init__()
        self.remove_footnotes_enabled = True
        self.temperature = 0.7
        self.current_model = None
        self.total_cost = 0.0  # Initialize total_cost

    def set_ui(self, ui):
        self.ui = ui

    def on_model_changed(self, model):
        self.current_model = model
        self.calculate_cost_estimate()

    def on_send_button_clicked(self):
        asyncio.create_task(self.improve_writing(recursive=False))

    def on_recursive_button_clicked(self):
        asyncio.create_task(self.improve_writing(recursive=True))

    def toggle_remove_footnotes(self, state):
        self.remove_footnotes_enabled = state == Qt.CheckState.Checked
        self.calculate_cost_estimate()

    def calculate_cost_estimate(self):
        if not self.ui:
            return

        text = self.ui.input_box.toPlainText().strip()
        model = self.ui.model_combo.currentText()
        system_message = SYSTEM_MESSAGES["non_recursive"]

        non_recursive_cost, non_recursive_tokens = calculate_cost(
            model, text, system_message, recursive=False
        )
        recursive_cost, recursive_tokens = calculate_cost(
            model, text, system_message, recursive=True
        )

        self.update_cost_estimate.emit(
            non_recursive_cost,
            non_recursive_tokens["input_tokens"],
            non_recursive_tokens["output_tokens"],
            recursive_cost,
            recursive_tokens["input_tokens"],
            recursive_tokens["output_tokens"],
        )

    async def improve_writing(self, recursive=False):
        if not self.ui:
            return

        text = self.ui.input_box.toPlainText().strip()

        if not text:
            self.update_revised_text.emit("Please enter some text to improve.")
            return

        if self.remove_footnotes_enabled:
            text = self.remove_footnotes(text)

        model = self.ui.model_combo.currentText()
        temperature_value = self.ui.temperature

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split text into paragraphs on one or more newlines
        paragraphs = [para.strip() for para in re.split(r"\n+", text) if para.strip()]
        total_paras = len(paragraphs)
        self.update_progress.emit(0, total_paras)
        self.update_status.emit("Starting improvement...")

        total_cost, token_counts = calculate_cost(model, text, recursive=recursive)

        if not recursive:
            revised_text = await self.process_non_recursive(
                text, model, temperature_value
            )
        else:
            revised_text = await self.process_recursive(
                paragraphs, model, temperature_value
            )

        self.total_cost += total_cost
        self.update_cost_estimate.emit(
            self.total_cost,
            token_counts["input_tokens"],
            token_counts["output_tokens"],
            self.total_cost if recursive else 0,
            token_counts["input_tokens"],
            token_counts["output_tokens"],
        )

        self.update_revised_text.emit(revised_text)
        self.update_progress.emit(total_paras, total_paras)
        self.update_status.emit("Improvement completed.")

    async def process_non_recursive(self, text, model, temperature):

        system_message = SYSTEM_MESSAGES["non_recursive"]

        response_content, _, _ = await self.send_api_request(
            text, system_message, model, temperature=temperature
        )

        response_json = json.loads(self.strip_code_blocks(response_content))
        result = WritingResponse(**response_json)
        revised_text = "\n\n".join(result.revisions) if result.revisions else text

        return revised_text

    async def process_recursive(self, paragraphs, model, temperature):
        improved_paragraphs = []

        for idx, para in enumerate(paragraphs, 1):
            self.update_status.emit(
                f"Processing paragraph {idx} of {len(paragraphs)}..."
            )

            cumulative_text = "\n\n".join(improved_paragraphs + [para])

            if idx == 1:
                system_message = SYSTEM_MESSAGES["non_recursive"]
            else:
                system_message = SYSTEM_MESSAGES["recursive"]

            response_content, _, _ = await self.send_api_request(
                cumulative_text, system_message, model, temperature=temperature
            )

            try:
                response_json = json.loads(self.strip_code_blocks(response_content))
                result = WritingResponse(**response_json)
                improved_para = result.revisions[0] if result.revisions else para

            except (json.JSONDecodeError, IndexError) as e:
                self.update_status.emit(f"JSON parsing error at paragraph {idx}: {e}")
                logging.error(f"Error parsing JSON for Paragraph {idx}: {e}")
                improved_para = para  # Fallback to original paragraph

            improved_paragraphs.append(improved_para)

            revised_text = "\n\n".join(improved_paragraphs)
            self.update_revised_text.emit(revised_text)
            self.update_progress.emit(idx, len(paragraphs))
            await asyncio.sleep(0.1)

        return revised_text

    async def send_api_request(self, prompt, system_message, model, temperature=0.7):
        # Create a timestamp for the log file name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file_name = f"api_request_log_{timestamp}.json"

        # Send the API request based on the model
        if model.startswith(("o1-", "gpt-")):
            response = await get_openai_response(
                prompt, system_message, model, temperature=temperature
            )
        elif model.startswith("claude-"):
            response = await get_claude_response(prompt, system_message)
        elif model == "gemini-1.5-pro":
            response = await get_gemini_response(prompt, system_message)
        else:
            raise ValueError(f"Unsupported model: {model}")

        # Prepare the output data
        logging_data = {
            "timestamp": timestamp,
            "model": model,
            "temperature": temperature,
            "system_message": system_message,
            "prompt": prompt,
            "response": response,
        }

        # Write the input and output to a JSON file
        with open(log_file_name, "w") as log_file:
            json.dump(logging_data, log_file, indent=2)

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

    def strip_code_blocks(self, text):
        pattern = r"```json\s*\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return text.strip()
