import { create } from "zustand"

type DriverState = {
  username: string | null
  token: string | null
  setToken: (token: string) => void
  clearToken: () => void
  setUsername: (username: string) => void
  clearUsername: () => void
}

export const useDriverStore = create<DriverState>((set) => ({
  token: null,
  username: null,
  setToken: (token: string) => set({ token }),
  setUsername: (username: string) => set({ username }),
  clearToken: () => set({ token: null }),
  clearUsername: () => set({ username: null }),
}))
