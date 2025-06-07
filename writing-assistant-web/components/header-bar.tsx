'use client'

import { Play, Download, RotateCcw, Info } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { SettingsDialog } from '@/components/settings-dialog'
import { useStore } from '@/lib/store'
import { MODEL_CONFIGS } from '@/lib/constants'
import { formatCost, estimateTokens, calculateCost, downloadText, generateOutputFilename } from '@/lib/utils'

interface HeaderBarProps {
  onSubmit: () => void
  isProcessing: boolean
}

export function HeaderBar({ onSubmit, isProcessing }: HeaderBarProps) {
  const { inputText, outputs, sessionCost, sessionRequests } = useStore()

  const handleExport = () => {
    const content = outputs
      .filter(o => o.output)
      .map(o => {
        const config = MODEL_CONFIGS[o.model]
        return `=== ${config.name} ===\n\n${o.output}\n`
      })
      .join('\n' + '='.repeat(50) + '\n\n')

    downloadText(content, generateOutputFilename())
  }

  // Calculate estimated cost
  const estimatedTokens = estimateTokens(inputText)
  const estimatedCost = outputs.reduce((total, output) => {
    const config = MODEL_CONFIGS[output.model]
    return total + calculateCost(estimatedTokens, estimatedTokens, config.inputCost, config.outputCost)
  }, 0)

  return (
    <header className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex items-center justify-between px-4 py-2">
        <div className="flex items-center gap-4">
          <h1 className="text-lg font-semibold">Writing Assistant</h1>
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            {inputText && (
              <>
                <span>Est. {formatCost(estimatedCost)}</span>
                <span>•</span>
              </>
            )}
            <span>Session: {formatCost(sessionCost)}</span>
            {sessionRequests > 0 && <span>({sessionRequests})</span>}
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            onClick={onSubmit}
            disabled={!inputText.trim() || isProcessing}
            size="sm"
            className="gap-2"
          >
            <Play className="h-3.5 w-3.5" />
            {isProcessing ? 'Processing...' : 'Improve'}
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={handleExport}
            disabled={!outputs.some(o => o.output)}
            title="Export all outputs"
          >
            <Download className="h-3.5 w-3.5" />
          </Button>
          
          <SettingsDialog />
          
          <div className="flex items-center gap-1 text-xs text-muted-foreground border-l pl-2 ml-1">
            <kbd className="px-1 py-0.5 rounded bg-muted text-[10px]">Enter</kbd>
            <span>to submit</span>
          </div>
        </div>
      </div>
    </header>
  )
}