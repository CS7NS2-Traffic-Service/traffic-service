import { describe, it, expect } from "vitest"
import { ensureUTCSuffix } from "./datetime"

describe("ensureUTCSuffix", () => {
  it("should append Z to naive datetime strings from the backend", () => {
    expect(ensureUTCSuffix("2026-06-01T00:00:00")).toBe("2026-06-01T00:00:00Z")
  })

  it("should not double-append Z if already present", () => {
    expect(ensureUTCSuffix("2026-06-01T00:00:00Z")).toBe("2026-06-01T00:00:00Z")
  })

  it("should not append Z if an offset is already present", () => {
    expect(ensureUTCSuffix("2026-06-01T00:00:00+02:00")).toBe("2026-06-01T00:00:00+02:00")
  })

  it("regression: naive backend datetime interpreted as local time shifts the hour", () => {
    const naiveFromBackend = "2026-06-01T00:00:00"

    const buggyDate = new Date(naiveFromBackend)
    const fixedDate = new Date(ensureUTCSuffix(naiveFromBackend))

    expect(fixedDate.getUTCHours()).toBe(0)
    expect(fixedDate.getUTCDate()).toBe(1)
    expect(fixedDate.getUTCMonth()).toBe(5)

    if (new Date().getTimezoneOffset() !== 0) {
      const buggyUTC = buggyDate.toISOString()
      expect(buggyUTC).not.toBe("2026-06-01T00:00:00.000Z")
    }
  })

  it("regression: round-trip local→UTC→display preserves the time", () => {
    const pickerValue = "2026-06-01T14:30"
    const sentToBackend = new Date(pickerValue).toISOString()
    const naiveFromBackend = sentToBackend.replace("Z", "").replace(/\.\d+$/, "")
    const displayDate = new Date(ensureUTCSuffix(naiveFromBackend))

    expect(displayDate.getHours()).toBe(14)
    expect(displayDate.getMinutes()).toBe(30)
  })
})
