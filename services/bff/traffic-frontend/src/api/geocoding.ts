const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string

export async function reverseGeocode(lng: number, lat: number): Promise<string> {
  const params = new URLSearchParams({
    access_token: MAPBOX_TOKEN,
    types: "place,locality,neighborhood,address",
    limit: "1",
  })
  
  try {
    const res = await fetch(
      `https://api.mapbox.com/geocoding/v5/mapbox.places/${lng},${lat}.json?${params}`
    )
    if (!res.ok) throw new Error("Geocoding failed")
    
    const data = await res.json()
    if (data.features && data.features.length > 0) {
      return data.features[0].place_name
    }
  } catch (err) {
    console.error("Reverse geocoding error:", err)
  }
  
  return `${lat.toFixed(4)}, ${lng.toFixed(4)}`
}
