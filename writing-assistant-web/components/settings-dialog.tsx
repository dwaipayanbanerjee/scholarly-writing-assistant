'use client'

import { Settings, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
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
    resetSession
  } = useStore()

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="icon" title="Settings">
          <Settings className="h-4 w-4" />
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
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
        </div>
      </DialogContent>
    </Dialog>
  )
}