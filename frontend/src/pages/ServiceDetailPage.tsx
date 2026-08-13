import { ArrowLeft, CheckCircle2, MapPin, ShieldCheck, Users, type LucideIcon } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api } from '../lib/api'
import type { Service } from '../types'

export function ServiceDetailPage() {
  const { serviceId } = useParams()
  const [service, setService] = useState<Service | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    api.services().then((response) => {
      const found = response.items.find((item) => String(item.id) === String(serviceId))
      setService(found || null)
    }).catch(() => setService(null)).finally(() => setLoading(false))
  }, [serviceId])

  if (loading) return <main className="bg-slate-50 px-5 py-12 lg:px-8"><div className="mx-auto max-w-4xl animate-pulse rounded-3xl border border-slate-200 bg-white p-8"><div className="h-5 w-32 rounded bg-slate-100"/><div className="mt-5 h-12 w-3/4 rounded bg-slate-100"/><div className="mt-5 h-24 rounded bg-slate-100"/></div></main>

  if (!service) return <main className="mx-auto max-w-4xl px-5 py-20 text-center lg:px-8"><p className="text-sm font-black uppercase tracking-widest text-blue-600">Jijenge</p><h1 className="mt-3 text-4xl font-black">Service not found</h1><p className="mt-3 text-slate-500">This service may no longer be available.</p><Link to="/services" className="mt-6 inline-flex rounded-xl bg-blue-600 px-5 py-3 font-bold text-white">Browse services</Link></main>

  return <main className="bg-slate-50"><section className="mx-auto max-w-5xl px-5 py-8 lg:px-8 lg:py-12"><Link to="/services" className="inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-blue-600"><ArrowLeft size={16} /> Back to services</Link><div className="mt-6 grid gap-6 lg:grid-cols-[1fr_320px] lg:items-start"><article className="rounded-3xl border border-slate-200 bg-white p-7 shadow-sm sm:p-10"><span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-black text-blue-700">{service.category_name || 'Service'}</span><h1 className="mt-5 text-4xl font-black tracking-tight sm:text-5xl">{service.name}</h1><p className="mt-5 text-lg leading-8 text-slate-600">{service.description || 'Find skilled people who offer this service through Jijenge.'}</p><div className="mt-8 grid gap-3 border-t border-slate-100 pt-7"><Benefit icon={Users} text="Connect with people offering this service"/><Benefit icon={MapPin} text="Discover providers based on your needs and location"/><Benefit icon={ShieldCheck} text="Manage requests and jobs through your Jijenge account"/></div></article><aside className="rounded-3xl border border-slate-200 bg-white p-6 shadow-sm"><h2 className="text-xl font-black">Need this service?</h2><p className="mt-2 text-sm leading-6 text-slate-500">Create an account to discover providers and request work.</p><Link to="/register" className="mt-6 block rounded-xl bg-blue-600 px-5 py-3.5 text-center font-bold text-white hover:bg-blue-700">Create account</Link><Link to="/login" className="mt-2 block rounded-xl border border-slate-200 px-5 py-3.5 text-center font-bold text-slate-700 hover:bg-slate-50">Log in</Link><div className="mt-5 flex items-center gap-2 text-xs font-semibold text-slate-400"><CheckCircle2 size={15} className="text-emerald-500"/> Free account to get started</div></aside></div></section></main>
}

function Benefit({ icon: Icon, text }: { icon: LucideIcon; text: string }) {
  return <div className="flex items-center gap-3 text-sm font-semibold text-slate-700"><span className="grid h-9 w-9 place-items-center rounded-xl bg-slate-50 text-blue-600"><Icon size={17}/></span>{text}</div>
}
