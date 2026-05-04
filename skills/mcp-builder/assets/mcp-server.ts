import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

export function createMCPServer() {
  const server = new McpServer({
    name: 'my-mcp-server',
    version: '1.0.0',
  });

  // Example tool: Echo
  server.tool(
    'echo',
    'Echo a message back to the user',
    {
      message: { type: 'string', description: 'Message to echo back' },
    },
    async ({ message }) => {
      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              echoed: message,
              timestamp: new Date().toISOString(),
            }),
          },
        ],
      };
    }
  );

  // Example tool: Calculate
  server.tool(
    'calculate',
    'Perform arithmetic operations on two numbers',
    {
      a: { type: 'number', description: 'First number' },
      b: { type: 'number', description: 'Second number' },
      operation: {
        type: 'string',
        description: 'Operation to perform: add, subtract, multiply, divide',
      },
    },
    async ({ a, b, operation }) => {
      let result: number;

      switch (operation) {
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
          throw new Error(`Invalid operation: ${operation}`);
      }

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              operation,
              operands: { a, b },
              result,
            }),
          },
        ],
      };
    }
  );

  // Example resource: Server Info
  server.resource(
    'server://info',
    'Get server information and status',
    async () => ({
      contents: [
        {
          uri: 'server://info',
          mimeType: 'application/json',
          text: JSON.stringify({
            name: 'my-mcp-server',
            version: '1.0.0',
            uptime: process.uptime(),
            timestamp: new Date().toISOString(),
          }),
        },
      ],
    })
  );

  // Example prompt: Greeting
  server.prompt(
    'greeting',
    'Generate a personalized greeting message',
    async (args: { name?: string }) => ({
      messages: [
        {
          role: 'user' as const,
          content: {
            type: 'text' as const,
            text: `Hello ${args.name || 'there'}! Welcome to my MCP server.`,
          },
        },
      ],
    })
  );

  return server;
}
