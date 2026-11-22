"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getApi } from "./index";
import type { CheckStep, DocumentQuery } from "./schemas";

export const keys = {
  key: ["key"] as const,
  dashboard: ["dashboard"] as const,
  documents: (q?: DocumentQuery) => ["documents", q ?? {}] as const,
  document: (id: string) => ["document", id] as const,
  exportDecision: (id: string) => ["export", id] as const,
  classes: ["classes"] as const,
};

export const useKeyStatus = () => useQuery({ queryKey: keys.key, queryFn: () => getApi().getKeyStatus() });
export const useDashboard = () => useQuery({ queryKey: keys.dashboard, queryFn: () => getApi().getDashboard() });
export const useClasses = () => useQuery({ queryKey: keys.classes, queryFn: () => getApi().listClasses() });
export const useDocuments = (q?: DocumentQuery) =>
  useQuery({
    queryKey: keys.documents(q),
    queryFn: () => getApi().listDocuments(q),
    refetchInterval: (query) => (query.state.data?.some((d) => d.status === "running") ? 1000 : false),
  });
export const useDocument = (id: string) =>
  useQuery({
    queryKey: keys.document(id),
    queryFn: () => getApi().getDocument(id),
    refetchInterval: (query) => (query.state.data?.status === "running" ? 1000 : false),
  });
export const useExportDecision = (id: string) => useQuery({ queryKey: keys.exportDecision(id), queryFn: () => getApi().getExportDecision(id) });

function useInvalidate() {
  const qc = useQueryClient();
  return () => qc.invalidateQueries();
}

export function useSaveKey() {
  const inv = useInvalidate();
  return useMutation({ mutationFn: (v: { value: string; persist: boolean }) => getApi().saveKey(v), onSuccess: inv });
}
export function useAddDocuments() {
  const inv = useInvalidate();
  return useMutation({ mutationFn: (files: { name: string; sizeKb: number; type: string }[]) => getApi().addDocuments(files), onSuccess: inv });
}
export function useRetryDocument() {
  const inv = useInvalidate();
  return useMutation({ mutationFn: (id: string) => getApi().retryDocument(id), onSuccess: inv });
}
export function useChooseClass() {
  const inv = useInvalidate();
  return useMutation({ mutationFn: (v: { id: string; classId: string }) => getApi().chooseClass(v.id, v.classId), onSuccess: inv });
}
export function useUpdateField() {
  const inv = useInvalidate();
  return useMutation({ mutationFn: (v: { id: string; key: string; value: import("./schemas").Field["value"] }) => getApi().updateField(v.id, v.key, v.value), onSuccess: inv });
}
export function useExportJson() {
  return useMutation({ mutationFn: (id: string) => getApi().exportJson(id) });
}

export function useRunSelfCheck() {
  const qc = useQueryClient();
  return useMutation({
    retry: false,
    mutationFn: (onStep: (steps: CheckStep[]) => void) => getApi().runSelfCheck(onStep),
    onSettled: () => qc.invalidateQueries({ queryKey: keys.key }),
  });
}

export const useSystemInfo = () => useQuery({ queryKey: ["system-info"], queryFn: () => getApi().getSystemInfo() });
export const useUsers = () => useQuery({ queryKey: ["users"], queryFn: () => getApi().listUsers() });

export const useEvents = () => useQuery({ queryKey: ["events"], queryFn: () => getApi().listEvents() });

export const usePipeline = (id: string) => useQuery({ queryKey: ["pipeline", id], queryFn: () => getApi().getPipeline(id), refetchInterval: q => q.state.data?.stages.some(s => s.state === "w toku") ? 1000 : false });
export const useDiagnosis = (id: string) => useQuery({ queryKey: ["diagnosis", id], queryFn: () => getApi().getDiagnosis(id) });
export const useVersions = (id: string) => useQuery({ queryKey: ["versions", id], queryFn: () => getApi().getVersions(id) });
export function useRestoreVersion() {
  const inv = useInvalidate();
  return useMutation({ mutationFn: (v: { id: string; version: number }) => getApi().restoreVersion(v.id, v.version), onSuccess: inv });
}
