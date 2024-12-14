# logic.py

import asyncio
import re
import json
import logging
from PyQt6.QtCore import QObject, pyqtSignal, Qt, pyqtSlot
from pydantic import BaseModel
from typing import List
from api_calls import (
    get_openai_response,
    get_claude_response,
    get_gemini_response,
)
from config import (
    SYSTEM_MESSAGES,
    MAX_CONTEXT_WINDOW,
    USER_MESSAGE_TEMPLATE,
)  # Imported MAX_CONTEXT_WINDOW
from dataclasses import dataclass
from datetime import datetime

# Configure logging for logic.py
logger = logging.getLogger("logic_handler")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

from token_cost_utils import calculate_cost

class WritingResponse(BaseModel):
    revisions: List[str]


@dataclass
class ProcessingStats:
    start_time: datetime
    paragraphs_processed: int
    total_paragraphs: int
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
    update_cost_estimate = pyqtSignal(
        float, float, int, int, bool
    )  # non_rec_cost, rec_cost, non_rec_tokens, rec_estimated_tokens, recursive_flag

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
            paragraphs_processed=0,
            total_paragraphs=0,
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
            self.stats.paragraphs_processed += 1
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

        # Calculate non-recursive cost
        non_rec_cost_info = self.calculate_cost_estimate(text, model, recursive=False)
        # Calculate recursive cost
        rec_cost_info = self.calculate_cost_estimate(text, model, recursive=True)

        logger.debug(
            f"Cost Estimate - Non-recursive: ${non_rec_cost_info['total_cost']:.6f}, "
            f"Tokens: {non_rec_cost_info['estimated_output_tokens']}; "
            f"Recursive: ${rec_cost_info['total_cost']:.6f}, Tokens: {rec_cost_info['estimated_output_tokens']}"
        )

        # Determine if recursive based on whether recursive cost is greater than 0
        is_recursive = rec_cost_info["total_cost"] > 0.0

        self.update_cost_estimate.emit(
            non_rec_cost_info["total_cost"],
            rec_cost_info["total_cost"],
            non_rec_cost_info["estimated_output_tokens"],
            rec_cost_info["estimated_output_tokens"],
            is_recursive,
        )

    def on_send_button_clicked(self):
        asyncio.create_task(self.improve_writing(recursive=False))

    def on_recursive_button_clicked(self):
        asyncio.create_task(self.improve_writing(recursive=True))

    def toggle_remove_footnotes(self, state):
        self.remove_footnotes_enabled = state == Qt.CheckState.Checked
        self.update_cost_estimates()

    async def improve_writing(self, recursive=False):
        if not self.ui:
            return

        text = self.ui.input_box.toPlainText().strip()
        model = self.ui.model_combo.currentText()
        temperature_value = self.ui.temperature

        if self.remove_footnotes_enabled:
            text = self.remove_footnotes(text)

        # Normalize line endings
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split text into paragraphs on one or more newlines
        paragraphs = [para.strip() for para in re.split(r"\n+", text) if para.strip()]
        total_paras = len(paragraphs)
        self.update_progress.emit(0, total_paras)
        self.update_status.emit("Starting improvement...")

        # Calculate and display cost estimate
        if not recursive:
            non_rec_cost_info = self.calculate_cost_estimate(
                text, model, recursive=False
            )
            rec_cost_info = {"total_cost": 0.0, "estimated_output_tokens": 0}
        else:
            non_rec_cost_info = self.calculate_cost_estimate(
                text, model, recursive=False
            )
            rec_cost_info = self.calculate_cost_estimate(text, model, recursive=True)

        # Determine if recursive based on whether recursive cost is greater than 0
        is_recursive = rec_cost_info["total_cost"] > 0.0

        self.update_cost_estimate.emit(
            non_rec_cost_info["total_cost"],
            rec_cost_info["total_cost"],
            non_rec_cost_info["estimated_output_tokens"],
            rec_cost_info["estimated_output_tokens"],
            is_recursive,
        )

        logger.debug(
            f"Improvement - Recursive: {recursive}, "
            f"Estimated Non-recursive Cost: ${non_rec_cost_info['total_cost']:.6f}, "
            f"Estimated Recursive Cost: ${rec_cost_info['total_cost']:.6f}"
        )

        # Process the text
        if not recursive:
            revised_text = await self.process_non_recursive(
                text, model, temperature_value
            )
        else:
            revised_text = await self.process_recursive(
                paragraphs, model, temperature_value
            )

        self.update_revised_text.emit(revised_text)
        self.update_progress.emit(total_paras, total_paras)
        self.update_status.emit("Improvement completed.")

        # Log the operation
        logging.info(
            f"Improvement completed. Model: {model}, Recursive: {recursive}, "
            f"Estimated cost: ${non_rec_cost_info['total_cost']:.6f} (non-recursive) / "
            f"${rec_cost_info['total_cost']:.6f} (recursive)"
        )

    async def process_non_recursive(self, text, model, temperature):
        try:
            system_message = SYSTEM_MESSAGES["non_recursive"]
            user_message = USER_MESSAGE_TEMPLATE.format(text=text)

            response_content, _, _ = await self.send_api_request(
                user_message, system_message, model, temperature=temperature
            )

            response_json = json.loads(self.strip_code_blocks(response_content))
            result = WritingResponse(**response_json)
            revised_text = "\n\n".join(result.revisions) if result.revisions else text

            with open(
                f"non_recursive_output-{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", "w"
            ) as f:
                f.write(revised_text)

            return revised_text
        except Exception as e:
            self.error_occurred.emit("Response format Error", str(e))
            return "Processing error occurred. Try again."

    async def process_recursive(self, paragraphs, model, temperature):
        max_context = MAX_CONTEXT_WINDOW.get(model, float("inf"))
        system_message = SYSTEM_MESSAGES["recursive"]

        improved_paragraphs = []
        cumulative_context = ""
        for idx, para in enumerate(paragraphs, 1):
            self.update_status.emit(
                f"Processing paragraph {idx} of {len(paragraphs)}..."
            )

            if idx == 1:
                user_message = USER_MESSAGE_TEMPLATE.format(text=para)
            else:
                context_with_current = f"{cumulative_context}\n\n{para}"
                user_message = USER_MESSAGE_TEMPLATE.format(text=context_with_current)

                # Check if the prompt exceeds MAX_CONTEXT_WINDOW
                input_tokens = calculate_cost(
                    model,
                    system_message,
                    user_message,
                    recursive=True,
                )["total_tokens"]

                if input_tokens > max_context:
                    self.update_status.emit(
                        f"Max context window exceeded at paragraph {idx}. Truncating context."
                    )
                    while input_tokens > max_context and improved_paragraphs:
                        _ = improved_paragraphs.pop(0)
                        cumulative_context = "\n\n".join(improved_paragraphs)
                        context_with_current = f"{cumulative_context}\n\n{para}"
                        user_message = USER_MESSAGE_TEMPLATE.format(
                            text=context_with_current
                        )
                        input_tokens = calculate_cost(
                            model,
                            system_message,
                            user_message,
                            recursive=True,
                        )["total_tokens"]
                    if input_tokens > max_context:
                        self.update_status.emit(
                            f"Cannot process paragraph {idx} due to context size."
                        )
                        improved_paragraphs.append(para)
                        continue

            response_content, _, _ = await self.send_api_request(
                user_message, system_message, model, temperature=temperature
            )

            try:
                response_json = json.loads(self.strip_code_blocks(response_content))
                improved_para = response_json["revisions"][-1]
            except (json.JSONDecodeError, IndexError, KeyError) as e:
                self.update_status.emit(f"Error at paragraph {idx}: {e}")
                improved_para = para  # Fallback to original paragraph

            improved_paragraphs.append(improved_para)
            cumulative_context = "\n\n".join(improved_paragraphs)
            self.update_revised_text.emit("\n\n".join(improved_paragraphs))
            self.update_progress.emit(idx, len(paragraphs))
            await asyncio.sleep(0.1)

        with open(
            f"recursive_output-{datetime.now().strftime('%Y%m%d%H%M%S')}.txt", "w"
        ) as f:
            for paragraph in improved_paragraphs:
                f.write(paragraph + "\n")

        return "\n\n".join(improved_paragraphs)

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

    def strip_code_blocks(self, text):
        pattern = r"```json\s*\n(.*?)\n```"
        match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
        if match:
            return match.group(1)
        return text.strip()

    def calculate_cost_estimate(self, text: str, model: str, recursive: bool):
        system_message = (
            SYSTEM_MESSAGES["recursive"]
            if recursive
            else SYSTEM_MESSAGES["non_recursive"]
        )
        cost_info = calculate_cost(model, text, system_message, recursive=recursive)
        logger.debug(
            f"Calculate Cost Estimate - Recursive: {recursive}, Cost Info: {cost_info}"
        )
        return cost_info

    def clean_json_string(self, s):
        # Replace literal newlines and tabs with their escaped versions
        s = s.replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

        # Escape any unescaped quotes
        s = re.sub(r'(?<!\\)"', '\\"', s)

        return s
