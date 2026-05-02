import {
  Tool,
  Resource,
  Prompt,
  SchemaConstraint,
  Optional,
} from '@leanmcp/core';

/**
 * Example service demonstrating LeanMCP SDK decorators
 * Place this file at: mcp/example/index.ts
 */

// Input schema with validation decorators
class CalculateInput {
  @SchemaConstraint({ description: 'First number' })
  a!: number;

  @SchemaConstraint({ description: 'Second number' })
  b!: number;

  @Optional()
  @SchemaConstraint({
    description: 'Operation to perform',
    enum: ['add', 'subtract', 'multiply', 'divide'],
    default: 'add',
  })
  operation?: string;
}

class EchoInput {
  @SchemaConstraint({
    description: 'Message to echo back',
    minLength: 1,
  })
  message!: string;
}

export class ExampleService {
  @Tool({
    description: 'Perform arithmetic operations with automatic schema validation',
    inputClass: CalculateInput,
  })
  async calculate(input: CalculateInput) {
    const a = Number(input.a);
    const b = Number(input.b);
    let result: number;

    switch (input.operation || 'add') {
      case 'add':
        result = a + b;
        break;
      case 'subtract':
        result = a - b;
        break;
      case 'multiply':
        result = a * b;
        break;
      case 'divide':
        if (b === 0) throw new Error('Cannot divide by zero');
        result = a / b;
        break;
      default:
        throw new Error('Invalid operation');
    }

    return {
      operation: input.operation || 'add',
      operands: { a: input.a, b: input.b },
      result,
    };
  }

  @Tool({
    description: 'Echo a message back',
    inputClass: EchoInput,
  })
  async echo(input: EchoInput) {
    return {
      echoed: input.message,
      timestamp: new Date().toISOString(),
    };
  }

  @Resource({ description: 'Get server information' })
  async serverInfo() {
    return {
      contents: [
        {
          uri: 'server://info',
          mimeType: 'application/json',
          text: JSON.stringify(
            {
              name: 'my-leanmcp-server',
              version: '1.0.0',
              uptime: process.uptime(),
            },
            null,
            2,
          ),
        },
      ],
    };
  }

  @Prompt({ description: 'Generate a greeting prompt' })
  async greeting(args: { name?: string }) {
    return {
      messages: [
        {
          role: 'user' as const,
          content: {
            type: 'text' as const,
            text: `Hello ${args.name || 'there'}! Welcome to my LeanMCP server.`,
          },
        },
      ],
    };
  }
}
