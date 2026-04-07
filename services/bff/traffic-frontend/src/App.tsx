import { lazy, Suspense } from 'react'
import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import ProtectedRoute from './components/ProtectedRoute'
import HomePage from './pages/Home/HomePage'
import LoginPage from './pages/Login/LoginPage'
import RegisterPage from './pages/Register/RegisterPage'
import BookingsPage from './pages/Bookings/BookingsPage'
import InboxPage from './pages/Inbox/InboxPage'

const BookRoutePage = lazy(() => import('./pages/BookRoute/BookRoutePage'))

function App() {
  return (
    <>
      <Navbar />
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/bookings" element={<ProtectedRoute><BookingsPage /></ProtectedRoute>} />
        <Route path="/inbox" element={<ProtectedRoute><InboxPage /></ProtectedRoute>} />
        <Route path="/routes" element={<ProtectedRoute><Suspense fallback={null}><BookRoutePage /></Suspense></ProtectedRoute>} />
      </Routes>
      <Footer />
    </>
  )
}

export default App
