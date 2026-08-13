import { ArrowRight } from "lucide-react";
import type { Service } from "../types";

export function ServicePreview({ service }: { service: Service }) {
  return (
    <a
      href={`/services/${service.id}`}
      className="flex items-center justify-between gap-4 rounded-2xl border border-slate-200 bg-white p-4 transition hover:border-teal-200 hover:shadow-md"
    >
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-teal-700">{service.category_name || "Service"}</p>
        <h3 className="mt-1 font-bold text-slate-950">{service.name}</h3>
        {service.description && <p className="mt-1 line-clamp-1 text-sm text-slate-500">{service.description}</p>}
      </div>
      <span className="grid size-9 shrink-0 place-items-center rounded-full bg-slate-100 text-slate-700">
        <ArrowRight size={17} />
      </span>
    </a>
  );
}