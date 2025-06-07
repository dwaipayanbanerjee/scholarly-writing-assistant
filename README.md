# Writing Assistant

A modern web application for improving academic writing using AI models from OpenAI, Anthropic, and Google. Get side-by-side comparisons of your text revised by three different AI models simultaneously.

![Writing Assistant](writing-assistant-web/public/screenshot.png)

## Features

- **Three AI Models**: Compare outputs from GPT-4, Claude, and Gemini models side-by-side
- **Visual Diff**: Toggle to see additions and deletions highlighted in each output
- **Collapsible Input**: Maximize screen space for outputs by collapsing the input panel
- **Real-time Cost Tracking**: See estimated costs before processing and track session totals
- **Resizable Panels**: Customize the layout to your preference
- **Export Results**: Download all outputs in a single file
- **Keyboard Shortcuts**: 
  - `⌘/Ctrl + Enter` to process text
  - `⌘/Ctrl + K` to toggle input panel

## Quick Start

### Using the Run Script (Recommended)

Simply run from the root directory:
```bash
./run.sh
```

This script will:
- Kill any existing instances
- Install dependencies if needed
- Start the server
- Open your browser automatically
- Handle cleanup on exit (Ctrl+C)

### Manual Setup

1. Navigate to the web app directory:
```bash
cd writing-assistant-web
```

2. Install dependencies:
```bash
npm install
```

3. Copy the `.env` file to `.env.local` or create a new `.env.local` file with your API keys:
```
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here
```

4. Run the development server:
```bash
npm run dev
```

5. Open [http://localhost:3500](http://localhost:3500) in your browser

## Usage

1. **Input Text**: Paste or type your text in the input panel (or drag and drop a .txt file)
2. **Select Models**: Choose different AI models for each output panel
3. **Adjust Settings**: 
   - Temperature slider for creativity level (0-1)
   - Toggle "Remove Footnotes" if needed
4. **Process**: Click "Improve Writing" or press `⌘/Ctrl + Enter`
5. **Compare Results**: 
   - Toggle diff view to see changes highlighted
   - Green = additions, Red with strikethrough = deletions
6. **Export**: Copy individual outputs or export all results

## Available Models

### OpenAI
- GPT-4 Turbo
- GPT-4
- GPT-3.5 Turbo
- o1-preview
- o1-mini

### Anthropic
- Claude 3 Opus
- Claude 3 Sonnet
- Claude 3 Haiku

### Google
- Gemini 1.5 Pro
- Gemini 1.5 Flash
- Gemini 1.0 Pro

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Zustand** - State management
- **react-resizable-panels** - Resizable layout

## Building for Production

```bash
cd writing-assistant-web
npm run build
npm start
```

## Configuration

### Model Configuration

Model names, pricing, and context windows are configured in `models.yaml` in the root directory. Edit this file to:
- Add new models
- Update pricing
- Change display names
- Set context windows
- Choose default models

After editing `models.yaml`, the configuration will be automatically regenerated when you run the app.

## Development

The app runs on port 3500 by default. To change this, modify the port in `package.json`.

## License

MIT