import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function removeFootnotes(text: string): string {
  // Remove footnote references like [1], [2], etc.
  let processedText = text.replace(/\[\d+\]/g, '')
  
  // Remove footnote content (lines starting with [1], [2], etc.)
  processedText = processedText.replace(/^\[\d+\].*$/gm, '')
  
  // Remove superscript numbers (common in some formats)
  processedText = processedText.replace(/[\u00B9\u00B2\u00B3\u2074-\u2079]+/g, '')
  
  // Clean up extra whitespace
  processedText = processedText.replace(/\s+/g, ' ').trim()
  
  return processedText
}

export function normalizeLineEndings(text: string): string {
  return text.replace(/\r\n/g, '\n').replace(/\r/g, '\n')
}

export function estimateTokens(text: string): number {
  // Simple estimation: ~4 characters per token
  return Math.ceil(text.length / 4)
}

export function calculateCost(
  inputTokens: number,
  outputTokens: number,
  inputCostPerMillion: number,
  outputCostPerMillion: number
): number {
  return (inputTokens * inputCostPerMillion + outputTokens * outputCostPerMillion) / 1000000
}

export function formatCost(cost: number): string {
  return `$${cost.toFixed(2)}`
}

export function generateOutputFilename(): string {
  const now = new Date()
  const timestamp = now.toISOString().replace(/[:.]/g, '-').slice(0, -5)
  return `output-${timestamp}.txt`
}

export function downloadText(text: string, filename: string) {
  const blob = new Blob([text], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}