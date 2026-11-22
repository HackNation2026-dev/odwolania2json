import { useState } from "react";
import { Button } from "@/components/atoms/Button";
import { AppShellMobileMenu } from "./AppShellMobileMenu";

const meta = {
  title: "Organisms/AppShellMobileMenu",
  component: AppShellMobileMenu,
};
export default meta;
function Example() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button onClick={() => setOpen(true)}>Otwórz menu</Button>
      <AppShellMobileMenu
        open={open}
        onClose={() => setOpen(false)}
        pathname="/dodaj"
      />
    </>
  );
}
export const Default = { render: () => <Example /> };
