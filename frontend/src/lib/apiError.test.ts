import { describe, expect, it } from 'vitest';
import { AxiosError } from 'axios';
import { getApiErrorMessage } from '@/lib/apiError';

function axiosError(
  status: number,
  data: unknown,
  message = 'Request failed'
): AxiosError {
  return new AxiosError(
    message,
    String(status),
    undefined,
    undefined,
    {
      status,
      statusText: message,
      headers: {},
      config: {} as never,
      data,
    }
  );
}

describe('getApiErrorMessage', () => {
  it('prefers detail string from the API body', () => {
    expect(
      getApiErrorMessage(axiosError(403, { detail: 'Operator role required' }))
    ).toBe('Operator role required');
  });

  it('prefers build_error when present', () => {
    expect(
      getApiErrorMessage(
        axiosError(403, { build_error: 'Tenant suspended', detail: 'ignored' })
      )
    ).toBe('Tenant suspended');
  });

  it('joins FastAPI validation detail arrays', () => {
    expect(
      getApiErrorMessage(
        axiosError(422, {
          detail: [
            { loc: ['body', 'name'], msg: 'Field required', type: 'missing' },
          ],
        })
      )
    ).toBe('Field required');
  });

  it('falls back for bare 403 without a body', () => {
    expect(getApiErrorMessage(axiosError(403, null))).toBe(
      'You do not have permission to do that.'
    );
  });
});
