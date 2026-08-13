import React, { createContext, useContext, useEffect, useMemo, useState } from "react";
import { getPublicContent, type PublicContentValue } from "@/lib/api";

type ContentMap = Record<string, PublicContentValue>;

interface PublicContentContextValue {
  content: ContentMap;
  loading: boolean;
  error: boolean;
  refresh: () => Promise<void>;
  text: (key: string) => string;
  list: (key: string) => string[];
}

const PublicContentContext = createContext<PublicContentContextValue | undefined>(undefined);

function asText(value: PublicContentValue | undefined): string {
  return typeof value === "string" ? value : "";
}

function asList(value: PublicContentValue | undefined): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

export function PublicContentProvider({ children, locale = "en-KE" }: { children: React.ReactNode; locale?: string }) {
  const [content, setContent] = useState<ContentMap>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const refresh = async () => {
    setLoading(true);
    setError(false);
    try {
      setContent(await getPublicContent(locale));
    } catch {
      setError(true);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
  }, [locale]);

  const value = useMemo<PublicContentContextValue>(() => ({
    content,
    loading,
    error,
    refresh,
    text: (key) => asText(content[key]),
    list: (key) => asList(content[key]),
  }), [content, loading, error]);

  return <PublicContentContext.Provider value={value}>{children}</PublicContentContext.Provider>;
}

export function usePublicContent() {
  const value = useContext(PublicContentContext);
  if (!value) throw new Error("usePublicContent must be used within PublicContentProvider");
  return value;
}
