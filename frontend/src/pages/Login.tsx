import { useState, type FormEvent } from "react";
import { Link, useLocation } from "wouter";
import { ArrowUpRight, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { login } from "@/lib/api";
import { useBranding } from "@/contexts/BrandingContext";

export default function Login() {
  const { branding } = useBranding();
  const [, navigate] = useLocation();
  const [identifier, setIdentifier] = useState("");
  const [password, setPassword] = useState("");
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setSubmitting(true);
    try {
      await login(identifier, password);
      toast.success("Signed in");
      navigate("/");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Couldn't sign in");
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

        <h1 className="font-display text-4xl font-bold leading-[.95] tracking-[-.04em]">Welcome back</h1>
        <p className="mt-3 text-sm leading-6 text-muted-foreground">Sign in to book services and track your requests.</p>

        <form onSubmit={handleSubmit} className="mt-9 grid gap-4">
          <div className="grid gap-1.5">
            <label htmlFor="identifier" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">Email or phone</label>
            <input
              id="identifier"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              required
              autoComplete="username"
              className="rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none transition focus:border-primary"
              placeholder="you@example.com"
            />
          </div>
          <div className="grid gap-1.5">
            <label htmlFor="password" className="text-xs font-bold uppercase tracking-[.14em] text-muted-foreground">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="current-password"
              className="rounded-xl border border-border bg-card px-4 py-3 text-sm outline-none transition focus:border-primary"
              placeholder="••••••••••••"
            />
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="mt-2 inline-flex items-center justify-center gap-2 rounded-full bg-primary px-5 py-3.5 text-sm font-bold text-primary-foreground transition hover:opacity-90 disabled:opacity-60"
          >
            {submitting ? <Loader2 size={17} className="animate-spin" /> : <>Sign in <ArrowUpRight size={17} /></>}
          </button>
        </form>

        <p className="mt-8 text-center text-sm text-muted-foreground">
          New to {branding.short_name}?{" "}
          <Link href="/register" className="font-bold text-foreground underline underline-offset-4">Create an account</Link>
        </p>
      </div>
    </div>
  );
}
