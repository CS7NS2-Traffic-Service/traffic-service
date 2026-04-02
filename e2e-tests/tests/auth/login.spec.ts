import { test, expect, APIRequestContext, Page } from '@playwright/test';


async function loginViaApi(page: Page, request: APIRequestContext) {
  const response = await request.post('/api/driver/auth/login', {
    data: { email: 'test@example.com', password: 'password123' },
  });
  const { access_token, driver } = await response.json();
  await page.goto('/');
  await page.evaluate(({ token, driver }) => {
    localStorage.setItem('driver-store', JSON.stringify({
      state: { token, driver },
      version: 0,
    }));
  }, { token: access_token, driver });
}

test.describe('login', () => {
  test('driver login', async ({ page }) => {
    await page.goto('/login')
    await expect(page).toHaveURL('/login')

    await page.getByPlaceholder('Email').fill('test@example.com')
    await page.getByPlaceholder('Password').fill('password123')

    await page.locator('form').getByRole('button', { name: 'Login' }).click()

    await expect(page).toHaveURL('/routes')

    await expect(page.locator('[data-slot="dropdown-menu-trigger"]')).toContainText('Test Driver')

    const rawStoreEntry = await page.evaluate(() => localStorage.getItem('driver-store'))

    expect(rawStoreEntry).not.toBeNull()

    const storeEntry = JSON.parse(rawStoreEntry!)

    expect(storeEntry.state.token).not.toBeNull();

  });

  test('login with valid credentials', async ({ page, request }) => {
    await loginViaApi(page, request)


    await page.goto('/routes')
    await expect(page).toHaveURL('/routes')
    await expect(page.locator('[data-slot="dropdown-menu-trigger"]')).toContainText('Test Driver')

    await page.goto('/bookings')
    await expect(page).toHaveURL('/bookings')

    await page.goto('/inbox')
    await expect(page).toHaveURL('/inbox')
  })

})
