# MCP Implementation Patterns

## Stateless Server Pattern

Stateless MCP servers create new instances for each request, maintaining no persistent state between interactions.

**Key Characteristics:**
- No session persistence between requests
- Each request is completely independent
- Simple to implement and understand
- Highly scalable architecture

**Best Use Cases:**
- Simple API wrappers
- Mathematical calculations
- Data transformations
- Read-only operations
- Stateless external API calls

**Implementation:**
```typescript
// Each request gets a fresh server instance
const handleMCPRequest = async (req, res) => {
  if (!sessionId && isInitializeRequest(req.body)) {
    transport = new StreamableHTTPServerTransport({...});
    const server = createMCPServer(); // Fresh instance
    await server.connect(transport);
  }
};
```

## Stateful Server Pattern

Stateful servers maintain context across multiple requests within a session.

**Key Characteristics:**
- Session persistence
- Context maintained between calls
- More complex implementation
- Supports multi-step workflows

**Best Use Cases:**
- Multi-step workflows
- Shopping carts
- Document editing sessions
- Game state management

**Implementation:**
```typescript
// Store state per session
const sessionState: Map<string, any> = new Map();

server.tool('addToCart', 'Add item to cart', {
  item: { type: 'string' }
}, async ({ item }) => {
  const sessionId = getCurrentSessionId();
  const cart = sessionState.get(sessionId) || [];
  cart.push(item);
  sessionState.set(sessionId, cart);
  return { content: [{ type: 'text', text: JSON.stringify({ cart }) }] };
});
```

## REST API Wrapper Pattern

Wrap existing REST APIs as MCP tools.

```typescript
server.tool('getUser', 'Get user by ID', {
  userId: { type: 'string', description: 'User ID' }
}, async ({ userId }) => {
  const response = await fetch(`${API_BASE}/users/${userId}`, {
    headers: { 'Authorization': `Bearer ${process.env.API_KEY}` }
  });
  
  if (!response.ok) {
    throw new Error(`API error: ${response.status}`);
  }
  
  const user = await response.json();
  return { content: [{ type: 'text', text: JSON.stringify(user) }] };
});
```

## Data Processing Pattern

Process and transform data.

```typescript
server.tool('transformData', 'Transform CSV to JSON', {
  csvData: { type: 'string', description: 'CSV data' }
}, async ({ csvData }) => {
  const lines = csvData.split('\n');
  const headers = lines[0].split(',');
  const result = lines.slice(1).map(line => {
    const values = line.split(',');
    return headers.reduce((obj, header, i) => {
      obj[header.trim()] = values[i]?.trim();
      return obj;
    }, {});
  });
  
  return { content: [{ type: 'text', text: JSON.stringify(result) }] };
});
```

## Error Handling Pattern

```typescript
server.tool('riskyOperation', 'Operation that might fail', {
  input: { type: 'string' }
}, async ({ input }) => {
  try {
    const result = await performRiskyOperation(input);
    return { content: [{ type: 'text', text: JSON.stringify({ success: true, result }) }] };
  } catch (error) {
    // Return error as structured response
    return { 
      content: [{ 
        type: 'text', 
        text: JSON.stringify({ 
          success: false, 
          error: error.message,
          code: error.code || 'UNKNOWN_ERROR'
        }) 
      }],
      isError: true
    };
  }
});
```

## Resource Template Pattern

Resources with URI templates for dynamic content.

```typescript
// Static resource
server.resource('config://app', 'App configuration', async () => ({
  contents: [{
    uri: 'config://app',
    mimeType: 'application/json',
    text: JSON.stringify(config)
  }]
}));

// Dynamic resource with parameter
server.resource('users://{id}', 'Get user by ID', async (uri) => {
  const id = uri.pathname.split('/').pop();
  const user = await getUser(id);
  return {
    contents: [{
      uri: uri.toString(),
      mimeType: 'application/json',
      text: JSON.stringify(user)
    }]
  };
});
```
