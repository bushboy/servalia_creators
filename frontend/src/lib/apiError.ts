import { AxiosError, isAxiosError } from 'axios';

/**
 * Prefer the API body (`detail` / `build_error`) over Axios's generic status text.
 */
export function getApiErrorMessage(
  error: unknown,
  fallback = 'Something went wrong'
): string {
  if (isAxiosError(error)) {
    const fromBody = messageFromAxiosBody(error);
    if (fromBody) return fromBody;
    if (error.response?.status === 403) {
      return 'You do not have permission to do that.';
    }
    if (error.message) return error.message;
  }
  if (error instanceof Error && error.message) {
    return error.message;
  }
  return fallback;
}

function messageFromAxiosBody(error: AxiosError): string | null {
  const data = error.response?.data;
  if (data == null) return null;
  if (typeof data === 'string' && data.trim()) return data.trim();
  if (typeof data !== 'object') return null;

  const body = data as Record<string, unknown>;

  if (typeof body.build_error === 'string' && body.build_error.trim()) {
    return body.build_error.trim();
  }

  const detail = body.detail;
  if (typeof detail === 'string' && detail.trim()) {
    return detail.trim();
  }
  if (Array.isArray(detail)) {
    const parts = detail
      .map((item) => {
        if (typeof item === 'string') return item;
        if (item && typeof item === 'object' && 'msg' in item) {
          return String((item as { msg: unknown }).msg);
        }
        return null;
      })
      .filter((part): part is string => Boolean(part));
    if (parts.length > 0) return parts.join('; ');
  }

  if (typeof body.message === 'string' && body.message.trim()) {
    return body.message.trim();
  }

  return null;
}
