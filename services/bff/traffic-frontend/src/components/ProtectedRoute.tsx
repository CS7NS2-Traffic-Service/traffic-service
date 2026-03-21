import { Navigate } from "react-router-dom"
import { useDriverStore } from "@/stores/driverStore"
import type { ReactNode } from "react"

function ProtectedRoute({ children }: { children: ReactNode }) {
  const token = useDriverStore((state) => state.token)

  if (!token) {
    return <Navigate to="/login" replace />
  }

  return <>{children}</>
}

export default ProtectedRoute
