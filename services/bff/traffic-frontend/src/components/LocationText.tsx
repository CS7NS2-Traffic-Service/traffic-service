import { useQuery } from "@tanstack/react-query"
import { reverseGeocode } from "@/api/geocoding"

interface Props {
  value: string
  className?: string
}

export function LocationText({ value, className }: Props) {
  // Pattern to match "lat,lng" or "lat, lng"
  const coordsMatch = value.match(/^(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)$/)
  const isCoords = !!coordsMatch

  const { data: name, isLoading } = useQuery({
    queryKey: ["geocoding", value],
    queryFn: () => {
      if (!coordsMatch) return value
      const lat = parseFloat(coordsMatch[1])
      const lng = parseFloat(coordsMatch[2])
      return reverseGeocode(lng, lat)
    },
    enabled: isCoords,
    staleTime: Infinity, // Coordinates to names map 1:1 and don't change
  })

  if (!isCoords) {
    return <span className={className}>{value}</span>
  }

  if (isLoading) {
    return <span className={`${className} animate-pulse text-muted-foreground`}>Resolving...</span>
  }

  return (
    <span className={className} title={value}>
      {name ?? value}
    </span>
  )
}
