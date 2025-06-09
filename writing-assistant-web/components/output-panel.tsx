'use client'

import { useState } from 'react'
import { Copy, Check, Eye, EyeOff, Loader2, AlertCircle, ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { DiffViewer } from '@/components/diff-viewer'
import { useStore } from '@/lib/store'
import { MODEL_CONFIGS } from '@/lib/constants'
import { formatCost, cn } from '@/lib/utils'
import { Model } from '@/types'

interface OutputPanelProps {
  id: string
  originalText: string
}

export function OutputPanel({ id, originalText }: OutputPanelProps) {
  const [copied, setCopied] = useState(false)
  const [showDiff, setShowDiff] = useState(false)
  
  const output = useStore(state => state.outputs.find(o => o.id === id))
  const setModelForOutput = useStore(state => state.setModelForOutput)
  
  if (!output) return null

  const handleCopy = () => {
    navigator.clipboard.writeText(output.output)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const modelConfig = MODEL_CONFIGS[output.model]

  return (
    <div className="h-full flex flex-col border rounded-lg bg-card">
      {/* Compact Header */}
      <div className={cn(
        "flex items-center justify-between p-2 border-b gap-2",
        showDiff && "bg-amber-50 dark:bg-amber-950/20"
      )}>
        <Select
          value={output.model}
          onValueChange={(value: Model) => setModelForOutput(id, value)}
          disabled={output.loading}
        >
          <SelectTrigger className="h-8 text-sm flex-1">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {Object.values(MODEL_CONFIGS).map(config => (
              <SelectItem key={config.id} value={config.id}>
                {config.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        
        <div className="flex items-center gap-1">
          {output.cost > 0 && (
            <span className="text-xs text-muted-foreground px-1">
              {formatCost(output.cost)}
            </span>
          )}
          
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={() => setShowDiff(!showDiff)}
            disabled={!output.output}
            title={showDiff ? "Hide differences" : "Show differences"}
          >
            {showDiff ? (
              <EyeOff className="h-3.5 w-3.5" />
            ) : (
              <Eye className="h-3.5 w-3.5" />
            )}
          </Button>
          
          <Button
            variant="ghost"
            size="icon"
            className="h-7 w-7"
            onClick={handleCopy}
            disabled={!output.output}
            title="Copy to clipboard"
          >
            {copied ? (
              <Check className="h-3.5 w-3.5 text-green-600" />
            ) : (
              <Copy className="h-3.5 w-3.5" />
            )}
          </Button>
        </div>
      </div>
      
      {/* Content Area - Takes all available space */}
      <div className="flex-1 overflow-auto p-4">
        {output.loading && (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <Loader2 className="h-6 w-6 animate-spin mx-auto mb-2" />
              <p className="text-sm text-muted-foreground">Processing...</p>
            </div>
          </div>
        )}
        
        {output.error && (
          <div className="flex items-start gap-2 text-destructive">
            <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
            <span className="text-sm">{output.error}</span>
          </div>
        )}
        
        {output.output && !output.loading && (
          <>
            {showDiff && (
              <div className="flex items-center gap-4 text-xs text-muted-foreground mb-2 p-2 bg-muted/30 rounded">
                <span className="flex items-center gap-1">
                  <span className="inline-block w-3 h-3 bg-green-200 dark:bg-green-900/40 rounded-sm"></span>
                  Added
                </span>
                <span className="flex items-center gap-1">
                  <span className="inline-block w-3 h-3 bg-red-200 dark:bg-red-900/40 rounded-sm"></span>
                  Removed
                </span>
              </div>
            )}
            <div className="custom-scrollbar text-base leading-relaxed">
              {showDiff ? (
                <DiffViewer
                  original={originalText}
                  revised={output.output}
                  showDiff={showDiff}
                />
              ) : (
                <div className="whitespace-pre-wrap">{output.output}</div>
              )}
            </div>
          </>
        )}
        
        {!output.output && !output.loading && !output.error && (
          <div className="text-muted-foreground text-center h-full flex items-center justify-center">
            <p className="text-sm">Revised text will appear here...</p>
          </div>
        )}
      </div>
      
      {/* Token count footer - only show when there's output */}
      {output.output && output.tokens.input > 0 && (
        <div className="border-t px-3 py-1.5 text-xs text-muted-foreground">
          {output.tokens.input + output.tokens.output} tokens
        </div>
      )}
    </div>
  )
}