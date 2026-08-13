import { BrowserRouter, Route, Routes } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { PublicLayout } from './layouts/PublicLayout'
import { HomePage } from './pages/HomePage'
import { ServicesPage } from './pages/ServicesPage'
import { ServiceDetailPage } from './pages/ServiceDetailPage'
import { PlaceholderPage } from './pages/PlaceholderPage'
import { api } from './lib/api'
import type { Branding } from './types'

const fallback: Branding = { app_name: 'Jijenge', tagline: 'Find services. Offer your skills. Get things done.', primary_color: '#2563EB', background_color: '#F8FAFC', surface_color: '#FFFFFF', text_color: '#0F172A' }

export default function App() {
  const [branding, setBranding] = useState<Branding>(fallback)
  useEffect(() => { api.branding().then(setBranding).catch(() => {}) }, [])
  return <BrowserRouter><PublicLayout branding={branding}><Routes>
    <Route path="/" element={<HomePage branding={branding} />} />
    <Route path="/services" element={<ServicesPage />} />
    <Route path="/services/:serviceId" element={<ServiceDetailPage />} />
    <Route path="/login" element={<PlaceholderPage title="Welcome back" text="Log in to your Jijenge account to find services, manage requests, or continue offering your skills." />} />
    <Route path="/register" element={<PlaceholderPage title="Create your Jijenge account" text="Create one account to find services, offer your skills, or do both." />} />
    <Route path="/help" element={<PlaceholderPage title="How can we help?" text="Jijenge help and support will be available here." />} />
    <Route path="*" element={<PlaceholderPage title="Page not found" text="The page you are looking for does not exist." />} />
  </Routes></PublicLayout></BrowserRouter>
}
