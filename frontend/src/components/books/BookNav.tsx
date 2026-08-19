import { NavLink } from 'react-router-dom';
import { cn } from '@/lib/utils';

const LINKS = [
  { suffix: '', label: 'Book' },
  { suffix: '/setup', label: 'Author' },
  { suffix: '/manuscript', label: 'Manuscript' },
  { suffix: '/assets', label: 'Assets' },
  { suffix: '/governance', label: 'Governance' },
  { suffix: '/publishing', label: 'Publishing' },
  { suffix: '/launch', label: 'Launch' },
];

export function BookNav({ bookId }: { bookId: string }) {
  const base = `/books/${bookId}`;
  return (
    <nav
      className="mb-6 flex flex-wrap gap-1 border-b pb-2"
      aria-label="Book"
    >
      {LINKS.map((link) => (
        <NavLink
          key={link.suffix || 'book'}
          to={`${base}${link.suffix}`}
          end={link.suffix === ''}
          className={({ isActive }) =>
            cn(
              'rounded-md px-3 py-1.5 text-sm font-medium',
              isActive
                ? 'bg-primary/10 text-primary'
                : 'text-muted-foreground hover:text-foreground'
            )
          }
        >
          {link.label}
        </NavLink>
      ))}
    </nav>
  );
}
