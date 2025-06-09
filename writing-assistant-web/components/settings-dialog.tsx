'use client'

import { Settings, X, FileText, Save } from 'lucide-react'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Textarea } from '@/components/ui/textarea'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { Switch } from '@/components/ui/switch'
import { useStore } from '@/lib/store'
import { formatCost } from '@/lib/utils'

export function SettingsDialog() {
  const {
    temperature,
    setTemperature,
    removeFootnotes,
    setRemoveFootnotes,
    sessionCost,
    sessionRequests,
    resetSession,
    systemPrompt,
    sessionPrompt,
    currentPrompt,
    setSystemPrompt,
    setSessionPrompt,
    setCurrentPrompt
  } = useStore()
  
  const [showPrompt, setShowPrompt] = useState(false)
  const [editedPrompt, setEditedPrompt] = useState('')
  const [promptScope, setPromptScope] = useState<'current' | 'session' | 'persistent'>('current')

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" title="Settings">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[625px]">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>
        <div className="space-y-6 py-4">
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm font-medium">
                  Temperature: {temperature.toFixed(1)}
                </label>
                <span className="text-xs text-muted-foreground">
                  {temperature === 0 ? 'Deterministic' : temperature < 0.5 ? 'Focused' : temperature < 0.8 ? 'Balanced' : 'Creative'}
                </span>
              </div>
              <Slider
                value={[temperature]}
                onValueChange={([value]) => setTemperature(value)}
                min={0}
                max={1}
                step={0.1}
                className="w-full"
              />
              <p className="text-xs text-muted-foreground">
                Controls randomness in AI responses. Lower = more focused, Higher = more creative.
              </p>
            </div>

            <div className="flex items-center justify-between py-2">
              <div className="space-y-1">
                <label htmlFor="footnotes" className="text-sm font-medium">
                  Remove Footnotes
                </label>
                <p className="text-xs text-muted-foreground">
                  Automatically remove footnote references before processing
                </p>
              </div>
              <Switch
                id="footnotes"
                checked={removeFootnotes}
                onCheckedChange={setRemoveFootnotes}
              />
            </div>
          </div>

          <div className="border-t pt-4">
            <h4 className="text-sm font-medium mb-3">Session Statistics</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-muted-foreground">Total Cost:</span>
                <span className="font-medium">{formatCost(sessionCost)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-muted-foreground">Requests Made:</span>
                <span className="font-medium">{sessionRequests}</span>
              </div>
              {sessionRequests > 0 && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Average Cost:</span>
                  <span className="font-medium">{formatCost(sessionCost / sessionRequests)}</span>
                </div>
              )}
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={resetSession}
              className="mt-3 w-full"
            >
              Reset Session
            </Button>
          </div>

          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-3">
              <h4 className="text-sm font-medium">Writing Prompt</h4>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setShowPrompt(!showPrompt)
                  if (!showPrompt) {
                    const activePrompt = currentPrompt || sessionPrompt || systemPrompt
                    setEditedPrompt(activePrompt)
                  }
                }}
              >
                <FileText className="h-4 w-4 mr-1" />
                {showPrompt ? 'Hide' : 'View'} Prompt
              </Button>
            </div>
            
            {showPrompt && (
              <div className="space-y-3">
                <div className="text-xs text-muted-foreground">
                  {currentPrompt ? 'Using current prompt override' : 
                   sessionPrompt ? 'Using session prompt override' : 
                   'Using default system prompt'}
                </div>
                
                <Textarea
                  value={editedPrompt}
                  onChange={(e) => setEditedPrompt(e.target.value)}
                  className="min-h-[200px] text-sm"
                  placeholder="Enter your custom prompt..."
                />
                
                <div className="flex items-center gap-2">
                  <Select
                    value={promptScope}
                    onValueChange={(value: 'current' | 'session' | 'persistent') => setPromptScope(value)}
                  >
                    <SelectTrigger className="flex-1">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="current">Current prompt only</SelectItem>
                      <SelectItem value="session">This session</SelectItem>
                      <SelectItem value="persistent">Save permanently</SelectItem>
                    </SelectContent>
                  </Select>
                  
                  <Button
                    size="sm"
                    onClick={() => {
                      switch (promptScope) {
                        case 'current':
                          setCurrentPrompt(editedPrompt)
                          break
                        case 'session':
                          setSessionPrompt(editedPrompt)
                          setCurrentPrompt(null)
                          break
                        case 'persistent':
                          setSystemPrompt(editedPrompt)
                          setSessionPrompt(null)
                          setCurrentPrompt(null)
                          break
                      }
                    }}
                  >
                    <Save className="h-4 w-4 mr-1" />
                    Save Changes
                  </Button>
                </div>
                
                <div className="text-xs text-muted-foreground space-y-1">
                  <p><strong>Current prompt only:</strong> Applies to the next submission only</p>
                  <p><strong>This session:</strong> Applies until you close the app</p>
                  <p><strong>Save permanently:</strong> Overwrites the default prompt</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}