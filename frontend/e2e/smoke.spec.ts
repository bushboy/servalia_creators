import { test, expect } from '@playwright/test';

const API_KEY = process.env.E2E_API_KEY || 'test-api-key:test-secret';

async function signIn(page: import('@playwright/test').Page) {
  await page.goto('/login');
  await expect(page.getByRole('heading', { name: /creatortrust/i })).toBeVisible();
  await page.getByLabel(/api key/i).fill(API_KEY);
  await page.getByRole('button', { name: /sign in with api key/i }).click();
  await expect(page).toHaveURL(/\/($|\?)/);
  await expect(page.getByRole('heading', { name: /^home$/i })).toBeVisible({
    timeout: 15_000,
  });
}

test.describe('auth', () => {
  test('unauthenticated users are redirected to login', async ({ page }) => {
    await page.goto('/');
    await expect(page).toHaveURL(/.*login/);
    await expect(
      page.getByRole('heading', { name: /creatortrust/i })
    ).toBeVisible();
    await expect(page.getByRole('button', { name: /sign in/i })).toBeVisible();
  });

  test('API key login reaches Home', async ({ page }) => {
    test.skip(
      !process.env.E2E_API || process.env.E2E_API === '0',
      'Set E2E_API=1 with a seeded backend on :8000'
    );
    await signIn(page);
    const nav = page.getByRole('navigation', { name: /main/i });
    await expect(nav).toContainText('Home');
    await expect(nav).toContainText('Library');
    await expect(nav).toContainText('Audit');
  });
});
