import { useState } from "react";
import type { Meta, StoryObj } from "@storybook/nextjs-vite";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { setApiForTests } from "@/lib/api";
import { createMockClient } from "@/lib/api/mock/client";
import { createClassMock, type ClassMockScenario } from "@/lib/api/mock/klasy";
import { ClassDetailView } from "./ClassDetailView";

function Scenario({ scenario }: { scenario: ClassMockScenario }) {
  const [client] = useState(() => {
    setApiForTests({
      ...createMockClient({ latencyMs: 0 }),
      ...createClassMock(
        (value) =>
          new Promise((resolve) => setTimeout(() => resolve(value), 600)),
        scenario,
      ),
    });
    return new QueryClient({ defaultOptions: { queries: { retry: false } } });
  });
  return (
    <QueryClientProvider client={client}>
      <ClassDetailView id="przelew" initialTab="test" />
    </QueryClientProvider>
  );
}

const meta = {
  title: "Features/Klasy/Szczegóły",
  component: Scenario,
} satisfies Meta<typeof Scenario>;
export default meta;
type Story = StoryObj<typeof meta>;
export const Ready: Story = { args: { scenario: "ready" } };
export const InvalidLine14: Story = { args: { scenario: "invalid" } };
export const ActivationError: Story = {
  args: { scenario: "activation-error" },
};
export const NoConfiguration: Story = {
  args: { scenario: "no-configuration" },
};
