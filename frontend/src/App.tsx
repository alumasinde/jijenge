import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider, useTheme } from "./contexts/ThemeContext";
import { BrandingProvider } from "./contexts/BrandingContext";
import { PublicContentProvider } from "./contexts/PublicContentContext";
import Home from "./pages/Home";
import Login from "./pages/Login";
import Register from "./pages/Register";
import FindProviders from "./pages/FindProviders";
import NotFound from "./pages/NotFound";
import PublicContentAdmin from "./pages/PublicContentAdmin";

function Router() {
  return (
    <Switch>
      <Route path="/" component={Home} />
      <Route path="/login" component={Login} />
      <Route path="/register" component={Register} />
      <Route path="/find-providers" component={FindProviders} />
      <Route path="/admin/public-content" component={PublicContentAdmin} />
      <Route path="/404" component={NotFound} />
      <Route component={NotFound} />
    </Switch>
  );
}

// Bridges the light/dark toggle into BrandingProvider, since branding
// colors can define separate dark-mode overrides (dark_theme on the
// branding record) that only apply once .dark is active.
function BrandedApp() {
  const { theme } = useTheme();
  return (
    <BrandingProvider isDark={theme === "dark"}>
      <PublicContentProvider>
        <TooltipProvider>
          <Toaster />
          <Router />
        </TooltipProvider>
      </PublicContentProvider>
    </BrandingProvider>
  );
}

export default function App() {
  return (
    <ErrorBoundary>
      <ThemeProvider defaultTheme="light" switchable>
        <BrandedApp />
      </ThemeProvider>
    </ErrorBoundary>
  );
}
