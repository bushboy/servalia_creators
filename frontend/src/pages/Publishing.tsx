import { useParams } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { BookNav } from '@/components/books/BookNav';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { useAssets, useEditions, usePublishingStatus } from '@/hooks/useCreator';
import {
  downloadIngramPackage,
  downloadKdpPackage,
} from '@/lib/api/creator';
import { getApiErrorMessage } from '@/lib/apiError';
import { toast } from 'sonner';
import { Package } from 'lucide-react';

export function PublishingPage() {
  const { bookId = '' } = useParams();
  const editions = useEditions(bookId);
  const assets = useAssets(bookId);
  const status = usePublishingStatus(bookId);
  const description = assets.data?.find((asset) => asset.type === 'description');
  const gated =
    !description ||
    description.approval_status !== 'approved' ||
    description.governance_status === 'block';

  if (editions.isLoading || assets.isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }
  if (editions.error) return <ApiErrorAlert error={editions.error} />;

  async function download(kind: 'kdp' | 'ingram', editionId: string) {
    try {
      if (kind === 'kdp') await downloadKdpPackage(editionId);
      else await downloadIngramPackage(editionId);
      toast.success('Package downloaded.');
    } catch (error) {
      toast.error(getApiErrorMessage(error, 'Could not build package'));
    }
  }

  return (
    <div>
      <BookNav bookId={bookId} />
      <div className="mb-6">
        <h1 className="text-2xl font-bold tracking-tight">Publishing centre</h1>
        <p className="text-muted-foreground">
          Download KDP and IngramSpark packages. CreatorTrust prepares the files; you
          remain the operator.
        </p>
      </div>

      {gated ? (
        <p className="mb-4 text-sm text-amber-800 dark:text-amber-200">
          Approve the book description (governance not Block) before packages can be
          built.
        </p>
      ) : null}

      {editions.data?.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {editions.data.map((edition) => (
            <Card key={edition.id}>
              <CardHeader>
                <CardTitle className="capitalize">{edition.format}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3 text-sm">
                <p>ISBN: {edition.isbn || '—'}</p>
                <p>Status: {edition.publishing_status}</p>
                <p>Proof review: {edition.proof_review_status}</p>
                <div className="flex flex-wrap gap-2">
                  <Button
                    disabled={gated}
                    onClick={() => download('kdp', edition.id)}
                  >
                    Download KDP ZIP
                  </Button>
                  <Button
                    variant="outline"
                    disabled={gated}
                    onClick={() => download('ingram', edition.id)}
                  >
                    Download IngramSpark ZIP
                  </Button>
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      status.mutate({
                        editionId: edition.id,
                        payload: { publishing_status: 'prepared' },
                      })
                    }
                  >
                    Mark prepared
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() =>
                      status.mutate({
                        editionId: edition.id,
                        payload: { proof_review_status: 'in_review' },
                      })
                    }
                  >
                    Proof in review
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={Package}
          title="No editions"
          description="Add paperback and ebook editions on the book workspace."
        />
      )}
    </div>
  );
}
