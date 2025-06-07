import { NextRequest, NextResponse } from 'next/server'
import { GoogleGenerativeAI } from '@google/generative-ai'
import { SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE, MODEL_CONFIGS } from '@/lib/constants'
import { estimateTokens } from '@/lib/utils'

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY || '')

export async function POST(req: NextRequest) {
  try {
    const { text, model, temperature } = await req.json()

    if (!text || !model) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    const modelConfig = MODEL_CONFIGS[model]
    if (!modelConfig || modelConfig.provider !== 'gemini') {
      return NextResponse.json(
        { error: 'Invalid Gemini model' },
        { status: 400 }
      )
    }

    const userMessage = USER_MESSAGE_TEMPLATE.replace('{text}', text)
    const fullPrompt = `${SYSTEM_MESSAGE}\n\n${userMessage}`

    const geminiModel = genAI.getGenerativeModel({ 
      model: modelConfig.apiModel,
      generationConfig: {
        temperature: temperature || 0.7,
        maxOutputTokens: modelConfig.maxTokens,
      }
    })

    const result = await geminiModel.generateContent(fullPrompt)
    const response = await result.response
    const content = response.text()

    // Estimate tokens for Gemini (they don't provide token counts)
    const inputTokens = estimateTokens(fullPrompt)
    const outputTokens = estimateTokens(content)

    return NextResponse.json({
      content,
      inputTokens,
      outputTokens
    })
  } catch (error: any) {
    console.error('Gemini API error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to process request' },
      { status: 500 }
    )
  }
}