import { CalendarIcon } from "lucide-react"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { cn } from "@/lib/utils"

interface DateTimePickerProps {
  value: Date
  onChange: (date: Date) => void
  className?: string
  "aria-label"?: string
}

const HOURS = Array.from({ length: 24 }, (_, i) => i)
const MINUTES = [0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]

function pad(n: number) {
  return n.toString().padStart(2, "0")
}

function formatDisplay(date: Date) {
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

function isSameDay(a: Date, b: Date) {
  return a.getFullYear() === b.getFullYear() &&
    a.getMonth() === b.getMonth() &&
    a.getDate() === b.getDate()
}

export function DateTimePicker({ value, onChange, className, "aria-label": ariaLabel }: DateTimePickerProps) {
  const now = new Date()
  const isToday = isSameDay(value, now)
  const minHour = isToday ? now.getHours() : 0
  const minMinute = (isToday && value.getHours() === now.getHours()) ? now.getMinutes() : 0

  function handleDaySelect(day: Date | undefined) {
    if (!day) return
    const next = new Date(day)
    // If selecting today, clamp hours/minutes to not be in the past
    const h = isSameDay(day, now) ? Math.max(value.getHours(), now.getHours()) : value.getHours()
    const m = (isSameDay(day, now) && h === now.getHours())
      ? MINUTES.find((m) => m >= now.getMinutes()) ?? 0
      : value.getMinutes()
    next.setHours(h, m, 0, 0)
    onChange(next)
  }

  function handleHourChange(hour: string | null) {
    if (hour === null) return
    const h = parseInt(hour)
    const next = new Date(value)
    // Clamp minutes if the new hour is the current hour on today
    const m = (isToday && h === now.getHours())
      ? Math.max(value.getMinutes(), MINUTES.find((m) => m >= now.getMinutes()) ?? 0)
      : value.getMinutes()
    next.setHours(h, m, 0, 0)
    onChange(next)
  }

  function handleMinuteChange(minute: string | null) {
    if (minute === null) return
    const next = new Date(value)
    next.setMinutes(parseInt(minute), 0, 0)
    onChange(next)
  }

  return (
    <Popover>
      <PopoverTrigger
        data-testid="departure-picker"
        aria-label={ariaLabel}
        className={cn(
          "flex h-9 w-full items-center justify-start gap-2 rounded-lg border border-input bg-transparent px-3 text-sm font-normal shadow-xs transition-colors hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
          className
        )}
      >
        <CalendarIcon className="h-4 w-4 shrink-0 opacity-50" />
        {formatDisplay(value)}
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0" align="start">
        <Calendar
          mode="single"
          selected={value}
          onSelect={handleDaySelect}
          disabled={{ before: new Date(now.getFullYear(), now.getMonth(), now.getDate()) }}
          autoFocus
        />
        <div className="flex items-center gap-2 border-t p-3">
          <Select value={String(value.getHours())} onValueChange={handleHourChange}>
            <SelectTrigger data-testid="hour-select" className="flex-1">
              <SelectValue placeholder="HH" />
            </SelectTrigger>
            <SelectContent>
              {HOURS.filter((h) => h >= minHour).map((h) => (
                <SelectItem key={h} value={String(h)}>{pad(h)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
          <span className="text-sm font-medium">:</span>
          <Select value={String(value.getMinutes())} onValueChange={handleMinuteChange}>
            <SelectTrigger data-testid="minute-select" className="flex-1">
              <SelectValue placeholder="MM" />
            </SelectTrigger>
            <SelectContent>
              {MINUTES.filter((m) => m >= minMinute).map((m) => (
                <SelectItem key={m} value={String(m)}>{pad(m)}</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </PopoverContent>
    </Popover>
  )
}
