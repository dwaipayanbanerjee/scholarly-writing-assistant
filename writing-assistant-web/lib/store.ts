import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { AppState, Model, OutputPanel } from '@/types'
import { DEFAULT_MODELS } from './constants'

interface Store extends AppState {
  setInputText: (text: string) => void
  toggleInputCollapsed: () => void
  setRemoveFootnotes: (value: boolean) => void
  setTemperature: (value: number) => void
  updateOutput: (id: string, updates: Partial<OutputPanel>) => void
  setModelForOutput: (id: string, model: Model) => void
  resetOutputs: () => void
  incrementSession: (cost: number) => void
  resetSession: () => void
}

export const useStore = create<Store>()(
  persist(
    (set) => ({
      inputText: '',
      inputCollapsed: false,
      removeFootnotes: true,
      temperature: 0.7,
      outputs: DEFAULT_MODELS.map((model, index) => ({
        id: `output-${index}`,
        model: model as Model,
        output: '',
        cost: 0,
        tokens: { input: 0, output: 0 },
        loading: false
      })),
      sessionCost: 0,
      sessionRequests: 0,

      setInputText: (text) => set({ inputText: text }),
      
      toggleInputCollapsed: () => set((state) => ({ 
        inputCollapsed: !state.inputCollapsed 
      })),
      
      setRemoveFootnotes: (value) => set({ removeFootnotes: value }),
      
      setTemperature: (value) => set({ temperature: value }),
      
      updateOutput: (id, updates) => set((state) => ({
        outputs: state.outputs.map(output =>
          output.id === id ? { ...output, ...updates } : output
        )
      })),
      
      setModelForOutput: (id, model) => set((state) => ({
        outputs: state.outputs.map(output =>
          output.id === id ? { ...output, model } : output
        )
      })),
      
      resetOutputs: () => set((state) => ({
        outputs: state.outputs.map(output => ({
          ...output,
          output: '',
          cost: 0,
          tokens: { input: 0, output: 0 },
          loading: false,
          error: undefined
        }))
      })),
      
      incrementSession: (cost) => set((state) => ({
        sessionCost: state.sessionCost + cost,
        sessionRequests: state.sessionRequests + 1
      })),
      
      resetSession: () => set({
        sessionCost: 0,
        sessionRequests: 0
      })
    }),
    {
      name: 'writing-assistant-storage',
      partialize: (state) => ({
        removeFootnotes: state.removeFootnotes,
        temperature: state.temperature,
        sessionCost: state.sessionCost,
        sessionRequests: state.sessionRequests
      })
    }
  )
)