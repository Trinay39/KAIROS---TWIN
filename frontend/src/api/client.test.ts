import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { ApiError, apiFetch } from './client';

const fetchMock = vi.fn();

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock);
  vi.spyOn(console, 'error').mockImplementation(() => undefined);
});

afterEach(() => {
  fetchMock.mockReset();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
});

describe('apiFetch', () => {
  it('parses a successful JSON response', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ status: 'ok' }), { status: 200 }));

    await expect(apiFetch('/health')).resolves.toEqual({ status: 'ok' });
  });

  it('classifies validation errors with a safe user-facing message', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ detail: 'Traceback C:\\secret\\api.py' }), { status: 422 }));

    await expect(apiFetch('/states/compute')).rejects.toMatchObject({
      kind: 'validation',
      userMessage: 'The selected student data could not be processed.',
    });

    try {
      await apiFetch('/states/compute');
    } catch (error) {
      expect(error).toBeInstanceOf(ApiError);
      expect((error as ApiError).message).not.toContain('Traceback');
      expect((error as ApiError).message).not.toContain('C:\\secret');
    }
  });

  it('classifies authentication/configuration failures', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ detail: 'Forbidden' }), { status: 403 }));

    await expect(apiFetch('/metadata/model')).rejects.toMatchObject({
      kind: 'auth',
      userMessage: 'KAIROS-TWIN backend access is not configured correctly.',
    });
  });

  it('classifies server errors with a safe message', async () => {
    fetchMock.mockResolvedValue(new Response('Traceback at /srv/app/secrets.py', { status: 500 }));

    await expect(apiFetch('/predictions')).rejects.toMatchObject({
      kind: 'server',
      userMessage: 'Prediction service is unavailable.',
    });
  });

  it('classifies network failures as backend unavailable', async () => {
    fetchMock.mockRejectedValue(new TypeError('fetch failed'));

    await expect(apiFetch('/health')).rejects.toMatchObject({
      kind: 'network',
      userMessage: 'Unable to connect to KAIROS-TWIN backend.',
    });
  });

  it('classifies malformed JSON responses with a safe message', async () => {
    fetchMock.mockResolvedValue(new Response('{bad-json', { status: 200 }));

    await expect(apiFetch('/analytics/system')).rejects.toMatchObject({
      kind: 'unknown',
      userMessage: 'The request could not be completed.',
    });
  });
});
