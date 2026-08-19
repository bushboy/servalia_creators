import { FormEvent, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { BookNav } from '@/components/books/BookNav';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { useDocuments, useUploadDocument } from '@/hooks/useCreator';
import { FileText } from 'lucide-react';

export function ManuscriptPage() {
  const { bookId = '' } = useParams();
  const documents = useDocuments(bookId);
  const upload = useUploadDocument(bookId);
  const [rights, setRights] = useState('all_rights_owned');
  const latest = documents.data?.[0];

  async function onUpload(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const file = (form.elements.namedItem('excerpt') as HTMLInputElement).files?.[0];
    if (!file) return;
    await upload.mutateAsync({ file, rights });
    form.reset();
  }

  if (documents.isLoading) return <Skeleton className="h-48 w-full" />;
  if (documents.error) return <ApiErrorAlert error={documents.error} />;

  return (
    <div>
      <BookNav bookId={bookId} />
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Manuscript</h1>
          <p className="text-muted-foreground">
            Upload a .txt or .md excerpt. Hash and rights are stored with the source.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Upload excerpt</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={onUpload} className="space-y-3">
              <input name="excerpt" type="file" accept=".txt,.md,text/plain,text/markdown" />
              <select
                className="flex h-10 rounded-md border border-input bg-background px-3 text-sm"
                value={rights}
                onChange={(event) => setRights(event.target.value)}
              >
                <option value="all_rights_owned">I own all rights</option>
                <option value="licensed_with_permission">Licensed with permission</option>
                <option value="unknown">Unknown</option>
              </select>
              <Button type="submit" disabled={upload.isPending}>
                Upload
              </Button>
            </form>
          </CardContent>
        </Card>

        {latest ? (
          <Card>
            <CardHeader>
              <CardTitle>
                {latest.file_name} · v{latest.version}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2 text-sm">
              <p>SHA-256: {latest.sha256}</p>
              <p>Rights: {latest.rights_declaration}</p>
              <pre className="max-h-80 overflow-auto whitespace-pre-wrap rounded-md border bg-muted/40 p-3 text-xs">
                {latest.extracted_text}
              </pre>
            </CardContent>
          </Card>
        ) : (
          <EmptyState
            icon={FileText}
            title="No excerpt yet"
            description="Upload a short .txt or .md file to generate assets."
          />
        )}
      </div>
    </div>
  );
}
