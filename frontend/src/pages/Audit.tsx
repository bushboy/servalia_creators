import { useState } from 'react';
import { useAuditEvents, useVerticals } from '@/hooks/useQueries';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Loader2 } from 'lucide-react';

const ACTIONS = [
  'author_created',
  'author_updated',
  'mind_message',
  'book_created',
  'edition_created',
  'document_uploaded',
  'assets_generated',
  'asset_evaluated',
  'asset_approved',
  'asset_rejected',
  'asset_revised',
  'package_built',
  'campaign_created',
  'demo_reset',
];
const LIMITS = [10, 25, 50, 100];

export function AuditPage() {
  const { data: verticals } = useVerticals();

  const [customerId, setCustomerId] = useState('');
  const [vertical, setVertical] = useState('');
  const [action, setAction] = useState('');
  const [agentId, setAgentId] = useState('');
  const [limit, setLimit] = useState(25);

  const [filters, setFilters] = useState({
    customer_id: '',
    vertical: '',
    action: '',
    agent_id: '',
    limit: 25,
  });

  const { data: events, isLoading, error } = useAuditEvents(filters);

  function handleSearch(e: React.FormEvent) {
    e.preventDefault();
    setFilters({
      customer_id: customerId,
      vertical,
      action,
      agent_id: agentId,
      limit,
    });
  }

  return (
    <div>
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Audit log</h1>
        <p className="text-muted-foreground">
          Filterable history of recorded events.
        </p>
      </div>

      <form
        onSubmit={handleSearch}
        className="mb-6 grid gap-4 rounded-lg border bg-card p-4 md:grid-cols-5"
      >
        <Input
          placeholder="Author ID"
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
        />
        <select
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          value={vertical}
          onChange={(e) => setVertical(e.target.value)}
        >
          <option value="">All verticals</option>
          {verticals?.map((v) => (
            <option key={v.name} value={v.name}>
              {v.name}
            </option>
          ))}
        </select>
        <select
          className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
          value={action}
          onChange={(e) => setAction(e.target.value)}
        >
          <option value="">All actions</option>
          {ACTIONS.map((a) => (
            <option key={a} value={a}>
              {a}
            </option>
          ))}
        </select>
        <Input
          placeholder="Agent ID"
          value={agentId}
          onChange={(e) => setAgentId(e.target.value)}
        />
        <div className="flex items-center gap-2">
          <select
            className="flex h-10 w-24 rounded-md border border-input bg-background px-3 py-2 text-sm"
            value={limit}
            onChange={(e) => setLimit(Number(e.target.value))}
          >
            {LIMITS.map((l) => (
              <option key={l} value={l}>
                {l}
              </option>
            ))}
          </select>
          <Button type="submit" className="flex-1">
            Search
          </Button>
        </div>
      </form>

      {isLoading ? (
        <div className="flex h-64 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </div>
      ) : error ? (
        <div className="rounded-lg border border-destructive/50 p-4 text-destructive">
          Failed to load audit events: {error.message}
        </div>
      ) : !events || events.length === 0 ? (
        <div className="rounded-lg border border-dashed p-8 text-center text-muted-foreground">
          No audit events found.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border">
          <table className="w-full text-sm">
            <thead className="bg-muted text-muted-foreground">
              <tr>
                <th className="px-4 py-2 text-left font-medium">Timestamp</th>
                <th className="px-4 py-2 text-left font-medium">Action</th>
                <th className="px-4 py-2 text-left font-medium">Vertical</th>
                <th className="px-4 py-2 text-left font-medium">Customer</th>
                <th className="px-4 py-2 text-left font-medium">Agent</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {events.map((event) => (
                <tr key={event.event_id}>
                  <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                    {new Date(event.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant="outline">{event.action}</Badge>
                  </td>
                  <td className="px-4 py-3">{event.vertical}</td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {event.customer_id}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs">
                    {event.agent_id}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
