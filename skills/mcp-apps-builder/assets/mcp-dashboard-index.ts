import { Tool, Resource, SchemaConstraint, Optional } from '@leanmcp/core';
import { UIApp } from '@leanmcp/ui/server';

/**
 * Example MCP App service with UI
 * Place this file at: mcp/dashboard/index.ts
 */

class CreateItemInput {
  @SchemaConstraint({ description: 'Item name', minLength: 1 })
  name!: string;

  @SchemaConstraint({ description: 'Item value', minimum: 0 })
  value!: number;

  @Optional()
  @SchemaConstraint({ description: 'Item description' })
  description?: string;
}

export class DashboardService {
  private items: any[] = [];

  @Tool({ description: 'View dashboard with all items' })
  @UIApp({ component: './Dashboard' })
  async viewDashboard() {
    return { 
      items: this.items, 
      total: this.items.length 
    };
  }

  @Tool({ description: 'Create a new item', inputClass: CreateItemInput })
  async createItem(input: CreateItemInput) {
    const item = { 
      id: crypto.randomUUID(), 
      ...input, 
      createdAt: new Date().toISOString() 
    };
    this.items.push(item);
    return { success: true, item };
  }

  @Tool({ description: 'Delete an item' })
  async deleteItem(args: { id: string }) {
    const index = this.items.findIndex(i => i.id === args.id);
    if (index === -1) throw new Error('Item not found');
    this.items.splice(index, 1);
    return { success: true };
  }

  @Tool({ description: 'Update an item' })
  async updateItem(args: { id: string; name?: string; value?: number }) {
    const item = this.items.find(i => i.id === args.id);
    if (!item) throw new Error('Item not found');
    
    if (args.name) item.name = args.name;
    if (args.value !== undefined) item.value = args.value;
    item.updatedAt = new Date().toISOString();
    
    return { success: true, item };
  }

  @Resource({ description: 'Dashboard statistics' })
  async stats() {
    return {
      contents: [{
        uri: 'dashboard://stats',
        mimeType: 'application/json',
        text: JSON.stringify({
          total: this.items.length,
          totalValue: this.items.reduce((sum, i) => sum + i.value, 0),
          lastUpdated: new Date().toISOString()
        })
      }]
    };
  }
}
