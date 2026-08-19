import { Button } from '@/components/ui/button';
import { getApiErrorMessage } from '@/lib/apiError';
import { cn } from '@/lib/utils';
import { AlertTriangle } from 'lucide-react';

interface ApiErrorAlertProps {
  title?: string;
  error?: unknown;
  onRetry?: () => void;
  className?: string;
}

export function ApiErrorAlert({
  title = 'Something went wrong',
  error,
  onRetry,
  className,
}: ApiErrorAlertProps) {
  return (
    <div
      className={cn(
        'rounded-lg border border-destructive/50 bg-destructive/5 p-4 text-destructive',
        className
      )}
      role="alert"
      aria-live="assertive"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0" aria-hidden="true" />
        <div className="flex-1">
          <h3 className="font-medium">{title}</h3>
          <p className="mt-1 text-sm">
            {getApiErrorMessage(error, 'An unexpected error occurred.')}
          </p>
          {onRetry && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onRetry}
              className="mt-3"
            >
              Try again
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
