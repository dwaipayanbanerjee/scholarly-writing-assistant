'use client'

import { useMemo } from 'react'
import * as diff from 'diff'

interface DiffViewerProps {
  original: string
  revised: string
  showDiff: boolean
}

export function DiffViewer({ original, revised, showDiff }: DiffViewerProps) {
  const diffElements = useMemo(() => {
    if (!showDiff || !original || !revised) {
      return revised
    }

    // Use diffWords for better word-level granularity
    const changes = diff.diffWords(original, revised, {
      ignoreCase: false,
      ignoreWhitespace: false
    })
    
    return changes.map((part, index) => {
      if (part.added) {
        return (
          <span 
            key={index} 
            className="diff-added" 
            style={{ backgroundColor: 'rgb(187, 247, 208)', color: 'rgb(6, 78, 59)', padding: '0 2px', borderRadius: '2px', fontWeight: 500 }}
            title="Added"
          >
            {part.value}
          </span>
        )
      } else if (part.removed) {
        return (
          <span 
            key={index} 
            className="diff-removed" 
            style={{ backgroundColor: 'rgb(254, 202, 202)', color: 'rgb(153, 27, 27)', textDecoration: 'line-through', padding: '0 2px', borderRadius: '2px', opacity: 0.75 }}
            title="Removed"
          >
            {part.value}
          </span>
        )
      } else {
        return <span key={index}>{part.value}</span>
      }
    })
  }, [original, revised, showDiff])

  return (
    <div className="whitespace-pre-wrap leading-relaxed">
      {diffElements}
    </div>
  )
}