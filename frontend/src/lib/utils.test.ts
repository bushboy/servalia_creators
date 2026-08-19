import { describe, expect, it } from 'vitest';
import { cn } from './utils';

describe('cn', () => {
  it('merges tailwind classes correctly', () => {
    expect(cn('px-2 py-1', 'px-4')).toBe('py-1 px-4');
  });

  it('ignores falsy values', () => {
    const maybeHidden: string | false = false;
    expect(cn('base', maybeHidden || undefined, undefined, null)).toBe('base');
  });
});
