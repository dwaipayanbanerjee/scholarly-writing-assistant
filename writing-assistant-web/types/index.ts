export type ModelProvider = 'openai' | 'claude' | 'gemini'

export type Model = 
  | 'gpt-4.5-preview'
  | 'gpt-4.1'
  | 'gpt-4o'
  | 'o3'
  | 'claude-opus-4-20250514'
  | 'claude-sonnet-4-20250514'
  | 'gemini-2.5-pro'
  | 'gemini-2.5-flash'
  // Legacy models (kept for compatibility)
  | 'gpt-4-turbo-preview'
  | 'gpt-4'
  | 'gpt-3.5-turbo'
  | 'o1-preview'
  | 'o1-mini'
  | 'claude-3-opus-20240229'
  | 'claude-3-sonnet-20240229'
  | 'claude-3-haiku-20240307'
  | 'gemini-1.5-pro'
  | 'gemini-1.5-flash'
  | 'gemini-1.0-pro'

export interface ModelConfig {
  id: Model
  name: string
  apiModel: string  // actual model name to use with API
  provider: ModelProvider
  inputCost: number  // per 1M tokens
  outputCost: number // per 1M tokens
  maxTokens?: number
  contextWindow?: number // total context window size
}

export interface OutputPanel {
  id: string
  model: Model
  output: string
  cost: number
  tokens: {
    input: number
    output: number
  }
  loading: boolean
  error?: string
}

export interface AppState {
  inputText: string
  inputCollapsed: boolean
  removeFootnotes: boolean
  temperature: number
  outputs: OutputPanel[]
  sessionCost: number
  sessionRequests: number
}