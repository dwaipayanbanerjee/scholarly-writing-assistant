'use client'

import { useState, forwardRef, useImperativeHandle } from 'react'
import { Play, RotateCcw, Download } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { useStore } from '@/lib/store'
import { MODEL_CONFIGS } from '@/lib/constants'
import { calculateCost, removeFootnotes, normalizeLineEndings, formatCost, estimateTokens, downloadText, generateOutputFilename } from '@/lib/utils'

export interface ControlPanelRef {
  handleImprove: () => void
}

export const ControlPanel = forwardRef<ControlPanelRef>((props, ref) => {
  const {
    inputText,
    temperature,
    setTemperature,
    removeFootnotes: removeFootnotesEnabled,
    setRemoveFootnotes,
    outputs,
    updateOutput,
    incrementSession,
    sessionCost,
    sessionRequests,
    resetSession
  } = useStore()

  const [isProcessing, setIsProcessing] = useState(false)

  const handleImprove = async () => {
    if (!inputText.trim() || isProcessing) return

    setIsProcessing(true)
    
    // Prepare text
    let processedText = inputText
    if (removeFootnotesEnabled) {
      processedText = removeFootnotes(processedText)
    }
    processedText = normalizeLineEndings(processedText)

    // Process all outputs in parallel
    const promises = outputs.map(async (output) => {
      const modelConfig = MODEL_CONFIGS[output.model]
      
      // Set loading state
      updateOutput(output.id, { loading: true, error: undefined })

      try {
        const response = await fetch(`/api/${modelConfig.provider}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: processedText,
            model: output.model,
            temperature
          })
        })

        const data = await response.json()

        if (!response.ok) {
          throw new Error(data.error || 'Failed to process request')
        }

        const cost = calculateCost(
          data.inputTokens,
          data.outputTokens,
          modelConfig.inputCost,
          modelConfig.outputCost
        )

        updateOutput(output.id, {
          output: data.content,
          cost,
          tokens: {
            input: data.inputTokens,
            output: data.outputTokens
          },
          loading: false
        })

        incrementSession(cost)
      } catch (error: any) {
        updateOutput(output.id, {
          error: error.message,
          loading: false
        })
      }
    })

    await Promise.all(promises)
    setIsProcessing(false)
  }

  // Expose handleImprove to parent component
  useImperativeHandle(ref, () => ({
    handleImprove
  }))

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
    <div className="border rounded-lg p-6 space-y-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Temperature: {temperature}</label>
          <Slider
            value={[temperature]}
            onValueChange={([value]) => setTemperature(value)}
            min={0}
            max={1}
            step={0.1}
            className="w-[200px]"
          />
        </div>

        <div className="flex items-center justify-between">
          <label htmlFor="footnotes" className="text-sm font-medium">
            Remove Footnotes
          </label>
          <Switch
            id="footnotes"
            checked={removeFootnotesEnabled}
            onCheckedChange={setRemoveFootnotes}
          />
        </div>
      </div>

      <div className="space-y-2 text-sm">
        <div className="flex justify-between">
          <span className="text-muted-foreground">Estimated cost:</span>
          <span className="font-medium">{formatCost(estimatedCost)}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-muted-foreground">Session total:</span>
          <span className="font-medium text-primary">
            {formatCost(sessionCost)} ({sessionRequests} requests)
          </span>
        </div>
      </div>

      <div className="flex gap-2">
        <Button
          onClick={handleImprove}
          disabled={!inputText.trim() || isProcessing}
          className="flex-1"
          aria-label="Improve Writing"
        >
          <Play className="mr-2 h-4 w-4" />
          {isProcessing ? 'Processing...' : 'Improve Writing'}
        </Button>
        
        <Button
          variant="outline"
          onClick={handleExport}
          disabled={!outputs.some(o => o.output)}
          title="Export all outputs"
        >
          <Download className="h-4 w-4" />
        </Button>
        
        <Button
          variant="outline"
          onClick={resetSession}
          title="Reset session cost"
        >
          <RotateCcw className="h-4 w-4" />
        </Button>
      </div>
    </div>
  )
})

ControlPanel.displayName = 'ControlPanel'