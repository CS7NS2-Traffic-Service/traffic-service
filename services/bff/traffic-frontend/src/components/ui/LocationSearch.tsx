import { useEffect, useRef, useState } from "react"
import { Input } from "./input"

type Suggestion = {
  place_name: string
  center: [number, number] // [lng, lat]
}

type Props = {
  label: string
  placeholder: string
  displayValue: string
  onSelect: (name: string, lng: number, lat: number) => void
  onClear: () => void
}

const MAPBOX_TOKEN = import.meta.env.VITE_MAPBOX_TOKEN as string

export function LocationSearch({ label, placeholder, displayValue, onSelect, onClear }: Props) {
  const [query, setQuery] = useState(displayValue)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [open, setOpen] = useState(false)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    setQuery(displayValue)
  }, [displayValue])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value
    setQuery(val)
    onClear()

    if (debounceRef.current) clearTimeout(debounceRef.current)

    if (val.length < 2) {
      setSuggestions([])
      setOpen(false)
      return
    }

    debounceRef.current = setTimeout(async () => {
      const params = new URLSearchParams({
        access_token: MAPBOX_TOKEN,
        limit: "5",
        types: "place,address,poi",
        country: "ie,gb",
      })
      const res = await fetch(
        `https://api.mapbox.com/geocoding/v5/mapbox.places/${encodeURIComponent(val)}.json?${params}`,
      )
      const data = await res.json()
      setSuggestions(data.features ?? [])
      setOpen(true)
    }, 300)
  }

  const handleSelect = (suggestion: Suggestion) => {
    const [lng, lat] = suggestion.center
    onSelect(suggestion.place_name, lng, lat)
    setQuery(suggestion.place_name)
    setSuggestions([])
    setOpen(false)
  }

  return (
    <div className="relative space-y-1">
      <label className="text-sm font-medium">{label}</label>
      <Input
        type="text"
        placeholder={placeholder}
        value={query}
        onChange={handleChange}
        onBlur={() => setTimeout(() => setOpen(false), 150)}
        autoComplete="off"
      />
      {open && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full overflow-hidden rounded-md border bg-white shadow-md">
          {suggestions.map((s) => (
            <li
              key={s.place_name}
              className="cursor-pointer px-3 py-2 text-sm hover:bg-gray-100"
              onMouseDown={() => handleSelect(s)}
            >
              {s.place_name}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
