import { FormEvent, useEffect, useState } from 'react';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { useAuthors, usePatchAuthor } from '@/hooks/useCreator';

const FIELDS = [
  ['display_name', 'Display name', false],
  ['voice', 'Writing voice', true],
  ['audience', 'Target reader', true],
  ['genres', 'Genres', false],
  ['rights', 'Rights declaration', false],
  ['prohibited_topics', 'Prohibited topics', true],
  ['preferred_terms', 'Preferred terms', false],
  ['approval_policy', 'Approval policy', true],
  ['publisher_name', 'Publisher / imprint name', false],
] as const;

export function AuthorSetupPage() {
  const authors = useAuthors();
  const author = authors.data?.[0];
  const save = usePatchAuthor(author?.author_id || '');
  const [name, setName] = useState('');
  const [context, setContext] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!author) return;
    setName(author.name);
    const next: Record<string, string> = {};
    for (const [key] of FIELDS) {
      next[key] = String(author.context[key] ?? '');
    }
    setContext(next);
  }, [author]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!author) return;
    await save.mutateAsync({ name, context });
  }

  if (authors.isLoading) return <Skeleton className="h-64 w-full" />;
  if (authors.error) return <ApiErrorAlert error={authors.error} />;
  if (!author) {
    return <p className="text-sm text-muted-foreground">Seed or create an author first.</p>;
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Author setup</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={onSubmit} className="space-y-4">
          <label className="block space-y-1 text-sm">
            <span>Author name</span>
            <Input value={name} onChange={(event) => setName(event.target.value)} />
          </label>
          {FIELDS.map(([key, label, area]) => (
            <label key={key} className="block space-y-1 text-sm">
              <span>{label}</span>
              {area ? (
                <Textarea
                  value={context[key] || ''}
                  onChange={(event) =>
                    setContext((current) => ({ ...current, [key]: event.target.value }))
                  }
                />
              ) : (
                <Input
                  value={context[key] || ''}
                  onChange={(event) =>
                    setContext((current) => ({ ...current, [key]: event.target.value }))
                  }
                />
              )}
            </label>
          ))}
          <p className="text-xs text-muted-foreground">
            Rights, voice, and prohibited topics drive creator-configured governance
            review. This is not legal clearance.
          </p>
          <Button type="submit" disabled={save.isPending}>
            Save profile
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
