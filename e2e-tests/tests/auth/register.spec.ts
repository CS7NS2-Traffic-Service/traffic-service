
import { test, expect } from '@playwright/test';

test('register new driver', async ({ page }) => {

  const driverName = 'best driver'
  const email = `driver-${Date.now()}@example.com`;

  await page.goto('/register')
  await expect(page).toHaveURL('/register')

  await page.getByPlaceholder('Full name').fill(driverName)
  await page.getByPlaceholder('Email').fill(email)
  await page.getByPlaceholder('Password').fill('secretpassword')
  await page.getByPlaceholder('License Number').fill('D12345')
  await page.locator('select').nth(0).selectOption('CAR')
  await page.locator('select').nth(1).selectOption('Ireland')

  await page.locator('form').getByRole('button', { name: 'Register' }).click()

  await expect(page).toHaveURL('/routes')

  await expect(page.locator('[data-slot="dropdown-menu-trigger"]')).toContainText(driverName)

  const rawStoreEntry = await page.evaluate(() => localStorage.getItem('driver-store'))

  expect(rawStoreEntry).not.toBeNull()

  const storeEntry = JSON.parse(rawStoreEntry!)

  expect(storeEntry.state.token).not.toBeNull();

})
