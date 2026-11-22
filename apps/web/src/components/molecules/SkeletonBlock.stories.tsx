import { SkeletonBlock } from "./LoadingState";

const meta = { title: "Molecules/SkeletonBlock" };
export default meta;
export const Default = { render: () => <SkeletonBlock lines={4} /> };
export const Empty = { render: () => <SkeletonBlock lines={0} /> };
