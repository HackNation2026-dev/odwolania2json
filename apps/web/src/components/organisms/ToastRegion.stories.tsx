import { ToastRegion, useToast } from "./ToastRegion";
import { Button } from "@/components/atoms";
function ToastTrigger() {
  const { toast } = useToast();
  return (
    <Button
      onClick={() =>
        toast({
          title: "Zapisano",
          description: "Dokument został zapisany.",
          tone: "success",
        })
      }
    >
      Pokaż powiadomienie
    </Button>
  );
}
const meta = { title: "Organisms/ToastRegion" };
export default meta;
export const Default = {
  render: () => (
    <ToastRegion>
      <ToastTrigger />
    </ToastRegion>
  ),
};
