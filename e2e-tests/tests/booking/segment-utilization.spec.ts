import { test, expect, type APIRequestContext, type Page } from '@playwright/test';

const ORIGIN_LAT = '53.349800';
const ORIGIN_LNG = '-6.260300';
const DEST_LAT = '53.412900';
const DEST_LNG = '-6.276500';
const DEPARTURE = '2028-06-01T12:00';

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

test('booking updates utilization for all segments, not just the first', async ({ page, request }) => {
  await loginViaApi(page, request);

  const routeUrl = `/routes?originLat=${ORIGIN_LAT}&originLng=${ORIGIN_LNG}&destLat=${DEST_LAT}&destLng=${DEST_LNG}&departure=${DEPARTURE}`;

  await page.goto(routeUrl);
  await page.getByRole('button', { name: 'Find Route' }).click();
  await expect(page.getByText('Route Found')).toBeVisible({ timeout: 15_000 });

  const segmentsHeading = page.getByText(/^Segments \(\d+\)$/);
  await expect(segmentsHeading).toBeVisible();
  const headingText = await segmentsHeading.textContent() ?? '';
  const segmentCount = parseInt(headingText.match(/\d+/)![0]);
  expect(
    segmentCount,
    'Route must have more than one segment for this test to be meaningful',
  ).toBeGreaterThan(1);

  await page.getByRole('button', { name: 'Book this Route' }).click();
  await expect(page.getByText('Booking created')).toBeVisible({ timeout: 10_000 });

  await page.goto('/bookings');
  await expect(
    page.getByText('Awaiting route assessment — usually instant'),
  ).not.toBeVisible({ timeout: 15_000 });

  await page.goto(routeUrl);
  await page.getByRole('button', { name: 'Find Route' }).click();
  await expect(page.getByText('Route Found')).toBeVisible({ timeout: 15_000 });

  const reservedRows = page.locator('p').filter({ hasText: /Reserved:/ });
  await expect(reservedRows).toHaveCount(segmentCount, { timeout: 10_000 });

  for (let i = 0; i < segmentCount; i++) {
    await expect(
      reservedRows.nth(i),
      `Segment ${i + 1} has 0 active reservations — utilization window may be too narrow`,
    ).not.toContainText('Reserved: 0 /');
  }
});
