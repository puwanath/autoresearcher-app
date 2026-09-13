"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { api, type TaskView } from "@/lib/api";
import { duration, parseEvent, thb } from "@/lib/format";
import { Bullets, CompetitorTable, ImageGallery, ProductTable, Prose, Section, SwotGrid } from "./AnalysisSections";
import { PriceChart } from "./PriceChart";
import { ProgressSteps } from "./ProgressSteps";
import { StatTile } from "./StatTile";
import { StatusBadge } from "./StatusBadge";

const CONF = { low: "ต่ำ", medium: "ปานกลาง", high: "สูง" };

export function ResearchDetail({ id }: { id: string }) {
  const [task, setTask] = useState<TaskView | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showProducts, setShowProducts] = useState(false);
  const [showLog, setShowLog] = useState(false);
  const [retrying, setRetrying] = useState(false);
  const router = useRouter();

  async function retry() {
    if (retrying) return;
    setRetrying(true);
    try {
      const { task_id } = await api.retry(id);
      router.push(`/research/${task_id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "ส่งคำขอไม่สำเร็จ");
      setRetrying(false);
    }
  }

  useEffect(() => {
    let alive = true;
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      try {
        const t = await api.get(id);
        if (!alive) return;
        setTask(t);
        setError(null);
        if (t.status === "pending" || t.status === "running") timer = setTimeout(poll, 2500);
      } catch (e) {
        if (alive) {
          setError(e instanceof Error ? e.message : "โหลดไม่สำเร็จ");
          timer = setTimeout(poll, 5000);
        }
      }
    };
    poll();
    return () => {
      alive = false;
      clearTimeout(timer);
    };
  }, [id]);

  if (error && !task)
    return <p className="card mt-16 p-8 text-center text-ink-2">{error}</p>;
  if (!task)
    return (
      <div className="mt-16 space-y-4">
        <div className="card shimmer h-24" />
        <div className="card shimmer h-40" />
      </div>
    );

  const a = task.analysis;
  const s = task.price_stats;
  const running = task.status === "pending" || task.status === "running";
  const targets = task.request.target_competitors;

  return (
    <div className="space-y-10 pt-10">
      {/* header */}
      <div className="fade-up">
        <Link href="/" className="btn-link mb-4 text-[13px]">← กลับ</Link>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="eyebrow">{task.plan?.product_category ?? "งานวิจัย"}</p>
            <h1 className="mt-1 text-[34px] font-semibold leading-tight tracking-[-0.02em] sm:text-[40px]">
              {a?.title ?? task.request.query}
            </h1>
            <p className="mt-2 text-[14px] text-ink-2">
              {task.request.query}
              {targets.length > 0 && <> · เทียบกับ <span className="text-ink">{targets.join(", ")}</span></>}
              {task.request.our_brand && <> · แบรนด์ของเรา <span className="text-ink">{task.request.our_brand}</span></>}
            </p>
          </div>
          <div className="flex items-center gap-2">
            <StatusBadge status={task.status} />
            {task.status === "failed" && (
              <button onClick={retry} disabled={retrying} className="btn-primary">
                {retrying ? <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" /> : "ลองใหม่"}
              </button>
            )}
            {task.status === "completed" && (
              <button onClick={retry} disabled={retrying} className="btn-secondary" title="รันงานวิจัยนี้อีกครั้งด้วยข้อมูลล่าสุด">
                {retrying ? "กำลังส่ง…" : "รันอีกครั้ง"}
              </button>
            )}
            {task.artifacts.pdf && (
              <a href={api.reportUrl(id, "pdf")} className="btn-primary">ดาวน์โหลด PDF</a>
            )}
            {task.artifacts.md && (
              <a href={api.reportUrl(id, "md")} className="btn-secondary">Markdown</a>
            )}
          </div>
        </div>
      </div>

      <ProgressSteps events={task.events} status={task.status} />

      {task.status === "failed" && (
        <div className="card border border-danger/20 p-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <p className="font-semibold text-danger">งานล้มเหลว</p>
              <p className="mt-1 text-[13px] text-ink-2">
                ข้อมูลที่เก็บมาแล้วยังอยู่ในระบบ กด "ลองใหม่" เพื่อรันงานวิจัยนี้อีกครั้งเป็นงานใหม่
              </p>
            </div>
            <button onClick={retry} disabled={retrying} className="btn-primary">
              {retrying ? "กำลังส่ง…" : "ลองใหม่"}
            </button>
          </div>
          <pre className="mt-4 whitespace-pre-wrap rounded-xl bg-canvas p-4 text-[12px] text-ink-2">{task.error}</pre>
          {error && <p className="mt-2 text-[13px] text-danger">{error}</p>}
        </div>
      )}

      {running && (
        <p className="text-center text-[14px] text-ink-3">
          <span className="ai-text-animated font-medium">AI กำลังทำงาน</span> · โดยทั่วไปใช้เวลา 1–3 นาที หน้านี้จะอัปเดตอัตโนมัติ
        </p>
      )}

      {a && (
        <>
          {/* KPI tiles */}
          <div className="fade-up grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <StatTile label="ราคามัธยฐานตลาด" value={thb(s?.median)} sub={s?.sample_size ? `จาก ${s.sample_size} รายการที่มีราคา` : "ไม่พบราคา"} />
            <StatTile label="ช่วงราคา" value={s?.min != null ? `${thb(s.min)} – ${thb(s.max)}` : "—"} sub="ต่ำสุด – สูงสุด" />
            <StatTile label="ช่วงราคาที่แนะนำ" value={a.recommended_price_range_thb || "—"} sub="AI แนะนำ · THB" accent />
            <StatTile label="ความเชื่อมั่น" value={CONF[a.confidence]} sub={`${task.products.length} สินค้า · ${task.events.length ? duration(task.created_at, task.finished_at) : ""}`} />
          </div>

          <Section eyebrow="Executive Summary" title="บทสรุปผู้บริหาร">
            <div className="card p-7">
              <Prose text={a.executive_summary} />
              <div className="mt-6 border-t border-line-2 pt-5">
                <p className="mb-3 text-[13px] font-semibold text-ink-2">Key Findings</p>
                <Bullets items={a.key_findings} />
              </div>
            </div>
          </Section>

          <Section eyebrow="Competitor Landscape" title="ภาพรวมคู่แข่ง">
            <div className="space-y-4">
              <div className="card p-7">
                <Prose text={a.market_overview} />
                <p className="mt-3 text-[13px] text-ink-3">ลักษณะการแข่งขัน: <span className="text-ink">{a.competition_type}</span></p>
              </div>
              <ImageGallery taskId={id} images={task.images} />
              <PriceChart products={task.products} highlight={targets} />
              <CompetitorTable rows={a.competitors} highlight={targets} />
            </div>
          </Section>

          <Section eyebrow="Price & Promotion" title="วิเคราะห์ราคาและโปรโมชั่น">
            <div className="card p-7">
              <Prose text={a.pricing_insight} />
            </div>
          </Section>

          <Section eyebrow="Sales Channel" title="ช่องทางการขาย">
            <div className="card p-7">
              <Prose text={a.channel_insight} />
              <div className="mt-4 flex flex-wrap gap-2">
                {a.recommended_channels.map((c) => (
                  <span key={c} className="rounded-full bg-ink px-3 py-1 text-[13px] font-medium text-white">{c}</span>
                ))}
              </div>
              <p className="mt-5 border-t border-line-2 pt-4 text-[14px] leading-relaxed text-ink-2">
                <span className="font-semibold text-ink">ความรู้สึกของลูกค้า: </span>{a.sentiment_summary}
              </p>
            </div>
          </Section>

          <Section eyebrow="Strategy" title="ข้อเสนอแนะเชิงกลยุทธ์">
            <div className="space-y-4">
              <SwotGrid swot={a.swot} />
              <div className="grid gap-4 lg:grid-cols-2">
                <div className="card p-7">
                  <p className="mb-3 text-[17px] font-semibold">ข้อเสนอแนะ</p>
                  <Bullets items={a.recommendations} numbered />
                </div>
                <div className="card p-7">
                  <p className="mb-3 text-[17px] font-semibold">Action Plan</p>
                  <ol className="space-y-2.5">
                    {a.action_plan.map((it, i) => (
                      <li key={i} className="flex gap-3 text-[15px] leading-relaxed">
                        <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full bg-canvas text-[12px] font-semibold text-ink-2">{i + 1}</span>
                        {it}
                      </li>
                    ))}
                  </ol>
                </div>
              </div>
              {a.data_gaps.length > 0 && (
                <div className="card bg-warn/[0.06] p-6">
                  <p className="mb-2 text-[14px] font-semibold">ข้อจำกัดของข้อมูล</p>
                  <Bullets items={a.data_gaps} />
                </div>
              )}
            </div>
          </Section>

          <Section eyebrow="Data" title={`สินค้าที่พบ (${task.products.length})`}>
            {showProducts ? (
              <ProductTable products={task.products} />
            ) : (
              <button onClick={() => setShowProducts(true)} className="btn-secondary">แสดงตารางสินค้าทั้งหมด</button>
            )}
          </Section>
        </>
      )}

      {/* log */}
      <div className="fade-up">
        <button onClick={() => setShowLog(!showLog)} className="btn-link text-[13px]">
          {showLog ? "ซ่อน" : "แสดง"}บันทึกการทำงาน ({task.events.length})
        </button>
        {showLog && (
          <div className="card mt-3 p-5 font-mono text-[12px] leading-relaxed text-ink-2">
            {task.events.map((e, i) => {
              const p = parseEvent(e);
              return (
                <div key={i} className="flex gap-3">
                  <span className="text-ink-3">{p.time}</span>
                  <span className="w-16 shrink-0 font-semibold text-ink">{p.stage}</span>
                  <span>{p.message}</span>
                </div>
              );
            })}
            {task.error && task.status === "completed" && (
              <details className="mt-3 text-ink-3">
                <summary className="cursor-pointer">คำเตือนระหว่างทำงาน</summary>
                <pre className="mt-1 whitespace-pre-wrap">{task.error}</pre>
              </details>
            )}
            {task.plan && (
              <details className="mt-3 text-ink-3">
                <summary className="cursor-pointer">แผนการวิจัย</summary>
                <pre className="mt-1 whitespace-pre-wrap">{JSON.stringify(task.plan, null, 2)}</pre>
              </details>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
