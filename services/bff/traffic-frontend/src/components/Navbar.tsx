import { useNavigate, useLocation } from 'react-router-dom'
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

function NavLink({ to, label, badge }: { to: string; label: string; badge?: number }) {
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const isActive = pathname === to

  return (
    <Button
      variant="ghost"
      className={isActive ? 'bg-muted' : ''}
      onClick={() => navigate(to)}
    >
      {label}
      {badge !== undefined && badge > 0 && (
        <span className="ml-1 inline-flex h-4 min-w-4 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-medium text-primary-foreground">
          {badge}
        </span>
      )}
    </Button>
  )
}

function Navbar() {
  const navigate = useNavigate()
  const { token, driver, logout } = useDriverStore()

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
    <nav className="border-b bg-background">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <div className="flex items-center gap-1">
          <Button variant="ghost" className="text-base font-semibold" onClick={() => navigate('/')}>
            Traffic Service
          </Button>
          {token && (
            <>
              <NavLink to="/routes" label="Routes" />
              <NavLink to="/bookings" label="Bookings" />
              <NavLink to="/inbox" label="Inbox" badge={unreadCount} />
              <NavLink to="/dashboard" label="Dashboard" />
            </>
          )}
        </div>
        <div className="flex gap-2">
          {token ? (
            <DropdownMenu>
              <DropdownMenuTrigger className="inline-flex items-center gap-1 rounded-md px-3 py-2 text-sm font-medium hover:bg-accent hover:text-accent-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring cursor-pointer">
                {driver?.name}
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
