import { ArrowUpRight, BriefcaseBusiness, Brush, Car, Computer, Home, Scissors, Wrench } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { ServiceCategory } from '../types'
const icons = [Home, Brush, Car, Scissors, Computer, BriefcaseBusiness, Wrench]
export function CategoryCard({ category, index }: { category: ServiceCategory; index: number }) {
  const Icon = icons[index % icons.length]
  return <Link to={`/services?category=${category.id}`} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-1 hover:border-blue-200 hover:shadow-lg"><div className="flex items-start justify-between"><span className="grid h-11 w-11 place-items-center rounded-xl bg-blue-50 text-blue-600"><Icon size={21}/></span><ArrowUpRight size={18} className="text-slate-300 transition group-hover:text-blue-600"/></div><h3 className="mt-7 font-bold text-slate-950">{category.name}</h3><p className="mt-2 line-clamp-2 text-sm leading-6 text-slate-500">{category.description || `Find ${category.name.toLowerCase()} providers on Jijenge.`}</p></Link>
}
