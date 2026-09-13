"use client";

import { useRouter } from "next/navigation";
import { useState, type KeyboardEvent } from "react";
import { api, type OutputFormat } from "@/lib/api";

const EXAMPLES = ["ครีมกันแดด SPF50+", "กาแฟดริป", "เซรั่มวิตามินซี", "หูฟังไร้สาย"];

export function ResearchForm() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [competitors, setCompetitors] = useState<string[]>([]);
  const [chip, setChip] = useState("");
  const [ourBrand, setOurBrand] = useState("");
  const [category, setCategory] = useState("");
  const [formats, setFormats] = useState<OutputFormat[]>(["md", "pdf"]);
  const [advanced, setAdvanced] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addChip() {
    const v = chip.trim().replace(/,$/, "");
    if (v && !competitors.includes(v)) setCompetitors([...competitors, v]);
    setChip("");
  }
  function onChipKey(e: KeyboardEvent<HTMLInputElement>) {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addChip();
    } else if (e.key === "Backspace" && !chip && competitors.length) {
      setCompetitors(competitors.slice(0, -1));
    }
  }
  function toggleFormat(f: OutputFormat) {
    setFormats((cur) => (cur.includes(f) ? cur.filter((x) => x !== f) : [...cur, f]));
  }

  async function submit() {
    if (query.trim().length < 2 || busy) return;
    setBusy(true);
    setError(null);
    try {
      const { task_id } = await api.create({
        query: query.trim(),
        target_competitors: competitors,
        our_brand: ourBrand || null,
        product_category: category || null,
        language: "th",
        output_formats: formats.length ? formats : ["md"],
      });
      router.push(`/research/${task_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "ส่งคำขอไม่สำเร็จ");
      setBusy(false);
    }
  }

  return (
    <div className="card fade-up fade-up-1 mx-auto max-w-3xl p-3 sm:p-4" style={{ boxShadow: "var(--shadow-float)" }}>
      <div className="ai-glow flex items-center gap-3 rounded-2xl bg-canvas px-4 py-2 transition focus-within:bg-surface">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="shrink-0 text-ink-3">
          <circle cx="8.5" cy="8.5" r="5.5" stroke="currentColor" strokeWidth="1.8" />
          <path d="M13 13l4 4" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        </svg>
        <input
          autoFocus
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="คีย์เวิร์ด, URL, SKU หรือชื่อคู่แข่ง…"
          className="w-full bg-transparent py-2.5 text-[17px] outline-none placeholder:text-ink-3"
        />
        <button onClick={submit} disabled={busy || query.trim().length < 2} className="btn-primary shrink-0 px-4 py-2">
          {busy ? (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
          ) : (
            "เริ่มวิจัย"
          )}
        </button>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2 px-1">
        <span className="text-[12px] text-ink-3">ลอง:</span>
        {EXAMPLES.map((ex) => (
          <button
            key={ex}
            onClick={() => setQuery(ex)}
            className="rounded-full border border-line-2 bg-surface px-3 py-1 text-[12px] text-ink-2 transition hover:border-line hover:text-ink"
          >
            {ex}
          </button>
        ))}
        <button onClick={() => setAdvanced(!advanced)} className="btn-link ml-auto text-[13px]">
          {advanced ? "ซ่อนตัวเลือก" : "ตัวเลือกเพิ่มเติม"}
          <svg width="12" height="12" viewBox="0 0 12 12" className={`transition ${advanced ? "rotate-180" : ""}`}>
            <path d="M2 4l4 4 4-4" stroke="currentColor" strokeWidth="1.5" fill="none" strokeLinecap="round" />
          </svg>
        </button>
      </div>

      {advanced && (
        <div className="fade-up mt-4 grid gap-4 border-t border-line-2 px-1 pt-4 sm:grid-cols-2">
          <div className="sm:col-span-2">
            <label className="label">คู่แข่งเป้าหมาย</label>
            <div className="field flex flex-wrap items-center gap-1.5 py-2" onClick={(e) => (e.currentTarget.querySelector("input") as HTMLInputElement)?.focus()}>
              {competitors.map((c) => (
                <span key={c} className="inline-flex items-center gap-1 rounded-full bg-ink px-2.5 py-1 text-[13px] text-white">
                  {c}
                  <button onClick={() => setCompetitors(competitors.filter((x) => x !== c))} className="text-white/60 hover:text-white">×</button>
                </span>
              ))}
              <input
                value={chip}
                onChange={(e) => setChip(e.target.value)}
                onKeyDown={onChipKey}
                onBlur={addChip}
                aria-label="เพิ่มคู่แข่ง"
                placeholder={competitors.length ? "" : "พิมพ์ชื่อแบรนด์แล้วกด Enter เช่น Anessa, Biore"}
                className="min-w-[160px] flex-1 bg-transparent py-1 text-[15px] outline-none placeholder:text-ink-3"
              />
            </div>
          </div>
          <div>
            <label className="label">แบรนด์ของเรา</label>
            <input value={ourBrand} onChange={(e) => setOurBrand(e.target.value)} placeholder="เพื่อทำ SWOT และ benchmark" className="field" />
          </div>
          <div>
            <label className="label">หมวดสินค้า (ถ้ามี)</label>
            <input value={category} onChange={(e) => setCategory(e.target.value)} placeholder="เช่น สกินแคร์" className="field" />
          </div>
          <div className="sm:col-span-2">
            <label className="label">รูปแบบรายงาน</label>
            <div className="flex gap-2">
              {(["md", "pdf"] as OutputFormat[]).map((f) => (
                <button
                  key={f}
                  onClick={() => toggleFormat(f)}
                  className={`rounded-full px-4 py-1.5 text-[13px] font-medium transition ${
                    formats.includes(f) ? "bg-ink text-white" : "border border-line text-ink-2 hover:text-ink"
                  }`}
                >
                  {f === "md" ? "Markdown" : "PDF"}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {error && <p className="mt-3 px-1 text-[13px] text-danger">{error}</p>}
    </div>
  );
}
