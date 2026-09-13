export function thb(v: number | null | undefined, currency = "THB"): string {
  if (v == null) return "—";
  const n = Number.isInteger(v) ? v.toLocaleString("th-TH") : v.toLocaleString("th-TH", { maximumFractionDigits: 2 });
  return currency === "THB" ? `฿${n}` : `${currency} ${n}`;
}

export function relativeTime(iso: string): string {
  const diff = (Date.now() - new Date(iso).getTime()) / 1000;
  if (diff < 60) return "เมื่อสักครู่";
  if (diff < 3600) return `${Math.floor(diff / 60)} นาทีที่แล้ว`;
  if (diff < 86400) return `${Math.floor(diff / 3600)} ชั่วโมงที่แล้ว`;
  return new Date(iso).toLocaleDateString("th-TH", { day: "numeric", month: "short", year: "numeric" });
}

export function duration(start: string, end: string | null): string {
  if (!end) return "";
  const s = Math.round((new Date(end).getTime() - new Date(start).getTime()) / 1000);
  return s < 60 ? `${s} วินาที` : `${Math.floor(s / 60)} นาที ${s % 60} วินาที`;
}

/** "[17:53:20] plan: keyword · 10 queries" → { time, stage, message } */
export function parseEvent(line: string): { time: string; stage: string; message: string } {
  const m = line.match(/^\[(\d\d:\d\d:\d\d)\]\s*(\w+):\s*(.*)$/) ?? line.match(/^(\w+):\s*(.*)$/);
  if (!m) return { time: "", stage: "", message: line };
  return m.length === 4 ? { time: m[1], stage: m[2], message: m[3] } : { time: "", stage: m[1], message: m[2] };
}
