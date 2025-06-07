const fs = require('fs');
const path = require('path');
const yaml = require('js-yaml');

// Read the YAML file from parent directory
const yamlPath = path.join(__dirname, '../../models.yaml');
const yamlContent = fs.readFileSync(yamlPath, 'utf8');
const config = yaml.load(yamlContent);

// Generate TypeScript content
const tsContent = `// This file is auto-generated from models.yaml
// Do not edit directly - edit models.yaml and run npm run generate-models

import { ModelConfig } from '@/types'

export const MODEL_CONFIGS: Record<string, ModelConfig> = {
${Object.entries(config.models).map(([id, model]) => {
    // Handle different output cost fields for Gemini models
    let outputCost = model.output_cost;
    if (!outputCost && model.output_cost_regular) {
      outputCost = model.output_cost_regular;
    }
    
    return `  '${id}': {
    id: '${id}',
    name: '${model.name}',
    apiModel: '${model.api_model || id}',
    provider: '${model.provider}',
    inputCost: ${model.input_cost},
    outputCost: ${outputCost},
    maxTokens: ${model.max_tokens},
    contextWindow: ${model.context_window}
  }`
  }).join(',\n')}
}

export const DEFAULT_MODELS = ${JSON.stringify(config.default_models, null, 2)}

// Export additional metadata
export const MODEL_METADATA = {
${Object.entries(config.models).map(([id, model]) => `  '${id}': {
    contextWindow: ${model.context_window}
  }`).join(',\n')}
}
`;

// Write to the constants file
const outputPath = path.join(__dirname, '../lib/model-config.ts');
fs.writeFileSync(outputPath, tsContent);

console.log('✅ Model configuration generated successfully!');
console.log(`📝 Written to: ${outputPath}`);
console.log(`📊 Total models: ${Object.keys(config.models).length}`);