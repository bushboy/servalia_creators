import { useState, type ElementType } from 'react';
import { Link } from 'react-router-dom';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';
import { resetDemo } from '@/lib/api/creator';
import {
  useJobs,
  useRetryJobMutation,
  useSystemEvents,
} from '@/hooks/useQueries';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  RefreshCw,
  Server,
  ShieldAlert,
  XCircle,
} from 'lucide-react';
import type { Job, SystemEvent } from '@/types';

const STATUS_LABELS: Record<string, string> = {
  pending: 'Pending',
  running: 'Running',
  completed: 'Completed',
  failed: 'Failed',
};

const STATUS_ICONS: Record<string, ElementType> = {
  pending: Clock,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
};

function SeverityBadge({ severity }: { severity: string }) {
  const classes =
    severity === 'high'
      ? 'bg-destructive/10 text-destructive'
      : severity === 'medium'
        ? 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400'
        : 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400';
  return (
    <span className={`rounded-full px-2 py-0.5 text-xs font-medium ${classes}`}>
      {severity}
    </span>
  );
}

function ActionableCards({ events }: { events: SystemEvent[] }) {
  const counts = events.reduce(
    (acc, event) => {
      acc[event.event_type] = (acc[event.event_type] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>
  );

  const cards = [
    {
      key: 'failed_job',
      label: 'Failed jobs',
      icon: XCircle,
      color: 'text-destructive',
    },
    {
      key: 'stale_audit',
      label: 'Stale audits',
      icon: Clock,
      color: 'text-amber-500',
    },
    {
      key: 'auth_anomaly',
      label: 'Auth anomalies',
      icon: ShieldAlert,
      color: 'text-orange-500',
    },
    {
      key: 'api_failure',
      label: 'API failures',
      icon: Server,
      color: 'text-rose-500',
    },
    {
      key: 'model_failure',
      label: 'Model failures',
      icon: AlertTriangle,
      color: 'text-yellow-500',
    },
  ];

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {cards.map(({ key, label, icon: Icon, color }) => (
        <Card key={key}>
          <CardContent className="flex items-center gap-4 p-4">
            <Icon className={`h-6 w-6 ${color}`} />
            <div>
              <p className="text-sm text-muted-foreground">{label}</p>
              <p className="text-2xl font-semibold">{counts[key] || 0}</p>
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

function JobRow({ job }: { job: Job }) {
  const retry = useRetryJobMutation();
  const Icon = STATUS_ICONS[job.status] || Activity;
  const isSpinning = job.status === 'running';

  return (
    <div className="flex flex-col gap-2 border-b p-4 last:border-b-0 sm:flex-row sm:items-center sm:justify-between">
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <Icon className={`h-4 w-4 ${isSpinning ? 'animate-spin' : ''}`} />
          <p className="font-medium">{job.job_type}</p>
          <Badge variant={job.status === 'failed' ? 'destructive' : 'secondary'}>
            {STATUS_LABELS[job.status] || job.status}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">
          {job.retry_count} / {job.max_retries} retries
          {job.started_at ? ` • started ${new Date(job.started_at).toLocaleString()}` : ''}
        </p>
        {job.last_error && (
          <p className="text-xs text-destructive">{job.last_error}</p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground">
          {new Date(job.created_at).toLocaleString()}
        </span>
        {job.status === 'failed' && (
          <Button
            size="sm"
            variant="outline"
            onClick={() => retry.mutate(job.job_id)}
            disabled={retry.isPending}
          >
            {retry.isPending ? (
              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
            ) : (
              <RefreshCw className="mr-2 h-3 w-3" />
            )}
            Retry
          </Button>
        )}
      </div>
    </div>
  );
}

export function SystemSettings() {
  const [status, setStatus] = useState('');
  const queryClient = useQueryClient();
  const demoReset = useMutation({
    mutationFn: resetDemo,
    onSuccess: () => {
      void queryClient.invalidateQueries();
      toast.success('Demo seed restored.');
    },
    onError: () => toast.error('Could not reset demo data.'),
  });
  const {
    data: events,
    isLoading: eventsLoading,
    error: eventsError,
  } = useSystemEvents();
  const { data: jobs, isLoading: jobsLoading, error: jobsError } = useJobs(status);

  if (eventsError || jobsError) {
    return (
      <div className="rounded-lg border border-destructive/50 p-4 text-destructive">
        Failed to load system health: {(eventsError || jobsError)?.message}
      </div>
    );
  }

  const loading = eventsLoading || jobsLoading;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">System health</h1>
        <p className="text-muted-foreground">
          Monitor jobs, stale audits, and actionable system signals.
        </p>
        <Button
          className="mt-3"
          variant="outline"
          onClick={() => demoReset.mutate()}
          disabled={demoReset.isPending}
        >
          Restore demo seed
        </Button>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <Skeleton key={i} className="h-24" />
          ))}
        </div>
      ) : (
        <ActionableCards events={events || []} />
      )}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Actionable events</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : !events || events.length === 0 ? (
            <EmptyState
              icon={CheckCircle2}
              title="All clear"
              description="No actionable system events right now."
            />
          ) : (
            <div className="divide-y rounded-md border">
              {events.map((event) => (
                <div
                  key={event.event_id}
                  className="flex flex-col gap-1 p-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-medium">{event.event_type}</span>
                      <SeverityBadge severity={event.severity} />
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {event.message}
                    </p>
                  </div>
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    {new Date(event.occurred_at).toLocaleString()}
                    {event.link && (
                    <Link
                      to={event.link}
                      className="text-sm font-medium text-primary hover:underline"
                    >
                      View
                    </Link>
                  )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Jobs</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="mb-4 flex flex-col gap-4 sm:flex-row sm:items-center">
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
            >
              <option value="">All statuses</option>
              {Object.entries(STATUS_LABELS).map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
            </select>
          </div>

          {jobsLoading ? (
            <div className="space-y-3">
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
              <Skeleton className="h-12 w-full" />
            </div>
          ) : !jobs || jobs.length === 0 ? (
            <EmptyState
              icon={Activity}
              title="No jobs"
              description="Background jobs will appear here once they are enqueued."
            />
          ) : (
            <div className="divide-y rounded-md border">
              {jobs.map((job) => (
                <JobRow key={job.job_id} job={job} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
