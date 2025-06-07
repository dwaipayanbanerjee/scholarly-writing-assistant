# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

This is a PyQt6-based desktop application for improving academic writing using various AI models (OpenAI GPT, Anthropic Claude, Google Gemini). The app provides a split-pane interface where users input text on the left and receive AI-revised text on the right.

## Running the Application

```bash
python main.py
```

## Dependencies

Install dependencies using:
```bash
pip install -r requirements.txt
```

## Environment Configuration

Create a `.env` file with API keys:
```
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key  
GEMINI_API_KEY=your_gemini_key
```

## Architecture

### Core Components

- `main.py` - Application entry point, sets up PyQt6 with qasync event loop
- `src/ui/main_window.py` - MainWindow class defining the PyQt6 interface with split text areas and control panel
- `src/core/logic.py` - LogicHandler class managing business logic, API calls, and Qt signals
- `src/api/api_calls.py` - Async functions for different AI providers (OpenAI, Anthropic, Gemini)
- `src/config/settings.py` - Centralized configuration using Pydantic for validation
- `src/utils/token_cost_utils.py` - Token estimation and cost calculation utilities
- `src/utils/cost_tracker.py` - Cost tracking functionality

### Signal/Slot Architecture

The app uses PyQt6's signal/slot pattern for communication between UI and logic:
- LogicHandler emits signals for status updates, progress, cost estimates, and text updates
- MainWindow connects these signals to UI update methods
- Text changes in UI trigger cost estimation updates via signals

### AI Model Integration

Each AI provider has its own async function in `api_calls.py`:
- OpenAI: Handles both regular models and o1 models (different message format)
- Claude: Uses Anthropic's API with async/await pattern
- Gemini: Uses Google's generative AI SDK

### Cost Calculation

Real-time cost estimation based on:
- Model-specific token costs defined in `settings.py`
- Token estimation using tiktoken or custom estimation
- Live updates as user types or changes models

## Key Features

- Real-time cost estimation as user types
- Footnote removal option with regex patterns
- Temperature control for AI creativity
- Automatic output file saving with timestamps
- Support for multiple AI model providers
- Async processing to keep UI responsive