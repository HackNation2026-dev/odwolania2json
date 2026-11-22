import { Button, type ButtonProps } from "./Button";
import { Icon, type IconName } from "./Icon";
export type IconButtonProps = Omit<ButtonProps, "children" | "aria-label"> & {
  label: string;
  icon: IconName;
};
export function IconButton({ label, icon, ...props }: IconButtonProps) {
  return (
    <Button
      touch
      {...props}
      aria-label={label}
      className={`min-w-11 md:min-w-10 px-2! ${props.className ?? ""}`}
    >
      <Icon name={icon} />
    </Button>
  );
}
