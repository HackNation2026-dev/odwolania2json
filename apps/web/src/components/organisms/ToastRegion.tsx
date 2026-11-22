"use client";
import {
  createContext,
  useContext,
  useState,
  useId,
  useCallback,
  type ReactNode,
} from "react";
import { IconButton } from "@/components/atoms";
import { Banner, type BannerTone } from "@/components/molecules/Banner";
export type ToastMessage = {
  title: string;
  description?: string;
  tone?: BannerTone;
};
type ToastContextValue = {
  toast: (message: ToastMessage) => string;
  dismiss: (id: string) => void;
};
const ToastContext = createContext<ToastContextValue | null>(null);
export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast wymaga ToastRegion.");
  return context;
}
export function ToastRegion({ children }: { children: ReactNode }) {
  const prefix = useId();
  const [messages, setMessages] = useState<(ToastMessage & { id: string })[]>(
    [],
  );
  const dismiss = useCallback(
    (id: string) =>
      setMessages((current) => current.filter((message) => message.id !== id)),
    [],
  );
  const toast = useCallback(
    (message: ToastMessage) => {
      const id = `${prefix}-${crypto.randomUUID()}`;
      setMessages((current) => [...current, { ...message, id }]);
      return id;
    },
    [prefix],
  );
  return (
    <ToastContext value={{ toast, dismiss }}>
      {children}
      <section
        aria-label="Powiadomienia"
        aria-live="polite"
        aria-relevant="additions removals"
        className="fixed right-4 bottom-4 z-[60] w-[calc(100%-2rem)] max-w-sm space-y-2"
      >
        {messages.map((message) => (
          <Banner
            key={message.id}
            role="note"
            tone={message.tone ?? "info"}
            title={message.title}
            actions={
              <IconButton
                icon="x"
                label={`Zamknij powiadomienie: ${message.title}`}
                onClick={() => dismiss(message.id)}
              />
            }
          >
            {message.description}
          </Banner>
        ))}
      </section>
    </ToastContext>
  );
}
