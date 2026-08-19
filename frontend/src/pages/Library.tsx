import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Input } from '@/components/ui/input';
import { Skeleton } from '@/components/ui/skeleton';
import { useAuthors, useBooks, useCreateBook } from '@/hooks/useCreator';
import { BookOpen } from 'lucide-react';

export function LibraryPage() {
  const authors = useAuthors();
  const author = authors.data?.[0];
  const books = useBooks(author?.author_id);
  const create = useCreateBook();
  const [title, setTitle] = useState('');

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!author || !title.trim()) return;
    await create.mutateAsync({
      author_id: author.author_id,
      working_title: title.trim(),
      final_title: title.trim(),
    });
    setTitle('');
  }

  if (authors.isLoading || books.isLoading) {
    return <Skeleton className="h-40 w-full" />;
  }
  if (authors.error || books.error) {
    return <ApiErrorAlert error={authors.error || books.error} />;
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Library</h1>
        <p className="text-muted-foreground">
          Books for {author?.name || 'this author'}. ISBN and price live on each edition.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>New book</CardTitle>
        </CardHeader>
        <CardContent>
          <form onSubmit={onCreate} className="flex flex-wrap gap-2">
            <Input
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Working title"
              className="max-w-sm"
            />
            <Button type="submit" disabled={!author || create.isPending}>
              Create book
            </Button>
          </form>
        </CardContent>
      </Card>

      {books.data?.length ? (
        <div className="grid gap-4 md:grid-cols-2">
          {books.data.map((book) => (
            <Card key={book.id}>
              <CardHeader>
                <CardTitle>{book.final_title || book.working_title}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-2 text-sm text-muted-foreground">
                <p>{book.subtitle || 'No subtitle'}</p>
                <Link to={`/books/${book.id}`}>
                  <Button variant="outline">Open workspace</Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      ) : (
        <EmptyState
          icon={BookOpen}
          title="No books yet"
          description="Create a book, then add paperback and ebook editions."
        />
      )}
    </div>
  );
}
