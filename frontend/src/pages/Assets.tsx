import { Link, useParams } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { BookNav } from '@/components/books/BookNav';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { useAssets, useGenerateAssets } from '@/hooks/useCreator';
import { Sparkles } from 'lucide-react';

const LABELS: Record<string, string> = {
  description: 'Book description',
  newsletter: 'Newsletter',
  social_post: 'Social post',
  podcast_pitch: 'Podcast pitch',
  video_script: 'Video script',
};

export function AssetsPage() {
  const { bookId = '' } = useParams();
  const assets = useAssets(bookId);
  const generate = useGenerateAssets(bookId);

  if (assets.isLoading) return <Skeleton className="h-48 w-full" />;
  if (assets.error) return <ApiErrorAlert error={assets.error} />;

  return (
    <div>
      <BookNav bookId={bookId} />
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Assets</h1>
          <p className="text-muted-foreground">
            Five structured outputs with source references and assumptions.
          </p>
        </div>
        <Button onClick={() => generate.mutate()} disabled={generate.isPending}>
          {generate.isPending ? 'Generating… this can take a couple of minutes' : 'Generate assets'}
        </Button>
      </div>

      {assets.data?.length ? (
        <div className="space-y-4">
          {assets.data.map((asset) => (
            <Card key={asset.id}>
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle>{LABELS[asset.type] || asset.type}</CardTitle>
                <div className="flex gap-2">
                  {asset.applied_preference ? (
                    <Badge variant="secondary">Applied author preference</Badge>
                  ) : null}
                  <Badge variant="outline">{asset.platform}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <pre className="whitespace-pre-wrap rounded-md border bg-muted/40 p-3 text-xs">
                  {asset.content}
                </pre>
                <p className="text-muted-foreground">
                  Assumptions: {asset.assumptions.join(' · ') || 'None'}
                </p>
                <p className="text-muted-foreground">
                  Source:{' '}
                  {asset.source_references
                    .map((ref) => String(ref.quote || ref.note || ''))
                    .join(' ')}
                </p>
              </CardContent>
            </Card>
          ))}
          <Link to={`/books/${bookId}/governance`} className="text-sm text-primary underline">
            Continue to governance review
          </Link>
        </div>
      ) : (
        <EmptyState
          icon={Sparkles}
          title="No assets yet"
          description="Generate from the uploaded excerpt. The Mind is called from the API when configured."
        />
      )}
    </div>
  );
}
