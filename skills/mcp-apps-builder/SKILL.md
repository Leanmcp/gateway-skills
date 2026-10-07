---
name: mcp-apps-builder
description: Build MCP Apps with interactive React UIs using the Leanmcp UI SDK. Use this skill when users ask for "MCP with UI", "MCP App", "interactive MCP", "leanmcp UI", "MCP dashboard", or want to create rich visual interfaces for their MCP tools. This skill covers @UIApp decorator, React components with useTool/useResource hooks, ToolDataGrid, ToolForm, ToolButton, and ChatGPT Apps support.
---

# MCP Apps Builder Skill

This skill guides you in building MCP Apps - MCP servers with interactive React UIs using the Leanmcp UI SDK.

## When to Use This Skill

- User asks for "MCP with UI"
- User wants "interactive MCP server"
- User mentions "MCP App" or "leanmcp UI"
- User needs "dashboard for MCP tools"
- User wants "visual interface for AI tools"
- User mentions "@leanmcp/ui" or "@UIApp"
- User asks for "ChatGPT App" or "GPT App"

## What is an MCP App?

MCP Apps extend MCP servers to deliver interactive UIs. Apps run in sandboxed iframes and communicate via JSON-RPC over postMessage. When a tool is called, the UI can be displayed alongside the tool response.

## Core Architecture

1. **Service file** (`mcp/*/index.ts`) - Tool methods decorated with `@Tool` AND `@UIApp`
2. **Component file** (`mcp/*/*.tsx`) - React component using `@leanmcp/ui` components
3. **CLI handles the rest** - `leanmcp dev` builds and wraps components with AppProvider

## Required Dependencies

```json
{
  "dependencies": {
    "@leanmcp/core": "^0.4.7",
    "@leanmcp/ui": "^0.3.7",
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "dotenv": "^16.5.0"
  },
  "devDependencies": {
    "@leanmcp/cli": "latest",
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
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
    "jsx": "react-jsx",
    "jsxImportSource": "react",
    "outDir": "./dist",
    "strict": true
  },
  "include": ["**/*.ts", "**/*.tsx", "mcp/**/*.ts", "mcp/**/*.tsx"]
}
```

## Project Structure

```
my-mcp-app/
├── main.ts                    # Entry point
├── mcp/
│   └── products/
│       ├── index.ts           # Service with @Tool + @UIApp
│       └── ProductsDashboard.tsx  # React component
├── package.json
└── tsconfig.json
```

## Two Import Paths (Critical)

| Import | Use In | Contents |
|--------|--------|----------|
| `@leanmcp/ui/server` | Service files (`index.ts`) | `UIApp`, `GPTApp` decorators only |
| `@leanmcp/ui` | Component files (`.tsx`) | React components, hooks, styles |

## @UIApp Decorator

**CRITICAL: @UIApp is a METHOD decorator, not a class decorator!**

### Correct Usage

```typescript
// mcp/products/index.ts
import { Tool } from '@leanmcp/core';
import { UIApp } from '@leanmcp/ui/server';  // Server import!

export class ProductsService {
  @Tool({ description: 'List products' })
  @UIApp({ component: './ProductsDashboard' })  // On method with @Tool
  async listProducts(args: { page?: number }) {
    return { products: [...], total: 100 };
  }
}
```

### WRONG - Never do this

```typescript
// WRONG: @UIApp on class
@UIApp({ component: './Dashboard' })  // WRONG!
export class MyService { ... }
```

### @UIApp Options

```typescript
@UIApp({ 
  component: './ComponentName',  // Required: relative path (string, not import)
  uri: 'ui://custom/path',       // Optional: custom URI
  title: 'Page Title',           // Optional
  styles: 'body { ... }'         // Optional: additional CSS
})
```

## React Component Development

### Basic Component

```tsx
// mcp/products/ProductsDashboard.tsx
import { RequireConnection, ToolDataGrid } from '@leanmcp/ui';
import '@leanmcp/ui/styles.css';

export function ProductsDashboard() {
  return (
    <RequireConnection loading={<div>Loading...</div>}>
      <div style={{ padding: '20px' }}>
        <h1>Products</h1>
        <ToolDataGrid
          dataTool="listProducts"
          columns={[
            { key: 'name', header: 'Name', sortable: true },
            { key: 'price', header: 'Price' }
          ]}
          transformData={(result) => ({
            rows: result.products,
            total: result.total
          })}
          pagination
        />
      </div>
    </RequireConnection>
  );
}
```

### Critical Rules

1. **NEVER wrap with AppProvider** - CLI does this automatically
2. **Always use RequireConnection** - Shows loading until host connects
3. **Import styles** - `import '@leanmcp/ui/styles.css'`
4. **Export matching name** - File `Foo.tsx` exports `function Foo()`
5. **Use string paths** - `'./Component'` not direct import

## Core Components

### ToolButton

Button that calls a tool with loading state and confirmation:

```tsx
import { ToolButton } from '@leanmcp/ui';

<ToolButton 
  tool="delete-item" 
  args={{ id: item.id }}
  confirm={{
    title: 'Delete Item?',
    description: 'This action cannot be undone.'
  }}
  variant="destructive"
  resultDisplay="toast"
  onToolSuccess={() => refetch()}
>
  Delete
</ToolButton>
```

**Props:**
- `tool` - Tool name to call
- `args` - Arguments to pass
- `confirm` - Confirmation dialog config
- `variant` - `default`, `destructive`, `outline`, `ghost`
- `resultDisplay` - `toast`, `inline`, `none`
- `onToolSuccess` / `onToolError` - Callbacks

### ToolForm

Form that submits to a tool:

```tsx
import { ToolForm } from '@leanmcp/ui';

<ToolForm
  toolName="create-product"
  fields={[
    { name: 'name', label: 'Product Name', type: 'text', required: true },
    { name: 'price', label: 'Price', type: 'number', min: 0 },
    { name: 'category', label: 'Category', type: 'select', options: [
      { value: 'electronics', label: 'Electronics' },
      { value: 'clothing', label: 'Clothing' }
    ]},
    { name: 'inStock', label: 'In Stock', type: 'switch' }
  ]}
  submitText="Create Product"
  showSuccessToast
  resetOnSuccess
  onSuccess={(result) => console.log('Created:', result)}
/>
```

**Field types:** `text`, `number`, `email`, `textarea`, `select`, `switch`, `slider`, `date`

### ToolDataGrid

Server-paginated table with sorting and row actions:

```tsx
import { ToolDataGrid } from '@leanmcp/ui';

<ToolDataGrid
  dataTool="listProducts"           // NOT 'toolName'!
  columns={[
    { key: 'name', header: 'Name', sortable: true },  // NOT 'field'/'headerName'!
    { key: 'price', header: 'Price', render: (v) => `$${v.toFixed(2)}` }
  ]}
  transformData={(r) => ({ rows: r.products, total: r.total })}
  pagination
  pageSize={20}
  refreshInterval={30000}           // NOT 'autoRefresh'!
  rowActions={[
    { 
      label: 'Edit', 
      tool: 'edit-product',
      getArgs: (row) => ({ id: row.id })
    },
    {
      label: 'Delete',
      tool: 'delete-product',
      getArgs: (row) => ({ id: row.id }),
      variant: 'destructive',
      confirm: { title: 'Delete?', description: 'Cannot undo' }
    }
  ]}
/>
```

**Common Mistakes to Avoid:**
- Use `dataTool` not `toolName`
- Use `key`/`header` not `field`/`headerName`
- Use `refreshInterval` not `autoRefresh`
- Always provide `transformData`

### ToolSelect

Select dropdown with tool-based options:

```tsx
import { ToolSelect } from '@leanmcp/ui';

<ToolSelect
  optionsTool="list-categories"
  transformOptions={(r) => r.categories.map(c => ({ value: c.id, label: c.name }))}
  onSelectTool="set-category"
  argName="categoryId"
  placeholder="Select category"
/>
```

### ResourceView

Display MCP resources with auto-refresh:

```tsx
import { ResourceView } from '@leanmcp/ui';

<ResourceView
  uri="config://settings"
  refreshInterval={5000}
  render={(data) => (
    <pre>{JSON.stringify(data, null, 2)}</pre>
  )}
/>
```

## Core Hooks

### useTool

Call MCP tools programmatically:

```tsx
import { useTool } from '@leanmcp/ui';

function MyComponent() {
  const { call, result, loading, error } = useTool('get-data', {
    retry: 3,
    transform: (r) => r.data
  });
  
  useEffect(() => {
    call({ filter: 'active' });
  }, []);
  
  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error.message}</div>;
  
  return <div>{result?.value}</div>;
}
```

### useResource

Read MCP resources:

```tsx
import { useResource } from '@leanmcp/ui';

function ConfigView() {
  const { data, loading, refresh } = useResource('config://settings', {
    refreshInterval: 5000
  });
  
  return (
    <div>
      {loading && <p>Loading...</p>}
      {data && <pre>{JSON.stringify(data, null, 2)}</pre>}
      <button onClick={refresh}>Refresh</button>
    </div>
  );
}
```

### useHostContext

Access host environment (theme, viewport):

```tsx
import { useHostContext } from '@leanmcp/ui';

function ThemedComponent() {
  const { theme, viewport } = useHostContext();
  
  return (
    <div className={theme === 'dark' ? 'dark-mode' : 'light-mode'}>
      Content
    </div>
  );
}
```

## GPT Apps SDK Hooks

For ChatGPT Apps integration:

### useToolOutput

Access `structuredContent` from tool response:

```tsx
import { useToolOutput } from '@leanmcp/ui';

function ChannelsView() {
  const toolOutput = useToolOutput<{ channels: Channel[] }>();
  
  if (!toolOutput?.channels) return <div>No channels</div>;
  
  return (
    <ul>
      {toolOutput.channels.map(ch => <li key={ch.id}>{ch.name}</li>)}
    </ul>
  );
}
```

### useWidgetState

Persistent state across sessions:

```tsx
import { useWidgetState } from '@leanmcp/ui';

function FilteredView() {
  const [state, setState] = useWidgetState<{ filter: string }>({ filter: 'all' });
  
  return (
    <select 
      value={state.filter}
      onChange={(e) => setState({ filter: e.target.value })}
    >
      <option value="all">All</option>
      <option value="active">Active</option>
    </select>
  );
}
```

## @GPTApp Decorator

For ChatGPT Apps specifically:

```typescript
import { Tool } from '@leanmcp/core';
import { GPTApp } from '@leanmcp/ui/server';

export class SlackService {
  @Tool({ description: 'Compose Slack message' })
  @GPTApp({
    component: './SlackComposer',
    name: 'slack-composer'
  })
  async composeMessage() {
    return { channels: [...] };
  }
}
```

## Complete Example

### Service File

```typescript
// mcp/dashboard/index.ts
import { Tool, Resource, SchemaConstraint } from '@leanmcp/core';
import { UIApp } from '@leanmcp/ui/server';

class CreateItemInput {
  @SchemaConstraint({ description: 'Item name', minLength: 1 })
  name!: string;

  @SchemaConstraint({ description: 'Item value', minimum: 0 })
  value!: number;
}

export class DashboardService {
  private items: any[] = [];

  @Tool({ description: 'View dashboard with items' })
  @UIApp({ component: './Dashboard' })
  async viewDashboard() {
    return { items: this.items, total: this.items.length };
  }

  @Tool({ description: 'Create a new item', inputClass: CreateItemInput })
  async createItem(input: CreateItemInput) {
    const item = { id: crypto.randomUUID(), ...input, createdAt: new Date().toISOString() };
    this.items.push(item);
    return { success: true, item };
  }

  @Tool({ description: 'Delete an item' })
  async deleteItem(args: { id: string }) {
    this.items = this.items.filter(i => i.id !== args.id);
    return { success: true };
  }

  @Resource({ description: 'Dashboard statistics' })
  async stats() {
    return {
      contents: [{
        uri: 'dashboard://stats',
        mimeType: 'application/json',
        text: JSON.stringify({
          total: this.items.length,
          totalValue: this.items.reduce((sum, i) => sum + i.value, 0)
        })
      }]
    };
  }
}
```

### Component File

```tsx
// mcp/dashboard/Dashboard.tsx
import { RequireConnection, ToolDataGrid, ToolForm, ToolButton, useResource } from '@leanmcp/ui';
import '@leanmcp/ui/styles.css';

export function Dashboard() {
  const { data: stats, refresh } = useResource('dashboard://stats');

  return (
    <RequireConnection loading={<div>Connecting...</div>}>
      <div style={{ padding: '20px', fontFamily: 'system-ui' }}>
        <h1>Dashboard</h1>
        
        {/* Stats */}
        {stats && (
          <div style={{ marginBottom: '20px', padding: '10px', background: '#f5f5f5', borderRadius: '8px' }}>
            <p>Total Items: {stats.total}</p>
            <p>Total Value: ${stats.totalValue}</p>
          </div>
        )}

        {/* Create Form */}
        <div style={{ marginBottom: '20px' }}>
          <h2>Create Item</h2>
          <ToolForm
            toolName="createItem"
            fields={[
              { name: 'name', label: 'Name', type: 'text', required: true },
              { name: 'value', label: 'Value', type: 'number', min: 0, required: true }
            ]}
            submitText="Create"
            showSuccessToast
            resetOnSuccess
            onSuccess={() => refresh()}
          />
        </div>

        {/* Items Table */}
        <h2>Items</h2>
        <ToolDataGrid
          dataTool="viewDashboard"
          columns={[
            { key: 'name', header: 'Name', sortable: true },
            { key: 'value', header: 'Value', render: (v) => `$${v}` },
            { key: 'createdAt', header: 'Created', render: (v) => new Date(v).toLocaleDateString() }
          ]}
          transformData={(r) => ({ rows: r.items, total: r.total })}
          rowActions={[
            {
              label: 'Delete',
              tool: 'deleteItem',
              getArgs: (row) => ({ id: row.id }),
              variant: 'destructive',
              confirm: { title: 'Delete item?', description: 'This cannot be undone.' }
            }
          ]}
          pagination
          showRefresh
          getRowKey={(row) => row.id}
        />
      </div>
    </RequireConnection>
  );
}
```

## Theming

Apps automatically adapt to host theme via CSS variables:

```css
:root {
  --color-background-primary: #ffffff;
  --color-text-primary: #171717;
}

.dark {
  --color-background-primary: #0a0a0a;
  --color-text-primary: #fafafa;
}
```

Access in React:

```tsx
const { theme } = useHostContext();
const isDark = theme === 'dark';
```

## Editing Guidelines

### DO

- Create `.tsx` files alongside service `index.ts` files
- Use `@UIApp` on methods paired with `@Tool`
- Import from `@leanmcp/ui/server` in service files
- Import from `@leanmcp/ui` in component files
- Always wrap content in `RequireConnection`
- Import `@leanmcp/ui/styles.css`

### DON'T

- Wrap components with AppProvider
- Put `@UIApp` on class
- Use direct imports in `@UIApp({ component: ... })`
- Use wrong prop names (toolName, field, autoRefresh)
- Add terminal commands in responses
