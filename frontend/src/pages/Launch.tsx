import { useParams } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { BookNav } from '@/components/books/BookNav';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { useCreateCampaign, useLatestCampaign } from '@/hooks/useCreator';
import { Calendar } from 'lucide-react';

const PHASES = ['pre-launch', 'launch_week', 'post-launch'] as const;

export function LaunchPage() {
  const { bookId = '' } = useParams();
  const campaign = useLatestCampaign(bookId);
  const create = useCreateCampaign(bookId);

  if (campaign.isLoading) return <Skeleton className="h-48 w-full" />;
  if (campaign.error) return <ApiErrorAlert error={campaign.error} />;

  const tasks = campaign.data?.tasks || [];

  return (
    <div>
      <BookNav bookId={bookId} />
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Launch board</h1>
          <p className="text-muted-foreground">
            Approved assets are assigned to tasks. Nothing is auto-published.
          </p>
        </div>
        <Button onClick={() => create.mutate()} disabled={create.isPending}>
          Create launch plan
        </Button>
      </div>

      {campaign.data ? (
        <div className="grid gap-4 md:grid-cols-3">
          {PHASES.map((phase) => (
            <Card key={phase}>
              <CardHeader>
                <CardTitle className="capitalize">{phase.replace('_', ' ')}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2">
                {tasks
                  .filter((task) => task.phase === phase)
                  .map((task) => (
                    <div key={task.id} className="rounded-md border p-3 text-sm">
                      <p className="font-medium">{task.channel}</p>
                      <div className="mt-1 flex gap-2">
                        <Badge variant="outline">{task.approval_status}</Badge>
                        <Badge variant="secondary">{task.execution_status}</Badge>
                      </div>
                      {!task.asset_id ? (
                        <p className="mt-1 text-xs text-muted-foreground">
                          No approved asset assigned yet.
                        </p>
                      ) : null}
                    </div>
                  ))}
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Calendar}
          title="No launch plan"
          description="Create a board after you have approved marketing assets."
        />
      )}
    </div>
  );
}
