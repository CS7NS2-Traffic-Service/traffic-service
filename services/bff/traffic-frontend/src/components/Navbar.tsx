import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'

function Navbar() {
  const navigate = useNavigate()

  return (
    <nav className="border-b bg-background">
      <div className="mx-auto flex h-14 max-w-5xl items-center justify-between px-4">
        <Button variant="ghost" className="text-base font-semibold" onClick={() => navigate('/')}>
          Traffic Service
        </Button>
        <div className="flex gap-2">
          <Button variant="ghost" onClick={() => navigate('/login')}>Login</Button>
          <Button onClick={() => navigate('/register')}>Register</Button>
        </div>
      </div>
    </nav>
  )
}

export default Navbar
