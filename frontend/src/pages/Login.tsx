import { useState } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Loader2 } from 'lucide-react';

export function LoginPage() {
  const { loginWithRedirect, loginWithApiKey, isLoading, error, authMode } =
    useAuth();
  const [apiKey, setApiKey] = useState('');

  async function handleApiKeySubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!apiKey.trim()) return;
    await loginWithApiKey(apiKey.trim());
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <div className="w-full max-w-sm space-y-6 rounded-lg border bg-card p-8 shadow-sm">
        <div className="flex flex-col items-center space-y-2 text-center">
          <img src="/creator_trust.png" alt="CreatorTrust" className="h-32 w-32 object-contain" />
          <h1 className="text-2xl font-bold tracking-tight">CreatorTrust</h1>
          <p className="text-sm text-muted-foreground">
            Sign in to your publishing Mind.
          </p>
        </div>

        {authMode === 'oidc' ? (
          <Button
            className="w-full"
            onClick={loginWithRedirect}
            disabled={isLoading}
          >
            {isLoading ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : null}
            Sign in with OIDC
          </Button>
        ) : (
          <form onSubmit={handleApiKeySubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="api-key" className="text-sm font-medium">
                API key
              </label>
              <Input
                id="api-key"
                placeholder="key-id:secret"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                disabled={isLoading}
                autoComplete="off"
              />
              <p className="text-xs text-muted-foreground">
                Paste an API key in the form <code>key-id:secret</code>.
              </p>
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              ) : null}
              Sign in with API key
            </Button>
          </form>
        )}

        {error && (
          <p className="rounded-md bg-destructive/10 p-3 text-sm text-destructive">
            {error.message || 'Sign in failed'}
          </p>
        )}
      </div>
    </div>
  );
}
