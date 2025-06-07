# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Application Overview

Writing Assistant is a Next.js web application that enables side-by-side comparison of AI-revised text from OpenAI, Anthropic Claude, and Google Gemini models. Users input text and receive improved versions from three different models simultaneously with visual diff highlighting.

## Development Commands

```bash
# Quick start (from root directory)
./run.sh                    # Automated setup and launch

# Manual development (from writing-assistant-web/)
npm install                 # Install dependencies
npm run dev                 # Start dev server on port 3500
npm run build              # Build for production
npm run start              # Start production server
npm run lint               # Run Next.js linter
npm run generate-models    # Regenerate model config from models.yaml
```

## Architecture

### Model Configuration System
- `models.yaml` (root) → `scripts/generate-models.js` → `lib/model-config.ts`
- The YAML file is the single source of truth for model definitions, pricing, and capabilities
- Running `npm run dev` or `npm run build` automatically regenerates TypeScript config

### State Management Architecture
- **Zustand store** (`lib/store.ts`) manages all application state
- Persisted state: `removeFootnotes`, `temperature`, `sessionCost`, `sessionRequests`
- Session state: `inputText`, `outputs`, `inputCollapsed`
- Each output panel maintains independent model selection and results

### API Route Architecture
- Server-side routes protect API keys: `/api/openai`, `/api/claude`, `/api/gemini`
- Each route handles provider-specific logic (e.g., o1 models don't support temperature)
- Unified request/response interface across all providers

### Component Communication Flow
1. User input → Control Panel → Zustand store
2. Process button → Parallel API calls to selected models
3. API responses → Update individual output panels via store
4. Output panels → Optional diff view transformation

## Key Implementation Details

### Three-Panel Comparison System
- `react-resizable-panels` manages layout with draggable dividers
- Each panel operates independently with its own model selection
- Panels can show raw output or diff view (toggle per panel)

### Diff Visualization
- Uses `diff` npm package for text comparison
- Custom CSS classes in `globals.css` for highlighting:
  - `.diff-added`: Green background for additions
  - `.diff-removed`: Red strikethrough for deletions

### Cost Tracking
- Pre-request estimation based on input tokens and model pricing
- Real-time session tracking stored in localStorage
- Individual request costs displayed per output

### Export Functionality
- Combines all three outputs with headers into single text file
- Includes metadata: models used, timestamps, costs

## Environment Variables

Required in `.env.local`:
```
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
GEMINI_API_KEY=your_key
```

## Common Development Tasks

### Adding a New AI Provider
1. Create new API route in `app/api/[provider]/route.ts`
2. Add provider type to `types/index.ts`
3. Update model configurations in `models.yaml`
4. Implement provider-specific logic in the API route

### Modifying the Prompt
- System prompt is in `lib/constants.ts` as `SYSTEM_PROMPT`
- User instruction prefix is `USER_INSTRUCTION_PREFIX`

### Debugging API Issues
- Check browser console for client-side errors
- Check terminal for server-side API route errors
- Verify API keys are correctly set in `.env.local`

## Type Safety

All types are defined in `types/index.ts`:
- `Model`: Available model identifiers
- `Provider`: API provider types
- `OutputPanel`: Panel state structure
- `AppState`: Complete application state