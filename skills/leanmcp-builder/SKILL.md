---
name: leanmcp-builder
description: Build MCP servers using the Leanmcp SDK with decorator-based TypeScript. Use this skill when users ask for "leanmcp", "MCP with decorators", "MCP with authentication", "MCP with elicitation", "MCP with environment injection", or want a simpler, more elegant way to build MCP servers. Leanmcp provides automatic schema generation, dependency injection, authentication, and user input collection.
---

# Leanmcp Builder Skill

This skill guides you in building MCP servers using the Leanmcp SDK - a decorator-based TypeScript framework for elegant MCP development.

## When to Use This Skill

- User asks for "leanmcp server"
- User wants "MCP with decorators"
- User needs "authenticated MCP server"
- User wants "simpler MCP development"
- User mentions "@leanmcp/core"
- User needs "user input collection" or "elicitation"
- User wants "environment injection" for multi-tenant secrets

## Leanmcp vs Vanilla MCP

| Feature | Vanilla MCP | Leanmcp SDK |
|---------|-------------|-------------|
| Tool definition | Manual schema | `@Tool` decorator with auto-schema |
| Input validation | Manual | Automatic with `@SchemaConstraint` |
| Service discovery | Manual registration | Auto-discovery from `./mcp` directory |
| Authentication | DIY | `@Authenticated` decorator |
| User input | Not built-in | `@Elicitation` decorator |
| Secrets | DIY | `@RequireEnv` + `getEnv()` |

## Core Packages

```bash
# Minimal setup
npm install @leanmcp/core

# With authentication
npm install @leanmcp/auth

# With user input forms
npm install @leanmcp/elicitation

# With user secrets
npm install @leanmcp/env-injection

# CLI (global or dev)
npm install -g @leanmcp/cli
```

## Project Structure

```
my-leanmcp-server/
├── main.ts                 # Entry point (minimal)
├── mcp/                    # Auto-discovered services
│   ├── example/
│   │   └── index.ts        # Exports ExampleService
│   └── myservice/
│       └── index.ts        # Exports MyService
├── package.json
├── tsconfig.json
└── .env
```

## Required package.json

```json
{
  "name": "my-leanmcp-server",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "leanmcp dev",
    "start": "leanmcp start",
    "build": "leanmcp build"
  },
  "dependencies": {
    "@leanmcp/core": "latest",
    "dotenv": "^16.5.0"
  },
  "devDependencies": {
    "@leanmcp/cli": "latest",
    "@types/node": "^20.0.0",
    "typescript": "^5.6.3"
  }
}
```

## TypeScript Configuration

```json
{
  "compilerOptions": {
    "experimentalDecorators": true,
    "emitDecoratorMetadata": true,
    "target": "ES2020",
    "module": "ESNext",
    "moduleResolution": "node",
    "outDir": "./dist",
    "strict": true,
    "esModuleInterop": true
  },
  "include": ["**/*.ts"]
}
```

## Entry Point (main.ts)

```typescript
import dotenv from 'dotenv';
import { createHTTPServer } from '@leanmcp/core';

dotenv.config();

// Services are automatically discovered from ./mcp directory
await createHTTPServer({
  name: 'my-leanmcp-server',
  version: '1.0.0',
  port: 3001,
  cors: true,
  logging: true,
});
```

## @Tool Decorator

Marks a method as an MCP tool with automatic schema generation.

### Basic Tool

```typescript
import { Tool } from '@leanmcp/core';

export class MyService {
  @Tool({ description: 'Echo a message back' })
  async echo(args: { message: string }) {
    return { echoed: args.message };
  }
}
```

### Tool with Input Class (Recommended)

```typescript
import { Tool, SchemaConstraint, Optional } from '@leanmcp/core';

class CalculateInput {
  @SchemaConstraint({ description: 'First number', minimum: -1000000 })
  a!: number;

  @SchemaConstraint({ description: 'Second number', minimum: -1000000 })
  b!: number;

  @Optional()
  @SchemaConstraint({ 
    description: 'Operation to perform',
    enum: ['add', 'subtract', 'multiply', 'divide'],
    default: 'add'
  })
  operation?: string;
}

export class MathService {
  @Tool({ 
    description: 'Perform arithmetic operations',
    inputClass: CalculateInput
  })
  async calculate(input: CalculateInput) {
    const a = Number(input.a);
    const b = Number(input.b);
    
    switch (input.operation || 'add') {
      case 'add': return { result: a + b };
      case 'subtract': return { result: a - b };
      case 'multiply': return { result: a * b };
      case 'divide': 
        if (b === 0) throw new Error('Division by zero');
        return { result: a / b };
      default: throw new Error('Invalid operation');
    }
  }
}
```

### Tool Naming

Tool name is derived from the method name:
- `async calculate(...)` -> tool name: `calculate`
- `async sendMessage(...)` -> tool name: `sendMessage`

## @Resource Decorator

```typescript
import { Resource } from '@leanmcp/core';

export class InfoService {
  @Resource({ description: 'Get server information' })
  async serverInfo() {
    return {
      contents: [{
        uri: 'server://info',
        mimeType: 'application/json',
        text: JSON.stringify({
          name: 'my-server',
          version: '1.0.0',
          uptime: process.uptime()
        })
      }]
    };
  }
}
```

## @Prompt Decorator

```typescript
import { Prompt } from '@leanmcp/core';

export class PromptService {
  @Prompt({ description: 'Generate a greeting prompt' })
  async greeting(args: { name?: string }) {
    return {
      messages: [{
        role: 'user' as const,
        content: {
          type: 'text' as const,
          text: `Hello ${args.name || 'there'}! Welcome to my server.`
        }
      }]
    };
  }
}
```

## @Authenticated Decorator

Add authentication to your service:

```typescript
import { Tool } from '@leanmcp/core';
import { Authenticated, AuthProvider, authUser } from '@leanmcp/auth';

const authProvider = new AuthProvider('cognito', {
  region: 'us-east-1',
  userPoolId: 'us-east-1_XXXXXXXXX',
  clientId: 'your-client-id'
});
await authProvider.init();

@Authenticated(authProvider)
export class SecureService {
  @Tool({ description: 'Get user data' })
  async getUserData() {
    // authUser is automatically available
    return { 
      userId: authUser.sub,
      email: authUser.email 
    };
  }
}
```

**Supported providers:** AWS Cognito, Clerk, Auth0, Leanmcp

## @Elicitation Decorator

Collect structured user input:

```typescript
import { Tool } from '@leanmcp/core';
import { Elicitation } from '@leanmcp/elicitation';

export class ChannelService {
  @Tool({ description: 'Create a new channel' })
  @Elicitation({
    title: 'Channel Details',
    fields: [
      { name: 'channelName', label: 'Channel Name', type: 'text', required: true },
      { name: 'isPrivate', label: 'Private Channel', type: 'boolean', defaultValue: false },
      { name: 'topic', label: 'Topic', type: 'textarea' }
    ]
  })
  async createChannel(args: { channelName: string; isPrivate: boolean; topic?: string }) {
    return { success: true, channel: args.channelName };
  }
}
```

**Field types:** text, textarea, number, boolean, select, multiselect, email, url, date

## @RequireEnv Decorator

Inject user-specific secrets:

```typescript
import { Tool } from '@leanmcp/core';
import { Authenticated } from '@leanmcp/auth';
import { RequireEnv, getEnv } from '@leanmcp/env-injection';

@Authenticated(authProvider, { projectId: 'my-project' })
export class SlackService {
  @Tool({ description: 'Send Slack message' })
  @RequireEnv(['SLACK_TOKEN', 'SLACK_CHANNEL'])
  async sendMessage(args: { message: string }) {
    const token = getEnv('SLACK_TOKEN')!;
    const channel = getEnv('SLACK_CHANNEL')!;
    
    await fetch('https://slack.com/api/chat.postMessage', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ channel, text: args.message })
    });
    
    return { success: true };
  }
}
```

## Complete Service Example

```typescript
// mcp/products/index.ts
import { Tool, Resource, SchemaConstraint, Optional } from '@leanmcp/core';

class CreateProductInput {
  @SchemaConstraint({ description: 'Product name', minLength: 1 })
  name!: string;

  @SchemaConstraint({ description: 'Price in dollars', minimum: 0 })
  price!: number;

  @Optional()
  @SchemaConstraint({ description: 'Product description' })
  description?: string;
}

class UpdateProductInput {
  @SchemaConstraint({ description: 'Product ID' })
  id!: string;

  @Optional()
  @SchemaConstraint({ description: 'Product name' })
  name?: string;

  @Optional()
  @SchemaConstraint({ description: 'Price in dollars', minimum: 0 })
  price?: number;
}

export class ProductsService {
  private products: Map<string, any> = new Map();

  @Tool({ description: 'Create a new product', inputClass: CreateProductInput })
  async createProduct(input: CreateProductInput) {
    const id = crypto.randomUUID();
    const product = { id, ...input, createdAt: new Date().toISOString() };
    this.products.set(id, product);
    return { success: true, product };
  }

  @Tool({ description: 'List all products' })
  async listProducts() {
    return { products: Array.from(this.products.values()) };
  }

  @Tool({ description: 'Update a product', inputClass: UpdateProductInput })
  async updateProduct(input: UpdateProductInput) {
    const product = this.products.get(input.id);
    if (!product) throw new Error('Product not found');
    
    if (input.name) product.name = input.name;
    if (input.price) product.price = input.price;
    product.updatedAt = new Date().toISOString();
    
    return { success: true, product };
  }

  @Tool({ description: 'Delete a product' })
  async deleteProduct(args: { id: string }) {
    if (!this.products.has(args.id)) throw new Error('Product not found');
    this.products.delete(args.id);
    return { success: true };
  }

  @Resource({ description: 'Get product statistics' })
  async productStats() {
    const products = Array.from(this.products.values());
    return {
      contents: [{
        uri: 'products://stats',
        mimeType: 'application/json',
        text: JSON.stringify({
          total: products.length,
          totalValue: products.reduce((sum, p) => sum + p.price, 0)
        })
      }]
    };
  }
}
```

## Server Configuration Options

```typescript
import { MCPServer, createHTTPServer } from '@leanmcp/core';

// Simple API (recommended)
await createHTTPServer({
  name: 'my-server',
  version: '1.0.0',
  port: 3001,
  cors: true,
  logging: true
});

// Advanced: Factory pattern with manual registration
const serverFactory = async () => {
  const server = new MCPServer({
    name: 'my-server',
    version: '1.0.0',
    autoDiscover: false,  // Disable auto-discovery
    logging: true
  });
  
  server.registerService(new MyService());
  return server.getServer();
};

await createHTTPServer(serverFactory, {
  port: 3001,
  cors: true
});
```

## Editing Guidelines

### DO

- Add new services in `mcp/servicename/index.ts`
- Use `@Tool`, `@Resource`, `@Prompt` decorators
- Use `@SchemaConstraint` for input validation
- Use `@Optional()` for optional fields
- Export service classes from index.ts
- Follow decorator patterns consistently

### DON'T

- Wrap services in AppProvider (CLI handles this)
- Use direct imports for components in `@UIApp`
- Completely rewrite existing files
- Add terminal/command instructions
- Remove existing working code

## Error Handling

```typescript
@Tool({ description: 'Divide two numbers' })
async divide(input: { a: number; b: number }) {
  if (input.b === 0) {
    throw new Error('Division by zero is not allowed');
  }
  return { result: input.a / input.b };
}
```

Errors are automatically caught and formatted as MCP error responses.

## Best Practices

1. **Always provide descriptions** - Helps LLMs understand tool purpose
2. **Use inputClass for complex inputs** - Automatic schema generation
3. **Return structured data** - Objects with clear field names
4. **Handle errors gracefully** - Throw descriptive errors
5. **Keep tools focused** - One tool = one clear action
6. **Organize by domain** - One service per business domain
7. **Use schema constraints** - Validate inputs with min/max/enum
