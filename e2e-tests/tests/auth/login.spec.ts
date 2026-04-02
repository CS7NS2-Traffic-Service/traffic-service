import { test, expect } from '@playwright/test';

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

})
