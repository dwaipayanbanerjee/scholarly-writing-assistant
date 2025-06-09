import { NextRequest, NextResponse } from 'next/server'
import OpenAI from 'openai'
import { SYSTEM_MESSAGE, USER_MESSAGE_TEMPLATE, MODEL_CONFIGS } from '@/lib/constants'

const openai = new OpenAI({
  apiKey: process.env.OPENAI_API_KEY,
})

export async function POST(req: NextRequest) {
  try {
    const { text, model, temperature, systemPrompt } = await req.json()

    if (!text || !model) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    const modelConfig = MODEL_CONFIGS[model]
    if (!modelConfig || modelConfig.provider !== 'openai') {
      return NextResponse.json(
        { error: 'Invalid OpenAI model' },
        { status: 400 }
      )
    }

    const userMessage = USER_MESSAGE_TEMPLATE.replace('{text}', text)
    const promptToUse = systemPrompt || SYSTEM_MESSAGE

    let response
    let inputTokens = 0
    let outputTokens = 0

    const apiModel = modelConfig.apiModel

    if (apiModel.startsWith('o1-')) {
      // o1 models don't support system messages or temperature
      response = await openai.chat.completions.create({
        model: apiModel,
        messages: [
          { role: 'user', content: `${promptToUse}\n\n${userMessage}` }
        ],
        max_tokens: modelConfig.maxTokens
      })
    } else {
      response = await openai.chat.completions.create({
        model: apiModel,
        messages: [
          { role: 'system', content: promptToUse },
          { role: 'user', content: userMessage }
        ],
        temperature: temperature || 0.7,
        max_tokens: modelConfig.maxTokens
      })
    }

    const content = response.choices[0]?.message?.content || ''
    inputTokens = response.usage?.prompt_tokens || 0
    outputTokens = response.usage?.completion_tokens || 0

    return NextResponse.json({
      content,
      inputTokens,
      outputTokens
    })
  } catch (error: any) {
    console.error('OpenAI API error:', error)
    return NextResponse.json(
      { error: error.message || 'Failed to process request' },
      { status: 500 }
    )
  }
}