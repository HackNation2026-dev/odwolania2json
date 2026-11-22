"use client";
import { ModalFrame, type ModalProps } from "./ModalFrame";
export type DialogProps = ModalProps;
export function Dialog(props: DialogProps) {
  return <ModalFrame {...props} />;
}
