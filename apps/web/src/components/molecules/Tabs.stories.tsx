import { Tabs, TabList, Tab, TabPanel } from "./Tabs";

const meta = { title: "Molecules/Tabs" };
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
export const Controlled = {
  render: () => (
    <Tabs value="second" onValueChange={() => {}}>
      <TabList aria-label="Widok kontrolowany">
        <Tab value="first">Dokument</Tab>
        <Tab value="second">Dane</Tab>
      </TabList>
      <TabPanel value="first">Dokument</TabPanel>
      <TabPanel value="second">Dane kontrolowane</TabPanel>
    </Tabs>
  ),
};
