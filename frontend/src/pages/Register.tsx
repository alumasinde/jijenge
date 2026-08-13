import { useState, type FormEvent } from "react";
import { Link, useLocation } from "wouter";
import { ArrowUpRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { register } from "@/lib/api";
import { useBranding } from "@/contexts/BrandingContext";

export default function Register() {
  const { branding } = useBranding();
  const [, navigate] = useLocation();
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (!email && !phone) {
      toast.error("Add an email or phone number so we can reach you");
      return;
    }
    setSubmitting(true);
    try {
      await register({ firstName, lastName, email: email || undefined, phone: phone || undefined, password });
      toast.success("Account created");
      navigate("/");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't create your account");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-5 py-16 text-foreground">
      <div className="w-full max-w-sm">
        <Link href="/" className="mb-8 inline-flex items-center gap-2 text-sm font-bold text-muted-foreground transition hover:text-foreground">
          &larr; Back to {branding.short_name}
        </Link>

        <h1 className="font-display text-4xl font-bold leading-[.95] tracking-[-.04em]">Create your account</h1>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">Find trusted providers or list your own services.</p>

        <form onSubmit={handleSubmit} className="mt-9 grid gap-4">
          <div className="grid grid-cols-2 gap-3">
            <div className="grid gap-1.5">
              <label htmlFor="firstName" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">First name</label>
              <input id="firstName" value={firstName} onChange={(e) => setFirstName(e.target.value)} required autoComplete="given-name" className="rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none transition focus:border-primary" />
            </div>
            <div className="grid gap-1.5">
              <label htmlFor="lastName" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">Last name</label>
              <input id="lastName" value={lastName} onChange={(e) => setLastName(e.target.value)} required autoComplete="family-name" className="rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none transition focus:border-primary" />
            </div>
          </div>
          <div className="grid gap-1.5">
            <label htmlFor="email" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" className="rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none transition focus:border-primary" placeholder="you@example.com" />
          </div>
          <div className="grid gap-1.5">
            <label htmlFor="phone" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">Phone (optional if email given)</label>
            <input id="phone" value={phone} onChange={(e) => setPhone(e.target.value)} autoComplete="tel" className="rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none transition focus:border-primary" placeholder="07xx xxx xxx" />
          </div>
          <div className="grid gap-1.5">
            <label htmlFor="password" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} required minLength={12} autoComplete="new-password" className="rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none transition focus:border-primary" placeholder="At least 12 characters" />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="mt-2 inline-flex items-center justify-center gap-2 rounded-full bg-primary px-5 py-3.5 text-sm font-bold text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
          >
            {submitting ? <Loader2 size={17} className="animate-spin" /> : <>Create account <ArrowUpRight size={17} /></>}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link href="/login" className="font-bold text-foreground underline underline-offset-4">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
