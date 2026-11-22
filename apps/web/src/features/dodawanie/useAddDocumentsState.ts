"use client";
import { useState } from "react";
import type { SelectedPdf } from "@/components/molecules/DropZone";
import {
  useAddDocuments,
  useClasses,
  useDocuments,
  useKeyStatus,
  useCheckPathCollision,
  useAddResolvedDocuments,
} from "@/lib/api/hooks";
export const identity = (file: SelectedPdf) => `${file.name}:${file.sizeKb}`;
export function useAddDocumentsState() {
  const key = useKeyStatus();
  const classes = useClasses();
  const documents = useDocuments();
  const add = useAddDocuments();
  const collision = useCheckPathCollision();
  const resolved = useAddResolvedDocuments();
  const [collisionOpen, setCollisionOpen] = useState(false);
  const [files, setFiles] = useState<SelectedPdf[]>([]);
  const [messages, setMessages] = useState<string[]>([]);
  const [submittedIds, setSubmittedIds] = useState<string[]>([]);
  const [caseName, setCaseName] = useState("");
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("newest");
  const submitted = submittedIds
    .map(
      (id) =>
        documents.data?.find((d) => d.id === id) ??
        add.data?.find((d) => d.id === id),
    )
    .filter((d) => d !== undefined);
  const completed = submitted.filter((d) => d.status !== "running").length;
  const finished =
    submitted.length === submittedIds.length &&
    submittedIds.length > 0 &&
    completed === submittedIds.length;
  const locked =
    add.isPending ||
    collision.isPending ||
    resolved.isPending ||
    (submittedIds.length > 0 && !finished);
  const recent = [...(documents.data ?? [])]
    .filter((d) =>
      d.fileName
        .toLocaleLowerCase("pl")
        .includes(search.toLocaleLowerCase("pl")),
    )
    .sort((a, b) =>
      sort === "name"
        ? a.fileName.localeCompare(b.fileName, "pl")
        : b.uploadedAt.localeCompare(a.uploadedAt),
    )
    .slice(0, 6);

  function selectFiles(incoming: SelectedPdf[], skipped: string[]) {
    const next = [...files];
    for (const file of incoming) {
      if (next.some((existing) => identity(existing) === identity(file)))
        skipped.push(`${file.name}: ten sam plik jest już na liście.`);
      else next.push(file);
    }
    if (!caseName && next.length > 0)
      setCaseName(
        `Sprawa z ${new Date().toLocaleString("pl-PL", { dateStyle: "short", timeStyle: "short" })}`,
      );
    setFiles(next);
    setMessages(skipped);
  }
  function analyze() {
    if (
      !classes.data?.some((c) => c.id !== "obcy") ||
      !key.data?.configured ||
      files.length === 0 ||
      locked
    )
      return;
    collision.mutate(files, {
      onSuccess: (collisions) => {
        if (collisions.length) setCollisionOpen(true);
        else
          add.mutate(files, {
            onSuccess: (added) => setSubmittedIds(added.map((d) => d.id)),
          });
      },
    });
  }
  function clear() {
    setFiles([]);
    setMessages([]);
    setSubmittedIds([]);
    add.reset();
  }
  function resolveCollision(choice: "version" | "package") {
    resolved.mutate(
      { files, choice },
      {
        onSuccess: (added) => {
          setSubmittedIds(added.map((d) => d.id));
          setCollisionOpen(false);
        },
      },
    );
  }
  return {
    key,
    classes,
    documents,
    add,
    files,
    setFiles,
    messages,
    submittedIds,
    caseName,
    setCaseName,
    search,
    setSearch,
    sort,
    setSort,
    submitted,
    finished,
    locked,
    recent,
    selectFiles,
    analyze,
    clear,
    collision,
    resolved,
    collisionOpen,
    setCollisionOpen,
    resolveCollision,
  };
}
