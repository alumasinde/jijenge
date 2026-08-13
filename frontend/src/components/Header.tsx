import { Menu, X } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Logo } from './Logo'

export function Header({ appName, logoUrl }: { appName?: string; logoUrl?: string | null }) {
  const [open, setOpen] = useState(false)
  const close = () => setOpen(false)
  return <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur">
    <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5 lg:px-8">
      <Link to="/" onClick={close}><Logo name={appName} logoUrl={logoUrl} /></Link>
      <nav className="hidden items-center gap-7 text-sm font-semibold text-slate-600 md:flex">
        <Link to="/services" className="hover:text-blue-600">Find a service</Link>
        <Link to="/#how-it-works" className="hover:text-blue-600">How it works</Link>
        <Link to="/#providers" className="hover:text-blue-600">For providers</Link>
      </nav>
      <div className="hidden items-center gap-3 md:flex"><Link to="/login" className="px-3 py-2 text-sm font-bold text-slate-700 hover:text-blue-600">Log in</Link><Link to="/register" className="rounded-xl bg-blue-600 px-4 py-2.5 text-sm font-bold text-white shadow-sm hover:bg-blue-700">Create account</Link></div>
      <button onClick={() => setOpen(!open)} className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200 md:hidden" aria-label="Toggle menu">{open ? <X/> : <Menu/>}</button>
    </div>
    {open && <div className="border-t border-slate-200 bg-white px-5 py-4 md:hidden"><div className="grid gap-1 text-sm font-semibold"><Link onClick={close} to="/services" className="rounded-lg px-3 py-3 hover:bg-slate-50">Find a service</Link><Link onClick={close} to="/#how-it-works" className="rounded-lg px-3 py-3 hover:bg-slate-50">How it works</Link><Link onClick={close} to="/#providers" className="rounded-lg px-3 py-3 hover:bg-slate-50">For providers</Link><div className="mt-2 grid grid-cols-2 gap-2"><Link onClick={close} to="/login" className="rounded-xl border px-4 py-3 text-center">Log in</Link><Link onClick={close} to="/register" className="rounded-xl bg-blue-600 px-4 py-3 text-center text-white">Create account</Link></div></div></div>}
  </header>
}
