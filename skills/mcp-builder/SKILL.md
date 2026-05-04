---
name: mcp-builder
description: Build MCP (Model Context Protocol) servers using the official @modelcontextprotocol/sdk. Use this skill when users ask to create an MCP server, MCP tools, MCP resources, or want to expose APIs/functionality to AI agents. This skill covers vanilla MCP implementation with Streamable HTTP transport, session management, tools, resources, and prompts.
---

# MCP Builder Skill

This skill guides you in building MCP (Model Context Protocol) servers using the official `@modelcontextprotocol/sdk` package with TypeScript.

## When to Use This Skill

- User asks to "create an MCP server"
- User wants to "expose an API to AI agents"
- User needs "tools for Claude/LLM"
- User mentions "Model Context Protocol"
- User wants to build "AI agent integrations"

## MCP Core Concepts

### What is MCP?

Model Context Protocol (MCP) is an open standard that enables structured, secure interactions between Large Language Models (LLMs) and external systems. MCP acts as a bridge allowing AI agents to:

- Access external data sources safely
- Execute tools and functions
- Maintain consistent communication protocols
- Integrate with APIs and databases

### Key Components

**Tools** - Interactive functions that perform actions or computations:
- Execute operations and computations
- Accept parameters from the LLM
- Return structured responses
- Can change system state (side effects allowed)
- Examples: calculations, database operations, API calls, sending emails

**Resources** - Read-only data endpoints:
- Passive data sources (no side effects)
- Loaded into AI context for reasoning
- URI-based identification
- Examples: documentation, config files, status data, user profiles

**Prompts** - Reusable prompt templates:
- Pre-defined conversation starters
- Can accept arguments for customization
- Return structured messages for the LLM

### Transport Options

| Transport | Best For | Pros | Cons |
|-----------|----------|------|------|
| **Streamable HTTP** | Production, cloud, multiple clients | Scalable, remote access | Requires session management |
| **SSE** | Real-time apps, live updates | Streaming, auto-reconnect | Connection limits |
| **STDIO** | Local desktop, development | Simple, low latency | Single session, local only |

**Recommendation**: Use Streamable HTTP for most production servers.

## Project Structure

```
my-mcp-server/
├── src/
│   ├── server.ts          # Express server with transport setup
│   ├── mcp-server.ts      # MCP server with tools/resources/prompts
│   └── minimal/           # Optional: organized components
│       ├── tool.ts
│       ├── resource.ts
│       └── prompt.ts
├── package.json
├── tsconfig.json
└── .env
```

## Required Dependencies

```json
{
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.12.0",
    "express": "^4.21.0",
    "cors": "^2.8.5",
    "dotenv": "^16.5.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "@types/express": "^4.17.21",
    "@types/cors": "^2.8.17",
    "typescript": "^5.6.3",
    "tsx": "^4.20.3"
  }
}
```

## TypeScript Configuration

```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "NodeNext",
    "moduleResolution": "NodeNext",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true
  },
  "include": ["src/**/*"]
}
```

## Implementation Pattern

### 1. MCP Server Setup (mcp-server.ts)

```typescript
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';

export function createMCPServer() {
  const server = new McpServer({
    name: 'my-mcp-server',
    version: '1.0.0',
  });

  // Register tools
  server.tool('toolName', 'Tool description', {
    param1: { type: 'string', description: 'Parameter description' }
  }, async (args) => {
    // Implementation
    return {
      content: [{ type: 'text', text: JSON.stringify(result) }]
    };
  });

  // Register resources
  server.resource('resource://uri', 'Resource description', async () => ({
    contents: [{
      uri: 'resource://uri',
      mimeType: 'application/json',
      text: JSON.stringify(data)
    }]
  }));

  // Register prompts
  server.prompt('promptName', 'Prompt description', async (args) => ({
    messages: [{
      role: 'user',
      content: { type: 'text', text: `Prompt content with ${args.param}` }
    }]
  }));

  return server;
}
```

### 2. HTTP Server with Session Management (server.ts)

```typescript
import express from 'express';
import cors from 'cors';
import { randomUUID } from 'node:crypto';
import { StreamableHTTPServerTransport } from '@modelcontextprotocol/sdk/server/streamableHttp.js';
import { isInitializeRequest } from '@modelcontextprotocol/sdk/types.js';
import { createMCPServer } from './mcp-server.js';

const app = express();
const PORT = process.env.PORT || 3001;

// CORS for browser clients
app.use(cors({
  origin: '*',
  methods: ['GET', 'POST', 'DELETE', 'OPTIONS'],
  allowedHeaders: ['Content-Type', 'mcp-session-id', 'mcp-protocol-version', 'Authorization'],
  exposedHeaders: ['mcp-session-id'],
  credentials: true,
}));
app.use(express.json());

// Session storage
const transports: Record<string, StreamableHTTPServerTransport> = {};

// MCP endpoint handler
const handleMCPRequest = async (req, res) => {
  const sessionId = req.headers['mcp-session-id'] as string | undefined;
  let transport: StreamableHTTPServerTransport;

  if (sessionId && transports[sessionId]) {
    transport = transports[sessionId];
  } else if (!sessionId && isInitializeRequest(req.body)) {
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (newSessionId) => {
        transports[newSessionId] = transport;
      },
    });

    transport.onclose = () => {
      if (transport.sessionId) delete transports[transport.sessionId];
    };

    const server = createMCPServer();
    await server.connect(transport);
  } else {
    res.status(400).json({
      jsonrpc: '2.0',
      error: { code: -32000, message: 'No valid session ID or not an init request' },
      id: null,
    });
    return;
  }

  await transport.handleRequest(req, res, req.body);
};

app.post('/', handleMCPRequest);
app.post('/mcp', handleMCPRequest);

app.get('/health', (req, res) => {
  res.json({ status: 'ok', server: 'my-mcp-server', version: '1.0.0' });
});

app.listen(PORT, () => console.log(`MCP Server running on port ${PORT}`));
```

## Tool Implementation Examples

### Simple Tool

```typescript
server.tool('echo', 'Echo a message back', {
  message: { type: 'string', description: 'Message to echo' }
}, async ({ message }) => ({
  content: [{ type: 'text', text: `Echo: ${message}` }]
}));
```

### Tool with Multiple Parameters

```typescript
server.tool('calculate', 'Perform arithmetic operations', {
  a: { type: 'number', description: 'First number' },
  b: { type: 'number', description: 'Second number' },
  operation: { type: 'string', description: 'Operation: add, subtract, multiply, divide' }
}, async ({ a, b, operation }) => {
  let result: number;
  switch (operation) {
    case 'add': result = a + b; break;
    case 'subtract': result = a - b; break;
    case 'multiply': result = a * b; break;
    case 'divide': 
      if (b === 0) throw new Error('Division by zero');
      result = a / b; 
      break;
    default: throw new Error('Invalid operation');
  }
  return { content: [{ type: 'text', text: JSON.stringify({ result }) }] };
});
```

### External API Tool

```typescript
server.tool('getWeather', 'Get current weather for a city', {
  city: { type: 'string', description: 'City name' }
}, async ({ city }) => {
  const response = await fetch(`https://api.weather.com/v1/current?city=${encodeURIComponent(city)}&key=${process.env.WEATHER_API_KEY}`);
  const data = await response.json();
  return {
    content: [{ type: 'text', text: JSON.stringify({
      city,
      temperature: data.main.temp,
      conditions: data.weather[0].description
    }) }]
  };
});
```

## Resource Implementation Examples

```typescript
// Static resource
server.resource('config://settings', 'Application settings', async () => ({
  contents: [{
    uri: 'config://settings',
    mimeType: 'application/json',
    text: JSON.stringify({ theme: 'dark', language: 'en' })
  }]
}));

// Dynamic resource
server.resource('server://info', 'Server information', async () => ({
  contents: [{
    uri: 'server://info',
    mimeType: 'application/json',
    text: JSON.stringify({
      name: 'my-server',
      version: '1.0.0',
      uptime: process.uptime(),
      timestamp: new Date().toISOString()
    })
  }]
}));
```

## Editing Guidelines

### Core Principles

1. **Edit existing files, don't recreate** - Template files are provided; modify them
2. **Preserve existing structure** - Don't change fundamental architecture
3. **Minimal necessary changes** - Make smallest changes to achieve requirements
4. **Maintain backward compatibility** - Don't break existing functionality

### DO

- Add new tools/resources/prompts to existing service files
- Extend existing functionality
- Follow existing code patterns
- Use TypeScript for type safety

### DON'T

- Completely rewrite template files
- Remove essential boilerplate code
- Create unnecessary new files
- Add terminal/command instructions (user will run commands themselves)

## Running the Server

The user will handle running commands. Your job is to provide the code files only.

Standard commands the user might run:
- `npm install` - Install dependencies
- `npm run dev` or `npx tsx src/server.ts` - Development mode
- `npm run build` - Build for production
- `npm start` - Run production build
