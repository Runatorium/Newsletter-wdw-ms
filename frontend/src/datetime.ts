export function dayStart(s: string): string | undefined {
  if (!s.trim()) return undefined;
  return `${s}T00:00:00`;
}

export function dayEnd(s: string): string | undefined {
  if (!s.trim()) return undefined;
  return `${s}T23:59:59.999999`;
}

export function fmtDate(s: string) {
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleString();
}
