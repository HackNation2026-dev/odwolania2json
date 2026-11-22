"use client";
import {
  useEffect,
  useId,
  useRef,
  type ReactNode,
  type RefObject,
} from "react";
import { createPortal } from "react-dom";
import { IconButton } from "@/components/atoms";
export type ModalProps = {
  open: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: ReactNode;
  actions?: ReactNode;
  initialFocusRef?: RefObject<HTMLElement | null>;
};
const layers: HTMLElement[] = [];
let originalOverflow = "";
const focusable =
  'a[href],button:not(:disabled),input:not(:disabled),select:not(:disabled),textarea:not(:disabled),[tabindex]:not([tabindex="-1"])';
function controls(node: HTMLElement) {
  return Array.from(node.querySelectorAll<HTMLElement>(focusable)).filter(
    (el) =>
      el.tabIndex >= 0 &&
      !el.matches(':disabled,input[type="hidden"]') &&
      !el.closest('[hidden],[inert],[aria-hidden="true"]'),
  );
}
export function ModalFrame({
  open,
  onClose,
  title,
  description,
  children,
  actions,
  initialFocusRef,
  drawer = false,
}: ModalProps & { drawer?: boolean }) {
  const id = useId();
  const panel = useRef<HTMLDivElement>(null);
  const closeRef = useRef(onClose);
  useEffect(() => {
    closeRef.current = onClose;
  }, [onClose]);
  useEffect(() => {
    if (!open || !panel.current) return;
    const node = panel.current;
    const previous =
      document.activeElement instanceof HTMLElement
        ? document.activeElement
        : null;
    if (!layers.length) {
      originalOverflow = document.body.style.overflow;
      document.body.style.overflow = "hidden";
    }
    layers.push(node);
    (initialFocusRef?.current ?? controls(node)[0] ?? node).focus();
    function keydown(event: KeyboardEvent) {
      if (layers.at(-1) !== node) return;
      if (event.key === "Escape") {
        event.preventDefault();
        event.stopPropagation();
        closeRef.current();
      }
      if (event.key === "Tab") {
        const items = controls(node);
        const first = items[0] ?? node,
          last = items.at(-1) ?? node;
        if (!items.length) {
          event.preventDefault();
          node.focus();
        } else if (
          event.shiftKey &&
          (document.activeElement === first || document.activeElement === node)
        ) {
          event.preventDefault();
          last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first.focus();
        }
      }
    }
    function contain(event: FocusEvent) {
      if (layers.at(-1) === node && !node.contains(event.target as Node))
        (controls(node)[0] ?? node).focus();
    }
    document.addEventListener("keydown", keydown);
    document.addEventListener("focusin", contain);
    return () => {
      document.removeEventListener("keydown", keydown);
      document.removeEventListener("focusin", contain);
      layers.splice(layers.indexOf(node), 1);
      if (!layers.length) document.body.style.overflow = originalOverflow;
      if (previous?.isConnected) previous.focus();
    };
  }, [open, initialFocusRef]);
  if (!open || typeof document === "undefined") return null;
  return createPortal(
    <div
      className={`fixed inset-0 z-50 flex bg-[var(--pdf-canvas)]/80 p-4 ${drawer ? "justify-start p-0" : "items-center justify-center"}`}
    >
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-title`}
        aria-describedby={description ? `${id}-description` : undefined}
        tabIndex={-1}
        className={`max-h-dvh overflow-y-auto border border-border bg-surface p-5 shadow-[var(--shadow-2)] ${drawer ? "h-dvh w-72 max-w-full" : "w-full max-w-[480px] rounded-lg"}`}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <h2 id={`${id}-title`} className="text-lg font-semibold">
            {title}
          </h2>
          <IconButton label="Zamknij" icon="x" onClick={onClose} />
        </div>
        {description && (
          <p id={`${id}-description`} className="mb-4 text-sm text-muted">
            {description}
          </p>
        )}
        <div className="min-w-0">{children}</div>
        {actions && (
          <div className="mt-5 flex flex-wrap justify-end gap-2">{actions}</div>
        )}
      </div>
    </div>,
    document.body,
  );
}
