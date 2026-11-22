import { LoadMore } from "./LoadMore";

const meta = { title: "Molecules/LoadMore" };
export default meta;
export const Default = {
  render: () => <LoadMore shown={20} total={80} onLoad={() => {}} />,
};
export const Loading = {
  render: () => <LoadMore shown={20} total={80} onLoad={() => {}} loading />,
};
export const Complete = {
  render: () => (
    <LoadMore shown={80} total={80} onLoad={() => {}} hasMore={false} />
  ),
};
