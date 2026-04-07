# Frontend Improvements

## ~~1. Place name search for route booking~~ ✓ Done
**Priority: High | Effort: Medium**

Route search currently requires raw lat/lng input (e.g. `53.3498, -6.2603`). Replace with a geocoding text input so users can type "Dublin Airport" or "Cork City". Mapbox GL is already bundled — the Mapbox Geocoding API requires no new dependency.

Affects: `BookRoutePage.tsx`

---

## 2. Human-readable booking identifiers
**Priority: High | Effort: Low**

Full UUIDs are shown as the primary booking identifier throughout the UI. Display a truncated reference like `#3F7A` instead. The inbox currently shows `booking_id: 3f7a1c2d-...` as the message body — messages should render a human sentence ("Your booking was **approved**") rather than a raw field dump.

Affects: `BookingsPage.tsx`, `InboxPage.tsx`, `RouteResultCard.tsx`

---

## 3. Human-readable durations
**Priority: High | Effort: Low**

Route estimated duration is displayed in raw seconds (e.g. `5400`). Add a `formatDuration(seconds)` helper to the existing `lib/datetime.ts` and use it wherever duration is rendered. Output should be "1h 30m" or "45 min".

Affects: `RouteResultCard.tsx`, `lib/datetime.ts`

---

## 4. Empty states
**Priority: Medium | Effort: Low**

The bookings list, inbox, and route results all render nothing when empty. Add contextual empty states with a short message and a relevant CTA:
- Bookings: "No bookings yet — [Book a route →]"
- Inbox: "Your inbox is empty"
- Route results: "No routes found between these two points"

Affects: `BookingsPage.tsx`, `InboxPage.tsx`, `BookRoutePage.tsx`

---

## 5. Home dashboard upgrade
**Priority: Medium | Effort: Medium**

Authenticated home screen shows only four stat numbers with no visual hierarchy or next steps. Add:
- A welcome line with the driver's name
- A "Recent bookings" section showing the last 3 entries
- A prominent "Book a route" CTA

Affects: `HomePage.tsx`

---

## 6. Booking status explanation
**Priority: Medium | Effort: Low**

Status badges (PENDING, APPROVED, REJECTED) have no supporting copy. Add a short descriptor beneath the badge explaining what the status means and what happens next, e.g. "Awaiting route assessment — usually instant" for PENDING.

Affects: `BookingsPage.tsx`, `StatusBadge.tsx`

---

## 7. Register form display labels
**Priority: Low | Effort: Low**

Vehicle type and region dropdowns expose raw backend enum values (`CAR`, `HGV`, `MOTORCYCLE`). Map these to display labels before rendering: "Car", "Heavy Goods Vehicle", "Motorcycle", etc.

Affects: `RegisterPage.tsx`
