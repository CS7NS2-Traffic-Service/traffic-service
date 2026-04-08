import { Link, NavLink as RouterNavLink, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { ChevronDown } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import { useDriverStore } from '@/stores/driverStore'
import { fetchMessages } from '@/api/messages'
import { cn } from '@/lib/utils'

function NavItem({ to, label, badge }: { to: string; label: string; badge?: number }) {
  return (
    <RouterNavLink
      to={to}
      className={({ isActive }) =>
        cn(
          'inline-flex items-center gap-1 rounded-full px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground',
          isActive && 'bg-muted text-foreground'
        )
      }
    >
      <span>{label}</span>
      {badge !== undefined && badge > 0 && (
        <span className="inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-primary/10 px-1 text-[10px] font-medium text-primary">
          {badge}
        </span>
      )}
    </RouterNavLink>
  )
}

function Navbar() {
  const navigate = useNavigate()
  const { token, driver, logout } = useDriverStore()
  const firstName = driver?.name?.split(' ')[0] ?? 'Account'

  const { data: messages } = useQuery({
    queryKey: ['messages'],
    queryFn: fetchMessages,
    refetchInterval: 10000,
    enabled: !!token,
  })

  const unreadCount = messages?.filter((m) => !m.is_read).length ?? 0

  const handleLogout = () => {
    logout()
    navigate('/')
  }

  return (
    <nav className="sticky top-0 z-30 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex min-h-16 max-w-5xl items-center justify-between gap-4 px-4 py-2">
        <div className="flex items-center gap-4">
          <Link to="/" className="text-base font-semibold tracking-tight">
            Traffic Service
          </Link>
          {token && (
            <div className="flex items-center gap-1">
              <NavItem to="/routes" label="Book Route" />
              <NavItem to="/bookings" label="Bookings" />
              <NavItem to="/inbox" label="Inbox" badge={unreadCount} />
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          {token ? (
            <DropdownMenu>
              <DropdownMenuTrigger className="inline-flex cursor-pointer items-center gap-1 rounded-full border px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring">
                {firstName}
                <ChevronDown className="h-4 w-4" />
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem onClick={handleLogout}>
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <>
              <Button variant="ghost" onClick={() => navigate('/login')}>Login</Button>
              <Button onClick={() => navigate('/register')}>Register</Button>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}

export default Navbar
