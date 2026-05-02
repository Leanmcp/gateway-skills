import { 
  RequireConnection, 
  ToolDataGrid, 
  ToolForm, 
  ToolButton,
  useResource 
} from '@leanmcp/ui';
import '@leanmcp/ui/styles.css';

/**
 * Dashboard UI Component
 * Place this file at: mcp/dashboard/Dashboard.tsx
 */
export function Dashboard() {
  const { data: stats, refresh: refreshStats } = useResource('dashboard://stats');

  return (
    <RequireConnection loading={<div style={{ padding: '20px' }}>Connecting...</div>}>
      <div style={{ 
        padding: '20px', 
        fontFamily: 'system-ui, -apple-system, sans-serif',
        maxWidth: '1200px',
        margin: '0 auto'
      }}>
        <h1 style={{ marginBottom: '20px' }}>Dashboard</h1>
        
        {/* Stats Section */}
        {stats && (
          <div style={{ 
            display: 'flex', 
            gap: '20px', 
            marginBottom: '30px' 
          }}>
            <div style={{
              padding: '20px',
              background: '#f0f9ff',
              borderRadius: '8px',
              flex: 1
            }}>
              <div style={{ fontSize: '14px', color: '#666' }}>Total Items</div>
              <div style={{ fontSize: '32px', fontWeight: 'bold' }}>{stats.total}</div>
            </div>
            <div style={{
              padding: '20px',
              background: '#f0fdf4',
              borderRadius: '8px',
              flex: 1
            }}>
              <div style={{ fontSize: '14px', color: '#666' }}>Total Value</div>
              <div style={{ fontSize: '32px', fontWeight: 'bold' }}>${stats.totalValue}</div>
            </div>
          </div>
        )}

        {/* Create Form */}
        <div style={{ 
          marginBottom: '30px',
          padding: '20px',
          background: '#fafafa',
          borderRadius: '8px'
        }}>
          <h2 style={{ marginBottom: '15px', fontSize: '18px' }}>Create New Item</h2>
          <ToolForm
            toolName="createItem"
            fields={[
              { 
                name: 'name', 
                label: 'Name', 
                type: 'text', 
                required: true,
                placeholder: 'Enter item name'
              },
              { 
                name: 'value', 
                label: 'Value ($)', 
                type: 'number', 
                min: 0, 
                required: true,
                placeholder: '0'
              },
              { 
                name: 'description', 
                label: 'Description', 
                type: 'textarea',
                placeholder: 'Optional description'
              }
            ]}
            submitText="Create Item"
            showSuccessToast
            resetOnSuccess
            onSuccess={() => refreshStats()}
          />
        </div>

        {/* Items Table */}
        <div>
          <h2 style={{ marginBottom: '15px', fontSize: '18px' }}>Items</h2>
          <ToolDataGrid
            dataTool="viewDashboard"
            columns={[
              { key: 'name', header: 'Name', sortable: true },
              { 
                key: 'value', 
                header: 'Value', 
                render: (v) => `$${Number(v).toFixed(2)}`,
                align: 'right'
              },
              { 
                key: 'description', 
                header: 'Description',
                render: (v) => v || '-'
              },
              { 
                key: 'createdAt', 
                header: 'Created', 
                render: (v) => new Date(v as string).toLocaleDateString()
              }
            ]}
            transformData={(result) => ({
              rows: result.items,
              total: result.total
            })}
            rowActions={[
              {
                label: 'Delete',
                tool: 'deleteItem',
                getArgs: (row) => ({ id: row.id }),
                variant: 'destructive',
                confirm: { 
                  title: 'Delete item?', 
                  description: 'This action cannot be undone.' 
                }
              }
            ]}
            pagination
            pageSizes={[5, 10, 25]}
            showRefresh
            getRowKey={(row) => row.id}
            emptyContent={<div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>No items yet. Create one above!</div>}
          />
        </div>
      </div>
    </RequireConnection>
  );
}
