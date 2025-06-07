'use client'

import { useState, useCallback, useRef } from 'react'
import { ChevronUp, ChevronDown, FileText, Trash2, Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { useStore } from '@/lib/store'
import { cn } from '@/lib/utils'

interface InputPanelProps {
  onSubmit: () => void
}

export function InputPanel({ onSubmit }: InputPanelProps) {
  const { inputText, setInputText, inputCollapsed, toggleInputCollapsed, resetOutputs } = useStore()
  const [isDragging, setIsDragging] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file && file.type === 'text/plain') {
      const reader = new FileReader()
      reader.onload = (event) => {
        const text = event.target?.result as string
        setInputText(text)
      }
      reader.readAsText(file)
    }
  }, [setInputText])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => {
    setIsDragging(false)
  }, [])

  const handleKeyDown = useCallback((e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Submit on Enter (without Shift)
    if (e.key === 'Enter' && !e.shiftKey && inputText.trim()) {
      e.preventDefault()
      onSubmit()
    }
  }, [inputText, onSubmit])

  const wordCount = inputText.split(/\s+/).filter(word => word.length > 0).length
  const charCount = inputText.length

  return (
    <div className={cn(
      "border rounded-lg transition-all duration-300",
      inputCollapsed ? "h-16" : "h-full min-h-[300px]"
    )}>
      <div className="flex items-center justify-between p-4 border-b">
        <div className="flex items-center gap-4">
          <h2 className="font-semibold">Input Text</h2>
          {inputText && (
            <span className="text-sm text-muted-foreground">
              {wordCount} words • {charCount} characters
            </span>
          )}
        </div>
        <div className="flex items-center gap-2">
          {inputText && !inputCollapsed && (
            <Button
              variant="default"
              size="sm"
              onClick={onSubmit}
              title="Improve Writing (Enter)"
            >
              <Send className="h-4 w-4 mr-1" />
              Submit
            </Button>
          )}
          {inputText && (
            <Button
              variant="ghost"
              size="icon"
              onClick={() => {
                setInputText('')
                resetOutputs()
              }}
              title="Clear input"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          )}
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleInputCollapsed}
            title={inputCollapsed ? "Expand" : "Collapse"}
          >
            {inputCollapsed ? (
              <ChevronDown className="h-4 w-4" />
            ) : (
              <ChevronUp className="h-4 w-4" />
            )}
          </Button>
        </div>
      </div>

      {!inputCollapsed && (
        <div
          className={cn(
            "p-4 h-[calc(100%-4rem)] relative",
            isDragging && "bg-accent/50"
          )}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
        >
          <Textarea
            ref={textareaRef}
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your text here... or drag and drop a .txt file

Press Enter to submit (Shift+Enter for new line)"
            className="h-full resize-none custom-scrollbar"
          />
          {isDragging && (
            <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
              <div className="bg-background/90 rounded-lg p-4 flex items-center gap-2">
                <FileText className="h-5 w-5" />
                <span>Drop your .txt file here</span>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  )
}