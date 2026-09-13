import type { ChannelAnalysis, FeatureComparison, PromotionAnalysis, UsageInsights } from "@/lib/api";
import { thb } from "@/lib/format";
import { Bullets, Prose } from "./AnalysisSections";

const FIT = { high: { label: "สูง", cls: "bg-success/10 text-[#1f8f3f]" }, medium: { label: "กลาง", cls: "bg-warn/10 text-[#b26a00]" }, low: { label: "ต่ำ", cls: "bg-canvas text-ink-3" } };

export function ChannelSection({ ca, targets }: { ca: ChannelAnalysis; targets: string[] }) {
  const channels = ca.matrix.length ? Object.keys(ca.matrix[0]).filter((k) => k !== "brand" && k !== "total") : [];
  const hl = new Set(targets.map((t) => t.toLowerCase()));
  const max = Math.max(1, ...ca.matrix.flatMap((r) => channels.map((c) => Number(r[c]) || 0)));
  return (
    <div className="space-y-4">
      <div className="card p-7">
        <Prose text={ca.summary} />
      </div>
      {channels.length > 0 && (
        <div className="card overflow-x-auto p-2">
          <p className="px-4 pt-3 text-[13px] font-semibold text-ink-2">Matrix แบรนด์ × ช่องทาง (จำนวนรายการที่พบ)</p>
          <table className="w-full min-w-[640px] text-[13px]">
            <thead>
              <tr className="text-left text-[12px] text-ink-3">
                <th className="px-4 py-3 font-medium">แบรนด์</th>
                {channels.map((c) => <th key={c} className="px-3 py-3 text-center font-medium">{c}</th>)}
                <th className="px-3 py-3 text-right font-medium">รวม</th>
              </tr>
            </thead>
            <tbody>
              {ca.matrix.map((r) => (
                <tr key={String(r.brand)} className="border-t border-line-2">
                  <td className="px-4 py-2 font-semibold">
                    {String(r.brand)}
                    {hl.has(String(r.brand).toLowerCase()) && <span className="ml-1.5 rounded-full bg-accent/10 px-1.5 py-0.5 text-[10px] text-accent">เป้าหมาย</span>}
                  </td>
                  {channels.map((c) => {
                    const n = Number(r[c]) || 0;
                    return (
                      <td key={c} className="px-3 py-2 text-center">
                        {n > 0 && (
                          <span className="inline-block min-w-7 rounded-md px-1.5 py-0.5 text-[12px] font-medium text-white" style={{ background: `rgba(10,132,255,${0.35 + (0.65 * n) / max})` }}>
                            {n}
                          </span>
                        )}
                      </td>
                    );
                  })}
                  <td className="px-3 py-2 text-right text-ink-2">{String(r.total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {ca.channels.map((c) => {
          const st = ca.stats.find((s) => s.channel_name === c.channel_name);
          return (
            <div key={c.channel_name} className="card flex flex-col gap-2 p-5">
              <div className="flex items-start justify-between gap-2">
                <p className="text-[17px] font-semibold">{c.channel_name}</p>
                <span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${FIT[c.fit_for_us].cls}`}>เหมาะกับเรา: {FIT[c.fit_for_us].label}</span>
              </div>
              {st && (
                <p className="text-[12px] text-ink-3">
                  {st.listing_count} รายการ · {st.brand_count} แบรนด์{st.price_median != null && <> · มัธยฐาน {thb(st.price_median)}</>}
                </p>
              )}
              <p className="text-[14px] text-ink">{c.role}</p>
              <div className="grid grid-cols-2 gap-3 text-[12px]">
                <div><p className="mb-1 font-semibold text-[#1f8f3f]">จุดแข็ง</p><ul className="list-disc pl-4 text-ink-2">{c.strengths.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
                <div><p className="mb-1 font-semibold text-[#b26a00]">ข้อควรระวัง</p><ul className="list-disc pl-4 text-ink-2">{c.watchouts.map((x, i) => <li key={i}>{x}</li>)}</ul></div>
              </div>
              <p className="mt-auto border-t border-line-2 pt-2 text-[13px]"><span className="font-semibold">แนะนำ:</span> {c.recommendation}</p>
            </div>
          );
        })}
      </div>
      <div className="card p-6">
        <p className="mb-3 text-[15px] font-semibold">ลำดับการเข้าช่องทางที่แนะนำ</p>
        <ol className="space-y-2">
          {ca.channel_mix_recommendation.map((it, i) => (
            <li key={i} className="flex gap-3 text-[15px] leading-relaxed">
              <span className="mt-0.5 grid h-6 w-6 shrink-0 place-items-center rounded-full text-[12px] font-semibold text-white" style={{ background: "var(--grad-ai)" }}>{i + 1}</span>
              {it}
            </li>
          ))}
        </ol>
      </div>
    </div>
  );
}

export function UsageSection({ u }: { u: UsageInsights }) {
  const cols = [
    { t: "การใช้งานหลัก", items: u.use_cases, cls: "bg-accent/[0.05]" },
    { t: "โอกาส / สถานการณ์ที่ใช้", items: u.usage_occasions, cls: "bg-canvas" },
    { t: "เหตุผลในการซื้อ", items: u.purchase_drivers, cls: "bg-success/[0.06]" },
    { t: "ปัญหา / ข้อกังวล", items: u.pain_points, cls: "bg-danger/[0.05]" },
  ];
  return (
    <div className="space-y-4">
      <div className="card p-7"><Prose text={u.summary} /></div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {cols.map((c) => (
          <div key={c.t} className={`card p-5 ${c.cls}`}>
            <p className="mb-2 text-[14px] font-semibold">{c.t}</p>
            {c.items.length ? <Bullets items={c.items} /> : <p className="text-[13px] text-ink-3">ไม่พบข้อมูล</p>}
          </div>
        ))}
      </div>
      <div className="card overflow-x-auto">
        <table className="w-full min-w-[640px] text-[13px]">
          <thead><tr className="border-b border-line-2 text-left text-[12px] text-ink-3">{["กลุ่มเป้าหมาย", "ความต้องการ", "แบรนด์ที่ตอบโจทย์", "โอกาสสำหรับเรา"].map((h) => <th key={h} className="px-4 py-3 font-medium">{h}</th>)}</tr></thead>
          <tbody>
            {u.target_segments.map((t) => (
              <tr key={t.segment} className="border-b border-line-2 align-top last:border-0">
                <td className="px-4 py-3 font-semibold">{t.segment}</td>
                <td className="px-4 py-3 text-ink-2">{t.needs.join("; ")}</td>
                <td className="px-4 py-3 text-ink-2">{t.brands_serving.join(", ") || "—"}</td>
                <td className="px-4 py-3">{t.opportunity || "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {u.evidence.length > 0 && (
        <div className="card p-6">
          <p className="mb-3 text-[13px] font-semibold text-ink-2">หลักฐานจากรีวิว</p>
          <div className="grid gap-2 sm:grid-cols-2">
            {u.evidence.map((e, i) => <blockquote key={i} className="rounded-xl bg-canvas px-4 py-3 text-[13px] leading-relaxed text-ink-2">“{e}”</blockquote>)}
          </div>
        </div>
      )}
    </div>
  );
}

export function PromoFeatureSection({ pa, fc }: { pa?: PromotionAnalysis | null; fc?: FeatureComparison | null }) {
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      {pa && (
        <div className="card p-7">
          <p className="mb-2 text-[17px] font-semibold">กลยุทธ์โปรโมชั่น</p>
          <p className="mb-4 text-[14px] leading-relaxed text-ink-2">{pa.summary}</p>
          {pa.promo_type_counts.length > 0 && (
            <div className="mb-4 flex flex-wrap gap-2">
              {pa.promo_type_counts.map((r) => (
                <span key={r.promo_type} className="rounded-full border border-line-2 px-3 py-1 text-[12px]" title={r.brands.join(", ")}>
                  {r.promo_type} <span className="text-ink-3">×{r.count}</span>
                </span>
              ))}
            </div>
          )}
          <Bullets items={pa.brand_tactics} />
          <p className="mt-4 border-t border-line-2 pt-3 text-[14px]"><span className="font-semibold">แนะนำ: </span>{pa.recommendations.join(" · ")}</p>
        </div>
      )}
      {fc && (
        <div className="card p-7">
          <p className="mb-2 text-[17px] font-semibold">เปรียบเทียบคุณสมบัติ</p>
          <p className="mb-4 text-[14px] leading-relaxed text-ink-2">{fc.summary}</p>
          <table className="w-full text-[13px]">
            <thead><tr className="text-left text-[12px] text-ink-3"><th className="py-2 font-medium">คุณสมบัติ</th><th className="py-2 font-medium">แบรนด์ที่มี</th><th className="py-2 text-center font-medium">พื้นฐาน</th></tr></thead>
            <tbody>
              {fc.features.map((f) => (
                <tr key={f.feature} className="border-t border-line-2 align-top">
                  <td className="py-2 pr-3 font-medium">{f.feature}</td>
                  <td className="py-2 pr-3 text-ink-2">{f.brands_offering.join(", ")}</td>
                  <td className="py-2 text-center">{f.is_table_stakes ? "✓" : ""}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <p className="mt-4 mb-2 text-[13px] font-semibold text-ink-2">โอกาสสร้างความแตกต่าง</p>
          <Bullets items={fc.differentiation_opportunities} />
        </div>
      )}
    </div>
  );
}
