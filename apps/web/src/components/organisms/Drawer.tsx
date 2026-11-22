"use client";
import { ModalFrame, type ModalProps } from "./ModalFrame";
export type DrawerProps = ModalProps;
export function Drawer(props: DrawerProps) {
  return <ModalFrame {...props} drawer />;
}
