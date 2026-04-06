import { test, expect, APIRequestContext, Page } from '@playwright/test';

const ORIGIN_LAT = '53.349800';
const ORIGIN_LNG = '-6.260300';
const DEST_LAT = '53.412900';
const DEST_LNG = '-6.276500';
const DEPARTURE = '2028-06-01T10:00';

let authToken = '';

async function loginViaApi(page: Page, request: APIRequestContext) {
  const response = await request.post('/api/driver/auth/login', {
    data: { email: 'test@example.com', password: 'password123' },
  });
  const { access_token, driver } = await response.json();
  authToken = access_token;
  await page.goto('/');
  await page.evaluate(({ token, driver }) => {
    localStorage.setItem('driver-store', JSON.stringify({
      state: { token, driver },
      version: 0,
    }));
  }, { token: access_token, driver });
}

test('booked departure time matches the time selected in the picker', async ({ page, request }) => {
  await loginViaApi(page, request);

  await page.goto(`/routes?departure=${DEPARTURE}`);
  await expect(page).toHaveURL(/\/routes/);

  await page.getByPlaceholder('e.g. 48.2082').fill(ORIGIN_LAT);
  await page.getByPlaceholder('e.g. 16.3738').fill(ORIGIN_LNG);
  await page.getByPlaceholder('e.g. 47.0707').fill(DEST_LAT);
  await page.getByPlaceholder('e.g. 15.4395').fill(DEST_LNG);

  await page.getByRole('button', { name: 'Find Route' }).click();
  await expect(page.getByText('Route Found')).toBeVisible({ timeout: 15_000 });

  await page.getByRole('button', { name: 'Book this Route' }).click();
  await expect(page.getByText('Booking created')).toBeVisible({ timeout: 10_000 });

  const bookingsResponse = await request.get('/api/booking/bookings', {
    headers: { Authorization: `Bearer ${authToken}` },
  });
  expect(bookingsResponse.ok()).toBe(true);

  const bookings = await bookingsResponse.json();
  expect(bookings.length).toBeGreaterThan(0);

  const booking = bookings[bookings.length - 1];
  const storedUTC = new Date(booking.departure_time);
  const pickerLocal = new Date(DEPARTURE);

  expect(storedUTC.getTime()).toBe(pickerLocal.getTime());

  await page.goto('/bookings');
  await page.waitForResponse(
    (resp) => resp.url().includes('/api/booking/bookings') && resp.status() === 200,
    { timeout: 15_000 },
  );

  const departureText = await page.getByText(/Departure:/).first().innerText();
  expect(departureText).toContain('10:00');
});
