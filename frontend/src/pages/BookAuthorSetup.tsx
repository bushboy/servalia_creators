import { useParams } from 'react-router-dom';
import { BookNav } from '@/components/books/BookNav';
import { AuthorSetupPage } from '@/pages/AuthorSetup';

export function BookAuthorSetupPage() {
  const { bookId = '' } = useParams();
  return (
    <div>
      <BookNav bookId={bookId} />
      <AuthorSetupPage />
    </div>
  );
}
