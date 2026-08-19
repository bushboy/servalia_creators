import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { BookNav } from '@/components/books/BookNav';
import { EvaluationResultView } from '@/components/evaluation/EvaluationResultView';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import {
  useApproveAsset,
  useAssets,
  useEvaluateAsset,
  useRejectAsset,
  useReviseAsset,
} from '@/hooks/useCreator';
import { Shield } from 'lucide-react';

const LABELS: Record<string, string> = {
  description: 'Book description',
  newsletter: 'Newsletter',
  social_post: 'Social post',
  podcast_pitch: 'Podcast pitch',
  video_script: 'Video script',
};

export function GovernancePage() {
  const { bookId = '' } = useParams();
  const assets = useAssets(bookId);
  const evaluate = useEvaluateAsset(bookId);
  const approve = useApproveAsset(bookId);
  const reject = useRejectAsset(bookId);
  const revise = useReviseAsset(bookId);
  const [corrections, setCorrections] = useState<Record<string, string>>({});

  if (assets.isLoading) return <Skeleton className="h-48 w-full" />;
  if (assets.error) return <ApiErrorAlert error={assets.error} />;

  return (
    <div>
      <BookNav bookId={bookId} />
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Governance</h1>
        <p className="text-muted-foreground">
          Creator-configured governance review. Allow, Review, or Block — not legal
          clearance.
        </p>
      </div>

      {assets.data?.length ? (
        <div className="space-y-6">
          {assets.data.map((asset) => (
            <Card key={asset.id}>
              <CardHeader className="flex flex-row items-center justify-between gap-2">
                <CardTitle>{LABELS[asset.type] || asset.type}</CardTitle>
                <Badge variant="outline">{asset.governance_status}</Badge>
              </CardHeader>
              <CardContent className="space-y-4">
                {asset.applied_preference ? (
                  <p className="text-sm font-medium">Applied author preference</p>
                ) : null}
                {asset.evaluation ? (
                  <EvaluationResultView result={asset.evaluation} />
                ) : (
                  <p className="text-sm text-muted-foreground">Not assessed yet.</p>
                )}
                <Textarea
                  placeholder="Recommended rewrite / author correction"
                  value={corrections[asset.id] || ''}
                  onChange={(event) =>
                    setCorrections((current) => ({
                      ...current,
                      [asset.id]: event.target.value,
                    }))
                  }
                />
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    onClick={() => evaluate.mutate(asset.id)}
                    disabled={evaluate.isPending}
                  >
                    Run review
                  </Button>
                  <Button
                    onClick={() => approve.mutate(asset.id)}
                    disabled={approve.isPending}
                  >
                    Approve
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() =>
                      reject.mutate({
                        assetId: asset.id,
                        note: corrections[asset.id] || 'Rejected',
                      })
                    }
                  >
                    Reject
                  </Button>
                  <Button
                    variant="outline"
                    onClick={() =>
                      revise.mutate({
                        assetId: asset.id,
                        correction:
                          corrections[asset.id] ||
                          'Do not use guaranteed results or aggressive sales language.',
                      })
                    }
                  >
                    Revise
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Shield}
          title="No assets to review"
          description="Generate assets first, then run a creator-configured governance review."
        />
      )}
    </div>
  );
}
