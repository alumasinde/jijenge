import { ArrowRight, Tag } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { Service } from '../types'
export function ServiceCard({ service }: { service: Service }) {
 return <Link to={`/services/${service.id}`} className="group rounded-2xl border border-slate-200 bg-white p-5 transition hover:border-blue-200 hover:shadow-md"><div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wide text-blue-600"><Tag size={14}/>{service.category_name || 'Service'}</div><h3 className="mt-4 font-bold text-slate-950">{service.name}</h3><p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">{service.description || 'Professional service available through Jijenge.'}</p><span className="mt-5 inline-flex items-center gap-1 text-sm font-bold text-slate-700 group-hover:text-blue-600">Explore <ArrowRight size={15}/></span></Link>
}
