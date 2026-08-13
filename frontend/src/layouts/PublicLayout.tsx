import type { ReactNode } from 'react'
import { useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { Header } from '../components/Header'
import { Logo } from '../components/Logo'
import type { Branding } from '../types'

export function PublicLayout({ branding, children }: { branding: Branding; children: ReactNode }) {
 const location = useLocation()
 useEffect(() => { if (location.hash) requestAnimationFrame(() => document.getElementById(location.hash.slice(1))?.scrollIntoView({ behavior: 'smooth' })) }, [location.pathname, location.hash])
 return <div className="min-h-screen bg-white text-slate-950" style={{fontFamily: branding.font_family || undefined}}><Header appName={branding.app_name} logoUrl={branding.logo_url}/>{children}<footer className="border-t border-slate-200 bg-slate-50"><div className="mx-auto grid max-w-7xl gap-8 px-5 py-12 sm:grid-cols-2 lg:grid-cols-4 lg:px-8"><div><Link to="/" className="inline-block"><Logo name={branding.app_name}/></Link><p className="mt-4 max-w-xs text-sm leading-6 text-slate-500">Find services, offer your skills and get things done through one marketplace.</p></div><div><h3 className="font-bold">Discover</h3><div className="mt-4 grid gap-2 text-sm text-slate-500"><a href="/#services">Services</a><a href="/#how-it-works">How it works</a><a href="/services">Browse services</a></div></div><div><h3 className="font-bold">Providers</h3><div className="mt-4 grid gap-2 text-sm text-slate-500"><a href="/#providers">Become a provider</a><a href="/login">Provider login</a></div></div><div><h3 className="font-bold">Account</h3><div className="mt-4 grid gap-2 text-sm text-slate-500"><a href="/register">Create account</a><a href="/login">Log in</a><a href="/help">Help</a></div></div></div><div className="border-t border-slate-200"><div className="mx-auto flex max-w-7xl flex-col gap-2 px-5 py-5 text-xs text-slate-500 sm:flex-row sm:justify-between lg:px-8"><span>© {new Date().getFullYear()} {branding.app_name || 'Jijenge'}</span><span>Privacy · Terms</span></div></div></footer></div>
}
