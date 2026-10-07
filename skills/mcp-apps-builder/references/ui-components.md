# Leanmcp UI Components Reference

## ToolButton

Button that executes MCP tools.

```tsx
import { ToolButton } from '@leanmcp/ui';

// Basic
<ToolButton tool="refresh-data">Refresh</ToolButton>

// With arguments and toast
<ToolButton 
  tool="save-item" 
  args={{ id: 1 }}
  resultDisplay="toast"
  successMessage="Saved!"
>
  Save
</ToolButton>

// With confirmation
<ToolButton
  tool="delete-item"
  args={{ id: item.id }}
  confirm={{
    title: 'Delete Item?',
    description: 'This cannot be undone.',
    confirmText: 'Delete',
    confirmVariant: 'destructive'
  }}
  variant="destructive"
  onToolSuccess={() => refetch()}
>
  Delete
</ToolButton>

// Render props
<ToolButton tool="process">
  {({ loading, result }) => (
    loading ? <Spinner /> : result ? 'Done' : 'Process'
  )}
</ToolButton>
```

**Props:**
- `tool` - Tool name (string)
- `args` - Tool arguments
- `resultDisplay` - `'inline'` | `'toast'` | `'modal'` | `'none'`
- `confirm` - Confirmation dialog config
- `variant` - `'default'` | `'destructive'` | `'outline'` | `'ghost'`
- `onToolSuccess` - Success callback
- `onToolError` - Error callback

## ToolForm

Form that submits to a tool.

```tsx
import { ToolForm } from '@leanmcp/ui';

<ToolForm
  toolName="create-user"
  fields={[
    { name: 'name', label: 'Name', type: 'text', required: true },
    { name: 'email', label: 'Email', type: 'email', required: true },
    { name: 'role', label: 'Role', type: 'select', options: [
      { value: 'user', label: 'User' },
      { value: 'admin', label: 'Admin' }
    ]},
    { name: 'bio', label: 'Bio', type: 'textarea' },
    { name: 'notify', label: 'Send notifications', type: 'switch' },
    { name: 'priority', label: 'Priority', type: 'slider', min: 1, max: 10 }
  ]}
  submitText="Create User"
  showSuccessToast
  resetOnSuccess
  onSuccess={(user) => console.log('Created:', user)}
/>
```

**Field types:** `text`, `number`, `email`, `password`, `textarea`, `select`, `checkbox`, `switch`, `slider`, `date`

## ToolDataGrid

Server-paginated table.

```tsx
import { ToolDataGrid } from '@leanmcp/ui';

<ToolDataGrid
  dataTool="listUsers"              // REQUIRED - tool name
  columns={[                        // REQUIRED - column definitions
    { key: 'name', header: 'Name', sortable: true },
    { key: 'email', header: 'Email' },
    { key: 'role', header: 'Role', width: '100px' },
    { 
      key: 'status', 
      header: 'Status', 
      render: (val) => <Badge>{val}</Badge> 
    }
  ]}
  transformData={(result) => ({     // REQUIRED - transform result
    rows: result.users,
    total: result.total
  })}
  pagination                        // Enable pagination
  pageSizes={[10, 25, 50]}
  refreshInterval={30000}           // Auto-refresh (ms)
  showRefresh                       // Show refresh button
  rowActions={[
    { 
      label: 'Edit', 
      tool: 'editUser',
      getArgs: (row) => ({ id: row.id })
    },
    { 
      label: 'Delete', 
      tool: 'deleteUser',
      variant: 'destructive',
      confirm: { title: 'Delete?', description: 'Cannot undo' },
      getArgs: (row) => ({ id: row.id })
    }
  ]}
  getRowKey={(row) => row.id}
  onRowClick={(row) => console.log('Clicked:', row)}
/>
```

**IMPORTANT - Correct prop names:**
- `dataTool` (NOT `toolName`)
- `key` and `header` (NOT `field` and `headerName`)
- `refreshInterval` (NOT `autoRefresh`)

## ToolSelect

Select dropdown with tool options.

```tsx
import { ToolSelect } from '@leanmcp/ui';

// Static options
<ToolSelect
  options={[
    { value: 'asc', label: 'Ascending' },
    { value: 'desc', label: 'Descending' }
  ]}
  onSelectTool="set-sort"
  argName="order"
/>

// Dynamic options from tool
<ToolSelect
  optionsTool="list-categories"
  transformOptions={(r) => r.categories.map(c => ({ 
    value: c.id, 
    label: c.name 
  }))}
  onSelectTool="set-category"
  argName="categoryId"
  placeholder="Select category"
/>
```

## ToolInput

Input with debounced search.

```tsx
import { ToolInput } from '@leanmcp/ui';

// Search input
<ToolInput
  searchTool="search-items"
  argName="query"
  debounce={300}
  placeholder="Search..."
/>

// With autocomplete
<ToolInput
  searchTool="search-users"
  autocomplete
  transformSuggestions={(r) => r.users.map(u => ({
    value: u.id,
    label: u.name,
    description: u.email
  }))}
  onSelect={(user) => setSelectedUser(user.value)}
/>
```

## RequireConnection

Loading guard for MCP connection.

```tsx
import { RequireConnection } from '@leanmcp/ui';

export function Dashboard() {
  return (
    <RequireConnection
      loading={<div>Connecting...</div>}
      error={<div>Connection failed</div>}
    >
      <DashboardContent />
    </RequireConnection>
  );
}
```

## ResourceView

Display MCP resources.

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

## StreamingContent

Render streaming tool data.

```tsx
import { StreamingContent } from '@leanmcp/ui';

<StreamingContent
  toolName="generate-report"
  args={{ id: reportId }}
  renderPartial={(partial) => <div>{partial.progress}%</div>}
  renderComplete={(final) => <ReportView data={final} />}
/>
```

## ToolErrorBoundary

Error boundary with retry.

```tsx
import { ToolErrorBoundary } from '@leanmcp/ui';

<ToolErrorBoundary
  fallback={(error, retry) => (
    <div>
      <p>Error: {error.message}</p>
      <button onClick={retry}>Retry</button>
    </div>
  )}
>
  <ToolHeavyContent />
</ToolErrorBoundary>
```
