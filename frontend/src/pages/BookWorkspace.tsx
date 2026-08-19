import { FormEvent, useState } from 'react';
import { useParams } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { BookNav } from '@/components/books/BookNav';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import {
  useBook,
  useCreateEdition,
  useEditions,
  usePatchBook,
  usePatchEdition,
} from '@/hooks/useCreator';

export function BookWorkspacePage() {
  const { bookId = '' } = useParams();
  const bookQuery = useBook(bookId);
  const editions = useEditions(bookId);
  const saveBook = usePatchBook(bookId);
  const saveEdition = usePatchEdition(bookId);
  const addEdition = useCreateEdition(bookId);
  const book = bookQuery.data;
  const [workingTitle, setWorkingTitle] = useState<string | null>(null);
  const [subtitle, setSubtitle] = useState<string | null>(null);
  const [description, setDescription] = useState<string | null>(null);

  if (bookQuery.isLoading || editions.isLoading) {
    return <Skeleton className="h-64 w-full" />;
  }
  if (bookQuery.error || !book) {
    return <ApiErrorAlert error={bookQuery.error} />;
  }

  async function onSaveBook(event: FormEvent) {
    event.preventDefault();
    if (!book) return;
    await saveBook.mutateAsync({
      working_title: workingTitle ?? book.working_title,
      final_title: workingTitle ?? book.final_title ?? book.working_title,
      subtitle: subtitle ?? book.subtitle ?? '',
      description: description ?? book.description,
    });
  }

  return (
    <div>
      <BookNav bookId={bookId} />
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">
            {book.final_title || book.working_title}
          </h1>
          <p className="text-muted-foreground">
            Titles on the book. ISBN, format, and price on each edition.
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Titles</CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSaveBook} className="space-y-3">
              <Input
                value={workingTitle ?? book.working_title}
                onChange={(event) => setWorkingTitle(event.target.value)}
                placeholder="Working / final title"
              />
              <Input
                value={subtitle ?? book.subtitle ?? ''}
                onChange={(event) => setSubtitle(event.target.value)}
                placeholder="Subtitle"
              />
              <Textarea
                value={description ?? book.description}
                onChange={(event) => setDescription(event.target.value)}
                placeholder="Book description"
              />
              <Button type="submit">Save book</Button>
            </form>
          </CardContent>
        </Card>

        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold">Editions</h2>
          <Button
            variant="outline"
            onClick={() => addEdition.mutate({ format: 'paperback', language: 'en' })}
          >
            Add edition
          </Button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {editions.data?.map((edition) => (
            <Card key={edition.id}>
              <CardHeader>
                <CardTitle className="capitalize">{edition.format}</CardTitle>
              </CardHeader>
              <CardContent className="grid gap-2 text-sm">
                {(
                  [
                    ['format', edition.format],
                    ['isbn', edition.isbn || ''],
                    ['language', edition.language],
                    ['list_price', String(edition.list_price ?? '')],
                    ['currency', edition.currency],
                    ['publication_date', edition.publication_date || ''],
                  ] as const
                ).map(([field, value]) => (
                  <label key={field} className="grid gap-1">
                    <span className="text-muted-foreground">{field.replace('_', ' ')}</span>
                    <Input
                      defaultValue={value}
                      onBlur={(event) =>
                        saveEdition.mutate({
                          editionId: edition.id,
                          payload: {
                            [field]:
                              field === 'list_price'
                                ? Number(event.target.value) || null
                                : event.target.value,
                          },
                        })
                      }
                    />
                  </label>
                ))}
                <label className="grid gap-1">
                  <span className="text-muted-foreground">platform strategy (publisher field)</span>
                  <Input
                    defaultValue={String(
                      (edition.platform_strategy || {}).publisher_field || ''
                    )}
                    onBlur={(event) =>
                      saveEdition.mutate({
                        editionId: edition.id,
                        payload: {
                          platform_strategy: {
                            ...edition.platform_strategy,
                            publisher_field: event.target.value,
                          },
                        },
                      })
                    }
                  />
                </label>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
