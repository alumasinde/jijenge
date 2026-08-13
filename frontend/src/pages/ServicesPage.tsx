import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { Filter, Search, SlidersHorizontal, X } from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import { api } from '../lib/api'
import type { Service, ServiceCategory } from '../types'

export function ServicesPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [services, setServices] = useState<Service[]>([])
  const [categories, setCategories] = useState<ServiceCategory[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const query = searchParams.get('q') || ''
  const categoryId = Number(searchParams.get('category') || 0)
  const [search, setSearch] = useState(query)
  const [mobileFilters, setMobileFilters] = useState(false)

  useEffect(() => {
    setSearch(query)
  }, [query])

  useEffect(() => {
    let active = true
    setLoading(true)
    setError('')
    Promise.all([api.services(), api.categories()])
      .then(([serviceResponse, categoryResponse]) => {
        if (!active) return
        setServices(serviceResponse.items || [])
        setCategories(categoryResponse || [])
      })
      .catch(() => {
        if (active) setError('We could not load services right now. Please try again.')
      })
      .finally(() => active && setLoading(false))
    return () => { active = false }
  }, [])

  const filtered = useMemo(() => {
    const needle = query.trim().toLowerCase()
    return services.filter((service) => {
      const matchesCategory = !categoryId || service.category_id === categoryId
      const haystack = `${service.name} ${service.description || ''} ${service.category_name || ''}`.toLowerCase()
      return matchesCategory && (!needle || haystack.includes(needle))
    })
  }, [services, query, categoryId])

  function submitSearch(event: FormEvent) {
    event.preventDefault()
    const next = new URLSearchParams(searchParams)
    if (search.trim()) next.set('q', search.trim())
    else next.delete('q')
    setSearchParams(next)
  }

  function chooseCategory(id: number) {
    const next = new URLSearchParams(searchParams)
    if (id) next.set('category', String(id))
    else next.delete('category')
    setSearchParams(next)
    setMobileFilters(false)
  }

  function clearFilters() {
    setSearch('')
    setSearchParams({})
    setMobileFilters(false)
  }

  return (
    <main className="bg-slate-50">
      <section className="border-b border-slate-200 bg-white">
        <div className="mx-auto max-w-7xl px-5 py-10 lg:px-8 lg:py-14">
          <p className="text-sm font-black uppercase tracking-widest text-blue-600">Marketplace</p>
          <div className="mt-3 flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
            <div>
              <h1 className="text-4xl font-black tracking-tight sm:text-5xl">Find a service</h1>
              <p className="mt-3 max-w-2xl text-base leading-7 text-slate-500">Browse services offered by people on Jijenge. Search by what you need or explore a category.</p>
            </div>
            <Link to="/register" className="hidden rounded-xl bg-blue-600 px-5 py-3.5 text-sm font-bold text-white hover:bg-blue-700 sm:inline-flex">Offer your skills</Link>
          </div>
          <form onSubmit={submitSearch} className="mt-7 flex flex-col gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm sm:flex-row">
            <div className="flex min-w-0 flex-1 items-center gap-3 px-3">
              <Search size={20} className="shrink-0 text-slate-400" />
              <input value={search} onChange={(e) => setSearch(e.target.value)} className="w-full py-3 outline-none placeholder:text-slate-400" placeholder="Try plumbing, cleaning, painting..." aria-label="Search services" />
              {search && <button type="button" onClick={() => { setSearch(''); const next = new URLSearchParams(searchParams); next.delete('q'); setSearchParams(next) }} className="text-slate-400 hover:text-slate-700" aria-label="Clear search"><X size={18} /></button>}
            </div>
            <button className="rounded-xl bg-blue-600 px-7 py-3.5 font-bold text-white hover:bg-blue-700">Search services</button>
          </form>
        </div>
      </section>

      <section className="mx-auto max-w-7xl px-5 py-8 lg:px-8 lg:py-10">
        <button onClick={() => setMobileFilters(true)} className="mb-5 inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm font-bold md:hidden"><Filter size={17} /> Filters</button>
        <div className="grid gap-8 md:grid-cols-[220px_1fr] lg:grid-cols-[250px_1fr]">
          <aside className="hidden md:block">
            <div className="sticky top-24 rounded-2xl border border-slate-200 bg-white p-5">
              <div className="flex items-center justify-between"><h2 className="font-black">Categories</h2><SlidersHorizontal size={17} className="text-slate-400" /></div>
              <div className="mt-4 grid gap-1">
                <CategoryFilter label="All services" active={!categoryId} onClick={() => chooseCategory(0)} />
                {categories.map((category) => <CategoryFilter key={category.id} label={category.name} active={category.id === categoryId} onClick={() => chooseCategory(category.id)} />)}
              </div>
            </div>
          </aside>

          <div>
            <div className="mb-5 flex flex-wrap items-center justify-between gap-3">
              <div><p className="font-bold text-slate-900">{loading ? 'Loading services...' : `${filtered.length} service${filtered.length === 1 ? '' : 's'} available`}</p>{query && <p className="mt-1 text-sm text-slate-500">Results for “{query}”</p>}</div>
              {(query || categoryId) && <button onClick={clearFilters} className="text-sm font-bold text-blue-600 hover:text-blue-700">Clear filters</button>}
            </div>

            {loading && <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 6 }).map((_, i) => <div key={i} className="h-52 animate-pulse rounded-2xl border border-slate-200 bg-white" />)}</div>}
            {!loading && error && <div className="rounded-2xl border border-red-100 bg-red-50 p-6 text-sm font-semibold text-red-700">{error}</div>}
            {!loading && !error && filtered.length > 0 && <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{filtered.map((service) => <MarketplaceServiceCard key={service.id} service={service} />)}</div>}
            {!loading && !error && filtered.length === 0 && <div className="rounded-2xl border border-dashed border-slate-300 bg-white px-6 py-14 text-center"><div className="mx-auto grid h-12 w-12 place-items-center rounded-full bg-blue-50 text-blue-600"><Search size={21} /></div><h2 className="mt-4 text-xl font-black">No services found</h2><p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">Try a different search or browse all service categories.</p><button onClick={clearFilters} className="mt-5 rounded-xl bg-blue-600 px-5 py-3 text-sm font-bold text-white">Browse all services</button></div>}
          </div>
        </div>
      </section>

      {mobileFilters && <div className="fixed inset-0 z-[60] md:hidden"><button aria-label="Close filters" onClick={() => setMobileFilters(false)} className="absolute inset-0 bg-slate-950/40" /><div className="absolute inset-x-0 bottom-0 rounded-t-3xl bg-white p-6 shadow-2xl"><div className="flex items-center justify-between"><h2 className="text-xl font-black">Categories</h2><button onClick={() => setMobileFilters(false)} className="grid h-10 w-10 place-items-center rounded-xl border border-slate-200" aria-label="Close"><X size={19} /></button></div><div className="mt-5 grid gap-1"> <CategoryFilter label="All services" active={!categoryId} onClick={() => chooseCategory(0)} />{categories.map((category) => <CategoryFilter key={category.id} label={category.name} active={category.id === categoryId} onClick={() => chooseCategory(category.id)} />)}</div></div></div>}
    </main>
  )
}

function CategoryFilter({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return <button onClick={onClick} className={`flex items-center justify-between rounded-xl px-3 py-2.5 text-left text-sm font-semibold transition ${active ? 'bg-blue-50 text-blue-700' : 'text-slate-600 hover:bg-slate-50'}`}><span>{label}</span>{active && <span className="h-2 w-2 rounded-full bg-blue-600" />}</button>
}

function MarketplaceServiceCard({ service }: { service: Service }) {
  return <Link to={`/services/${service.id}`} className="group rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-lg"><div className="flex items-center justify-between gap-3"><span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-bold text-blue-700">{service.category_name || 'Service'}</span><span className="text-xs font-semibold text-slate-400">#{service.code}</span></div><h2 className="mt-5 text-lg font-black text-slate-950 group-hover:text-blue-700">{service.name}</h2><p className="mt-2 line-clamp-3 text-sm leading-6 text-slate-500">{service.description || 'Professional service available through Jijenge.'}</p><div className="mt-6 flex items-center justify-between border-t border-slate-100 pt-4"><span className="text-sm font-bold text-slate-700">View service</span><span className="text-sm font-black text-blue-600">→</span></div></Link>
}
