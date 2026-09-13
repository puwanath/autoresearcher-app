import type { TaskStatus } from "@/lib/api";

const STYLE: Record<TaskStatus, { label: string; cls: string; dot: string }> = {
  pending: { label: "รอคิว", cls: "bg-canvas text-ink-2", dot: "bg-ink-3" },
  running: { label: "กำลังวิจัย", cls: "bg-accent/10 text-accent", dot: "bg-accent pulse-dot" },
  completed: { label: "เสร็จสิ้น", cls: "bg-success/10 text-[#1f8f3f]", dot: "bg-success" },
  failed: { label: "ล้มเหลว", cls: "bg-danger/10 text-danger", dot: "bg-danger" },
};

export function StatusBadge({ status }: { status: TaskStatus }) {
  const s = STYLE[status];
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] font-medium ${s.cls}`}>
      <span className={`h-1.5 w-1.5 rounded-full ${s.dot}`} />
      {s.label}
    </span>
  );
}
