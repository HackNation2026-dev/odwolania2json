import { Tabs, TabList, Tab, TabPanel } from "./Tabs";

const meta = { title: "Molecules/Tab" };
export default meta;
export const Default = {
  render: () => (
    <Tabs defaultValue="first">
      <TabList aria-label="Widok">
        <Tab value="first">Dokument</Tab>
        <Tab value="second">Dane</Tab>
        <Tab value="disabled" disabled>
          Niedostępne
        </Tab>
      </TabList>
      <TabPanel value="first">Treść dokumentu</TabPanel>
      <TabPanel value="second">Dane dokumentu</TabPanel>
    </Tabs>
  ),
};
