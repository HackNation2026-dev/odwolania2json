import Link from "next/link";
import type { ComponentProps } from "react";
import { cn } from "@/lib/cn";
export function TextLink({ className, ...props }: ComponentProps<typeof Link>) {
  return (
    <Link
      {...props}
      className={cn(
        "inline-flex min-h-11 md:min-h-10 items-center text-primary underline underline-offset-4 hover:opacity-90",
        className,
      )}
    />
  );
}
