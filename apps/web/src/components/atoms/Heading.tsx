import type { ElementType, HTMLAttributes } from "react";
import { cn } from "@/lib/cn";
export type HeadingProps = HTMLAttributes<HTMLHeadingElement> & {
  level: 1 | 2 | 3 | 4;
  as?: ElementType;
  size?: "sm" | "md" | "lg" | "xl";
};
export function Heading({
  level,
  as: Tag = `h${level}`,
  size,
  className,
  ...props
}: HeadingProps) {
  return (
    <Tag
      {...props}
      role="heading"
      aria-level={level}
      className={cn(
        "font-semibold text-fg",
        size
          ? { sm: "text-base", md: "text-xl", lg: "text-2xl", xl: "text-3xl" }[
              size
            ]
          : { 1: "text-3xl", 2: "text-2xl", 3: "text-xl", 4: "text-base" }[
              level
            ],
        className,
      )}
    />
  );
}
