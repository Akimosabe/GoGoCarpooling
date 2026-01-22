import { BrowserRouter, Routes, Route, Navigate, useParams } from 'react-router-dom'
import { AuthProvider } from '@/contexts/AuthContext'
import { Layout } from '@/components/Layout'
import { Home } from '@/pages/Home'
import { Auth } from '@/pages/Auth'
import { Profile } from '@/pages/Profile'
import { ProfileSettings } from '@/pages/ProfileSettings'
import { ProfileCars } from '@/pages/ProfileCars'
import { SearchResults } from '@/pages/SearchResults'
import { TripDetail } from '@/pages/TripDetail'
import { CreateTrip } from '@/pages/CreateTrip'

function PasswordResetRedirect() {
  const { uid, token } = useParams<{ uid: string; token: string }>()
  if (uid && token) {
    return <Navigate to={`/auth?uid=${uid}&token=${token}`} replace /> 
  }
  return <Navigate to="/auth" replace />
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Home />} />
            <Route path="auth" element={<Auth />} />
            <Route path="search" element={<SearchResults />} />
            <Route path="trips/create" element={<CreateTrip />} />
            <Route path="trips/:id" element={<TripDetail />} />
            <Route path="profile/settings" element={<ProfileSettings />} />
            <Route path="profile/cars" element={<ProfileCars />} />
            <Route path="profile" element={<Profile />} />
            <Route path="profile/:id" element={<Profile />} />
          </Route>
          <Route
            path="password-reset/:uid/:token"
            element={<PasswordResetRedirect />}
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  )
}
