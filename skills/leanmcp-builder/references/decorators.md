# LeanMCP Decorators Reference

## @Tool Decorator

Marks a method as an MCP tool.

```typescript
import { Tool, SchemaConstraint, Optional } from '@leanmcp/core';

// Simple tool
@Tool({ description: 'Tool description' })
async myTool(args: { param: string }) {
  return { result: args.param };
}

// With input class
class MyInput {
  @SchemaConstraint({ description: 'Field description', minLength: 1 })
  field!: string;
  
  @Optional()
  @SchemaConstraint({ description: 'Optional field', default: 'default' })
  optional?: string;
}

@Tool({ description: 'Tool with input class', inputClass: MyInput })
async myToolWithInput(input: MyInput) {
  return { result: input.field };
}
```

## @Resource Decorator

Marks a method as an MCP resource.

```typescript
import { Resource } from '@leanmcp/core';

@Resource({ description: 'Server information' })
async serverInfo() {
  return {
    contents: [{
      uri: 'server://info',
      mimeType: 'application/json',
      text: JSON.stringify({ name: 'server', version: '1.0.0' })
    }]
  };
}
```

## @Prompt Decorator

Marks a method as an MCP prompt.

```typescript
import { Prompt } from '@leanmcp/core';

@Prompt({ description: 'Generate greeting' })
async greeting(args: { name?: string }) {
  return {
    messages: [{
      role: 'user' as const,
      content: {
        type: 'text' as const,
        text: `Hello ${args.name || 'there'}!`
      }
    }]
  };
}
```

## @SchemaConstraint Decorator

Adds validation constraints to input fields.

```typescript
import { SchemaConstraint } from '@leanmcp/core';

class Input {
  // String constraints
  @SchemaConstraint({ 
    description: 'User name',
    minLength: 1,
    maxLength: 100,
    pattern: '^[a-zA-Z]+$'
  })
  name!: string;

  // Number constraints
  @SchemaConstraint({ 
    description: 'Age',
    minimum: 0,
    maximum: 150,
    multipleOf: 1
  })
  age!: number;

  // Enum constraint
  @SchemaConstraint({ 
    description: 'Status',
    enum: ['active', 'inactive', 'pending']
  })
  status!: string;

  // Format constraint
  @SchemaConstraint({ 
    description: 'Email address',
    format: 'email'
  })
  email!: string;

  // Default value
  @SchemaConstraint({ 
    description: 'Priority',
    default: 'medium'
  })
  priority!: string;
}
```

## @Optional Decorator

Marks a field as optional.

```typescript
import { Optional, SchemaConstraint } from '@leanmcp/core';

class Input {
  @SchemaConstraint({ description: 'Required field' })
  required!: string;

  @Optional()
  @SchemaConstraint({ description: 'Optional field' })
  optional?: string;
}
```

## @Authenticated Decorator

Adds authentication to a service class.

```typescript
import { Authenticated, AuthProvider, authUser } from '@leanmcp/auth';

const authProvider = new AuthProvider('cognito', {
  region: 'us-east-1',
  userPoolId: 'us-east-1_XXX',
  clientId: 'client-id'
});
await authProvider.init();

@Authenticated(authProvider)
export class SecureService {
  @Tool({ description: 'Get user data' })
  async getUserData() {
    // authUser is automatically available
    return { userId: authUser.sub, email: authUser.email };
  }
}
```

**Supported providers:**
- `cognito` - AWS Cognito
- `clerk` - Clerk (session & OAuth)
- `auth0` - Auth0
- `leanmcp` - LeanMCP platform

## @Elicitation Decorator

Collects user input via forms.

```typescript
import { Elicitation } from '@leanmcp/elicitation';

@Tool({ description: 'Create item' })
@Elicitation({
  title: 'Item Details',
  description: 'Please provide item information',
  fields: [
    { name: 'name', label: 'Name', type: 'text', required: true },
    { name: 'description', label: 'Description', type: 'textarea' },
    { name: 'quantity', label: 'Quantity', type: 'number', min: 1, max: 100 },
    { name: 'active', label: 'Active', type: 'boolean', defaultValue: true },
    { name: 'category', label: 'Category', type: 'select', options: [
      { value: 'a', label: 'Category A' },
      { value: 'b', label: 'Category B' }
    ]},
    { name: 'tags', label: 'Tags', type: 'multiselect', options: [
      { value: 'tag1', label: 'Tag 1' },
      { value: 'tag2', label: 'Tag 2' }
    ]},
    { name: 'email', label: 'Email', type: 'email' },
    { name: 'website', label: 'Website', type: 'url' },
    { name: 'date', label: 'Date', type: 'date' }
  ]
})
async createItem(args: { name: string; description?: string; quantity?: number }) {
  return { success: true, item: args };
}
```

## @RequireEnv Decorator

Validates required environment variables.

```typescript
import { RequireEnv, getEnv } from '@leanmcp/env-injection';

@Authenticated(authProvider, { projectId: 'my-project' })
export class ApiService {
  @Tool({ description: 'Call external API' })
  @RequireEnv(['API_KEY', 'API_SECRET'])
  async callApi(args: { endpoint: string }) {
    const apiKey = getEnv('API_KEY')!;
    const apiSecret = getEnv('API_SECRET')!;
    
    const response = await fetch(args.endpoint, {
      headers: { 'X-API-Key': apiKey, 'X-API-Secret': apiSecret }
    });
    
    return await response.json();
  }
}
```

**Env injection functions:**
- `getEnv(key)` - Get single env var
- `getAllEnv()` - Get all env vars
- `hasEnvContext()` - Check if env context is active
- `runWithEnv(env, fn)` - Run function with env vars
