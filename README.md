# Writing Assistant

A PyQt6-based desktop application for improving academic writing using various AI models (OpenAI GPT, Anthropic Claude, Google Gemini). The app provides a split-pane interface where users input text on the left and receive AI-revised text on the right.

## Features

- **Multi-Model Support**: Choose from various AI models including:
  - Claude 4 Series (Opus, Sonnet)
  - OpenAI GPT-4.1 Series
  - Google Gemini 2.5 Series
  - OpenAI reasoning models (o3-mini, o4-mini-high)
- **Real-time Cost Estimation**: See estimated costs before processing
- **Word Count Tracking**: Monitor document length as you type
- **Footnote Removal**: Optional removal of footnotes before processing
- **Temperature Control**: Adjust AI creativity level
- **Automatic Output Saving**: Processed text is automatically saved with timestamps
- **Responsive UI**: Async processing keeps the interface responsive

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd "Writing Assistant"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your API keys:
```env
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here
```

## Usage

Run the application:
```bash
python main.py
```

### Interface Guide

1. **Input Panel** (Left): Enter or paste your text here
2. **Output Panel** (Right): AI-improved text appears here
3. **Control Panel** (Bottom):
   - **Model Selection**: Choose your preferred AI model
   - **Temperature Slider**: Adjust creativity (0-100%)
   - **Remove Footnotes**: Toggle footnote removal
   - **Improve Writing**: Process your text
   - **Clear**: Reset both panels

## Project Structure

```
Writing Assistant/
├── main.py                 # Application entry point
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── CLAUDE.md              # Claude Code instructions
├── icon.icns              # Application icon
├── .env                   # API keys (create this)
└── src/                   # Source code
    ├── api/               # API integration
    │   ├── api_calls.py   # AI provider interfaces
    │   └── api_clients.py # API client management
    ├── config/            # Configuration
    │   ├── config.py      # Model settings & prompts
    │   └── constants.py   # Application constants
    ├── core/              # Business logic
    │   └── logic.py       # Main application logic
    ├── ui/                # User interface
    │   └── main_window.py # PyQt6 UI components
    └── utils/             # Utilities
        ├── cost_tracker.py    # Usage cost tracking
        ├── formatters.py      # Text formatting
        ├── token_cost_utils.py # Token estimation
        └── validators.py      # Input validation
```

## Architecture

### Signal/Slot Pattern
The application uses PyQt6's signal/slot mechanism for clean separation between UI and business logic:
- `LogicHandler` emits signals for status updates, progress, and results
- `MainWindow` connects these signals to UI update methods

### Async Processing
- API calls are handled asynchronously using `asyncio` and `qasync`
- Keeps the UI responsive during AI processing

### Cost Calculation
- Real-time token estimation based on input text and selected model
- Accurate cost tracking for each API call
- Cumulative cost tracking across sessions

## Configuration

### Models
Available models and their settings are defined in `src/config/config.py`:
- Context window sizes
- Output token limits
- Cost per million tokens

### System Prompt
The AI behavior is controlled by the system prompt in `config.py`. It emphasizes:
- Clarity and precision
- Scholarly tone preservation
- Logical flow enhancement
- Meaning preservation

## API Requirements

### OpenAI
- Supports GPT-4.1 series and reasoning models
- Requires valid OpenAI API key

### Anthropic
- Supports Claude 4 and Claude 3.7 series
- Requires valid Anthropic API key

### Google Gemini
- Supports Gemini 2.5 Pro and Flash
- Requires valid Google AI Studio API key

## Output Files

Processed text is automatically saved to timestamped files:
- Format: `output-YYYYMMDDHHMMSS.txt`
- Location: Application directory

## Troubleshooting

### Common Issues

1. **Module Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version (3.8+ required)

2. **API Key Errors**
   - Verify `.env` file exists and contains valid keys
   - Check API key format and permissions

3. **UI Not Responding**
   - Large texts may take time to process
   - Check console for error messages

### Debug Mode

Run with Python's verbose flag for detailed logging:
```bash
python -v main.py
```

## Development

### Adding New AI Models

1. Add model configuration to `src/config/config.py`:
   - Add to `MODEL_CHOICES`
   - Define in `MAX_OUTPUT_TOKENS`
   - Set costs in `COST_PER_1M_TOKENS`

2. Update model detection in `src/utils/validators.py`

3. Add API integration in `src/api/api_calls.py`

### Code Style

- Type hints are used throughout
- Follow PEP 8 conventions
- Imports organized by: standard library → third-party → local

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]