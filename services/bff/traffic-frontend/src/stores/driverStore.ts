import { create } from "zustand"
import { persist } from "zustand/middleware"
import type { DriverProfile } from "@/api/auth"

type DriverState = {
  driver: DriverProfile | null
  token: string | null
  login: (driver: DriverProfile, token: string) => void
  logout: () => void
}

export const useDriverStore = create<DriverState>()(
  persist(
    (set) => ({
      driver: null,
      token: null,
      login: (driver: DriverProfile, token: string) => set({ driver, token }),
      logout: () => set({ driver: null, token: null }),
    }),
    { name: "driver-store" }
  )
)
