import type { TaskStatus } from "@/lib/api";
import { parseEvent } from "@/lib/format";

const STAGES = [
  { key: "plan", label: "วางแผน", hint: "จัดประเภทอินพุตและสร้างคำค้นหา" },
  { key: "search", label: "ค้นหา", hint: "ค้นหาแหล่งข้อมูลจากเว็บ" },
  { key: "scrape", label: "ดึงข้อมูล", hint: "โหลดหน้าเว็บและแยกเนื้อหา" },
  { key: "extract", label: "สกัดข้อมูล", hint: "LLM แปลงหน้าเว็บเป็นข้อมูลสินค้า/ราคา" },
  { key: "analyze", label: "วิเคราะห์", hint: "เปรียบเทียบคู่แข่ง SWOT และกลยุทธ์ราคา" },
  { key: "write", label: "เขียนรายงาน", hint: "สร้าง Markdown และ PDF" },
];

export function ProgressSteps({ events, status }: { events: string[]; status: TaskStatus }) {
  const parsed = events.map(parseEvent);
  const done = new Set(parsed.map((e) => e.stage));
  const lastStage = parsed.at(-1)?.stage;
  const activeIdx = status === "running" ? STAGES.findIndex((s) => s.key === lastStage) + 1 : -1;
  const refining = lastStage === "refine";

  return (
    <div className="card p-6">
      <ol className="grid gap-4 sm:grid-cols-6">
        {STAGES.map((s, i) => {
          const isDone = done.has(s.key) && (status !== "running" || i < activeIdx);
          const isActive = status === "running" && (i === activeIdx || (refining && s.key === "search"));
          const raw = parsed.filter((e) => e.stage === s.key).at(-1)?.message;
          const msg = s.key === "write" && raw ? `รายงานพร้อมแล้ว (${raw.split(", ").map((x) => x.split("=")[0].toUpperCase()).join(", ")})` : raw;
          return (
            <li key={s.key} className="flex min-w-0 gap-3 sm:flex-col sm:gap-2">
              <div className="flex items-center gap-2 sm:w-full">
                <span
                  className={`grid h-7 w-7 shrink-0 place-items-center rounded-full text-[12px] font-semibold transition ${
                    isDone ? "bg-ink text-white" : isActive ? "ai-dot text-white shadow-[0_0_0_4px_rgba(110,92,255,.15)]" : "bg-canvas text-ink-3"
                  }`}
                >
                  {isDone ? (
                    <svg width="12" height="12" viewBox="0 0 12 12"><path d="M2.5 6.5l2.5 2.5 4.5-5" stroke="currentColor" strokeWidth="1.8" fill="none" strokeLinecap="round" strokeLinejoin="round" /></svg>
                  ) : isActive ? (
                    <span className="h-2 w-2 rounded-full bg-white pulse-dot" />
                  ) : (
                    i + 1
                  )}
                </span>
                <span className="hidden h-px flex-1 bg-line-2 sm:block" />
              </div>
              <div className="min-w-0">
                <p className={`text-[14px] font-medium ${isDone || isActive ? "text-ink" : "text-ink-3"}`}>{s.label}</p>
                <p className="mt-0.5 break-words text-[12px] leading-snug text-ink-3">{msg ?? s.hint}</p>
              </div>
            </li>
          );
        })}
      </ol>
      {status === "running" && <div className="ai-thinking mt-5" aria-hidden />}
      {refining && status === "running" && (
        <p className="mt-4 rounded-xl bg-accent/5 px-4 py-2 text-[13px] text-accent">
          ข้อมูลยังน้อย — เอเจนต์กำลังขยายคำค้นหาและวนรอบใหม่
        </p>
      )}
    </div>
  );
}
