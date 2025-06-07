# Writing Assistant Web App

A modern web application for improving academic writing using AI models from OpenAI, Anthropic, and Google. Get side-by-side comparisons of your text revised by three different AI models simultaneously.

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

## Setup

1. Install dependencies:
```bash
npm install
```

2. Create a `.env.local` file with your API keys:
```
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
GEMINI_API_KEY=your_gemini_key_here
```

3. Run the development server:
```bash
npm run dev
```

4. Open [http://localhost:3000](http://localhost:3000) in your browser

## Usage

1. Paste or type your text in the input panel (or drag and drop a .txt file)
2. Select different AI models for each output panel
3. Adjust temperature for creativity level
4. Toggle "Remove Footnotes" if needed
5. Click "Improve Writing" or press `⌘/Ctrl + Enter`
6. Compare the results and toggle diff view to see changes
7. Copy individual outputs or export all results

## Tech Stack

- **Next.js 14** - React framework with App Router
- **TypeScript** - Type safety
- **Tailwind CSS** - Styling
- **shadcn/ui** - UI components
- **Zustand** - State management
- **react-resizable-panels** - Resizable layout

## Building for Production

```bash
npm run build
npm start
```

## License

MIT