import { Link } from 'react-router-dom'
interface Props { name?: string; logoUrl?: string | null }
export function Logo({ name = 'Jijenge', logoUrl }: Props) {
  return <Link to="/" className="flex items-center gap-2.5 font-black tracking-tight text-slate-950" aria-label={`${name} home`}>
    {logoUrl ? <img src={logoUrl} alt="" className="h-9 w-9 rounded-xl object-contain" /> : <span className="grid h-9 w-9 place-items-center rounded-xl bg-blue-600 text-lg text-white shadow-sm">J</span>}
    <span className="text-xl">{name}</span>
  </Link>
}
