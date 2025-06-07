import { NextRequest, NextResponse } from 'next/server'
import Anthropic from '@anthropic-ai/sdk'
import { SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE, MODEL_CONFIGS } from '@/lib/constants'

const anthropic = new Anthropic({
  apiKey: process.env.ANTHROPIC_API_KEY,
})

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
    if (!modelConfig || modelConfig.provider !== 'claude') {
      return NextResponse.json(
        { error: 'Invalid Claude model' },
        { status: 400 }
      )
    }

    const userMessage = USER_MESSAGE_TEMPLATE.replace('{text}', text)

    const response = await anthropic.messages.create({
      model: modelConfig.apiModel,
      max_tokens: modelConfig.maxTokens || 4096,
      temperature: temperature || 0.7,
      system: SYSTEM_MESSAGE,
      messages: [
        { role: 'user', content: userMessage }
      ]
    })

    const content = response.content[0].type === 'text' 
      ? response.content[0].text 
      : ''
    
    const inputTokens = response.usage?.input_tokens || 0
    const outputTokens = response.usage?.output_tokens || 0

    return NextResponse.json({
      content,
      inputTokens,
      outputTokens
    })
  } catch (error: any) {
    console.error('Claude API error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to process request' },
      { status: 500 }
    )
  }
}