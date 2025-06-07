'use client'

import { useEffect, useState, useCallback } from 'react'
import { Panel, PanelGroup, PanelResizeHandle } from 'react-resizable-panels'
import { InputPanel } from '@/components/input-panel'
import { OutputPanel } from '@/components/output-panel'
import { HeaderBar } from '@/components/header-bar'
import { useStore } from '@/lib/store'
import { MODEL_CONFIGS } from '@/lib/constants'
import { calculateCost, removeFootnotes, normalizeLineEndings } from '@/lib/utils'

export default function HomePage() {
  const {
    inputText,
    inputCollapsed,
    temperature,
    removeFootnotes: removeFootnotesEnabled,
    outputs,
    updateOutput,
    incrementSession
  } = useStore()

  const [isProcessing, setIsProcessing] = useState(false)
  const [currentProcessedText, setCurrentProcessedText] = useState('')

  const handleSubmit = useCallback(async () => {
    if (!inputText.trim() || isProcessing) return

    setIsProcessing(true)
    
    // Prepare text
    let processedText = inputText
    if (removeFootnotesEnabled) {
      processedText = removeFootnotes(processedText)
    }
    processedText = normalizeLineEndings(processedText)
    setCurrentProcessedText(processedText)

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
  }, [inputText, isProcessing, removeFootnotesEnabled, outputs, temperature, updateOutput, incrementSession])

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Cmd/Ctrl + Enter to process (global)
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter') {
        e.preventDefault()
        handleSubmit()
      }
      
      // Cmd/Ctrl + K to toggle input collapse
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault()
        useStore.getState().toggleInputCollapsed()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [handleSubmit])

  return (
    <div className="h-screen flex flex-col bg-background">
      <HeaderBar onSubmit={handleSubmit} isProcessing={isProcessing} />

      <main className="flex-1 overflow-hidden">
        <PanelGroup direction="vertical" className="h-full">
          <Panel 
            defaultSize={inputCollapsed ? 15 : 25} 
            minSize={inputCollapsed ? 10 : 15}
            maxSize={40}
            collapsible={true}
          >
            <div className="px-4 pt-4 pb-2 h-full">
              <InputPanel onSubmit={handleSubmit} />
            </div>
          </Panel>

          <PanelResizeHandle className="h-1.5 hover:bg-accent transition-colors" />

          <Panel defaultSize={inputCollapsed ? 85 : 75}>
            <div className="p-4 h-full">
              <PanelGroup direction="horizontal" className="h-full">
                <Panel defaultSize={33} minSize={25}>
                  <OutputPanel id="output-0" originalText={currentProcessedText || inputText} />
                </Panel>

                <PanelResizeHandle className="w-1.5 hover:bg-accent transition-colors mx-2" />

                <Panel defaultSize={34} minSize={25}>
                  <OutputPanel id="output-1" originalText={currentProcessedText || inputText} />
                </Panel>

                <PanelResizeHandle className="w-1.5 hover:bg-accent transition-colors mx-2" />

                <Panel defaultSize={33} minSize={25}>
                  <OutputPanel id="output-2" originalText={currentProcessedText || inputText} />
                </Panel>
              </PanelGroup>
            </div>
          </Panel>
        </PanelGroup>
      </main>
    </div>
  )
}