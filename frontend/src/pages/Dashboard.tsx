import { FormEvent, useState } from 'react';
import { Link } from 'react-router-dom';
import { ApiErrorAlert } from '@/components/ApiErrorAlert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { EmptyState } from '@/components/ui/empty-state';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { useAuthors, useBooks, useMindChat } from '@/hooks/useCreator';
import { BookOpen, MessageSquare } from 'lucide-react';

export function Dashboard() {
  const authors = useAuthors();
  const author = authors.data?.[0];
  const books = useBooks(author?.author_id);
  const book = books.data?.[0];
  const chat = useMindChat(author?.author_id || '');
  const [message, setMessage] = useState('');
  const [thread, setThread] = useState<{ role: 'author' | 'mind'; text: string }[]>(
    []
  );

  async function onSend(event: FormEvent) {
    event.preventDefault();
    if (!author || !message.trim()) return;
    const text = message.trim();
    setThread((current) => [...current, { role: 'author', text }]);
    setMessage('');
    try {
      const result = await chat.mutateAsync(text);
      setThread((current) => [...current, { role: 'mind', text: result.reply }]);
    } catch {
      setThread((current) => current.slice(0, -1));
    }
  }

  if (authors.isLoading) {
    return <Skeleton className="h-48 w-full" />;
  }
  if (authors.error) {
    return <ApiErrorAlert error={authors.error} onRetry={() => authors.refetch()} />;
  }
  if (!author) {
    return (
      <EmptyState
        icon={BookOpen}
        title="No author yet"
        description="Create an author profile to bind a publishing Mind."
      >
        <Link to="/author">
          <Button>Set up author</Button>
        </Link>
      </EmptyState>
    );
  }

  const next = !book
    ? { to: '/library', label: 'Add a book in the Library' }
    : { to: `/books/${book.id}/manuscript`, label: 'Continue with manuscript and assets' };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Home</h1>
        <p className="text-muted-foreground">
          {author.name} · one Mind, messaged only through Servalia
        </p>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Author</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <p>
              <span className="text-muted-foreground">Voice: </span>
              {String(author.context.voice || 'Not set')}
            </p>
            <p>
              <span className="text-muted-foreground">Reader: </span>
              {String(author.context.audience || 'Not set')}
            </p>
            <p>
              <span className="text-muted-foreground">Rights: </span>
              {String(author.context.rights || 'Not set')}
            </p>
            <p>
              <span className="text-muted-foreground">Avoid: </span>
              {String(author.context.prohibited_topics || 'Not set')}
            </p>
            <p>
              <span className="text-muted-foreground">Mind: </span>
              {author.mind?.mind_id || 'Not bound'} ({author.mind?.status})
              {author.mind?.configured ? '' : ' · credentials not configured on the API'}
            </p>
            {book ? (
              <p>
                Active book:{' '}
                <Link className="text-primary underline" to={`/books/${book.id}`}>
                  {book.final_title || book.working_title}
                </Link>
              </p>
            ) : (
              <p className="text-muted-foreground">No book yet.</p>
            )}
            <div className="flex flex-wrap gap-2 pt-2">
              <Link to="/author">
                <Button variant="outline">Edit profile</Button>
              </Link>
              <Link to={next.to}>
                <Button>{next.label}</Button>
              </Link>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Mind
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="max-h-80 min-h-48 space-y-3 overflow-y-auto rounded-md border p-3 text-sm">
              {thread.length === 0 ? (
                <p className="text-muted-foreground">
                  Ask the bound Mind about voice, rights, or the launch. This calls
                  Servalia, not the browser.
                </p>
              ) : (
                thread.map((item, index) => (
                  <div key={`${item.role}-${index}`} className="space-y-1">
                    <p className="font-medium">
                      {item.role === 'author' ? 'You' : 'Mind'}
                    </p>
                    <p className="whitespace-pre-wrap break-words">{item.text}</p>
                  </div>
                ))
              )}
              {chat.isPending ? (
                <p className="text-muted-foreground">
                  Mind is working through Servalia. Replies often take one to two
                  minutes.
                </p>
              ) : null}
            </div>
            <form onSubmit={onSend} className="space-y-2">
              <Textarea
                value={message}
                onChange={(event) => setMessage(event.target.value)}
                placeholder="Message your publishing Mind"
              />
              <Button type="submit" disabled={chat.isPending || !message.trim()}>
                {chat.isPending ? 'Waiting for the Mind…' : 'Send through Servalia'}
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
