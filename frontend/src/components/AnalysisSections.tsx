import { api, type Analysis, type CompetitorAssessment, type ImageAsset, type Product } from "@/lib/api";
import { thb } from "@/lib/format";

const POS: Record<CompetitorAssessment["price_position"], string> = {
  budget: "ประหยัด", "mid-range": "กลาง", premium: "พรีเมียม", unknown: "—",
};
const SENT: Record<CompetitorAssessment["sentiment"], { label: string; cls: string }> = {
  positive: { label: "บวก", cls: "bg-success/10 text-[#1f8f3f]" },
  neutral: { label: "กลาง", cls: "bg-canvas text-ink-2" },
  negative: { label: "ลบ", cls: "bg-danger/10 text-danger" },
  mixed: { label: "ผสม", cls: "bg-warn/10 text-[#b26a00]" },
  unknown: { label: "—", cls: "bg-canvas text-ink-3" },
};

export function Section({ title, children, eyebrow }: { title: string; eyebrow?: string; children: React.ReactNode }) {
  return (
    <section className="fade-up">
      {eyebrow && <p className="eyebrow mb-1">{eyebrow}</p>}
      <h2 className="mb-4 text-[24px] font-semibold tracking-tight">{title}</h2>
      {children}
    </section>
  );
}

export function Prose({ text }: { text: string }) {
  return <p className="text-[16px] leading-[1.7] text-ink">{text}</p>;
}

export function Bullets({ items, numbered = false }: { items: string[]; numbered?: boolean }) {
  const Tag = numbered ? "ol" : "ul";
  return (
    <Tag className={`space-y-2 ${numbered ? "list-decimal" : "list-disc"} pl-5 text-[15px] leading-relaxed text-ink`}>
      {items.map((it, i) => <li key={i}>{it}</li>)}
    </Tag>
  );
}

export function CompetitorTable({ rows, highlight }: { rows: CompetitorAssessment[]; highlight: string[] }) {
  const hl = new Set(highlight.map((h) => h.toLowerCase()));
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[720px] text-[13px]">
        <thead>
          <tr className="border-b border-line-2 text-left text-[12px] text-ink-3">
            {["แบรนด์", "ตำแหน่งราคา", "ช่วงราคา", "จุดเด่น", "จุดด้อย", "ช่องทาง", "Sentiment"].map((h) => (
              <th key={h} className="px-4 py-3 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((c) => (
            <tr key={c.brand_name} className="border-b border-line-2 align-top last:border-0">
              <td className="px-4 py-3 font-semibold">
                {c.brand_name}
                {hl.has(c.brand_name.toLowerCase()) && <span className="ml-1.5 rounded-full bg-accent/10 px-1.5 py-0.5 text-[10px] text-accent">เป้าหมาย</span>}
              </td>
              <td className="px-4 py-3 text-ink-2">{POS[c.price_position]}</td>
              <td className="px-4 py-3 whitespace-nowrap">{c.price_range_thb || "—"}</td>
              <td className="px-4 py-3 text-ink-2"><ul className="list-disc pl-4">{c.strengths.map((s, i) => <li key={i}>{s}</li>)}</ul></td>
              <td className="px-4 py-3 text-ink-2"><ul className="list-disc pl-4">{c.weaknesses.map((s, i) => <li key={i}>{s}</li>)}</ul></td>
              <td className="px-4 py-3 text-ink-2">{c.channels.join(", ") || "—"}</td>
              <td className="px-4 py-3"><span className={`rounded-full px-2 py-0.5 text-[11px] font-medium ${SENT[c.sentiment].cls}`}>{SENT[c.sentiment].label}</span></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function SwotGrid({ swot }: { swot: Analysis["swot"] }) {
  const cells = [
    { k: "Strengths", th: "จุดแข็ง", items: swot.strengths, cls: "bg-success/[0.06]" },
    { k: "Weaknesses", th: "จุดอ่อน", items: swot.weaknesses, cls: "bg-danger/[0.05]" },
    { k: "Opportunities", th: "โอกาส", items: swot.opportunities, cls: "bg-accent/[0.05]" },
    { k: "Threats", th: "อุปสรรค", items: swot.threats, cls: "bg-warn/[0.07]" },
  ];
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {cells.map((c) => (
        <div key={c.k} className={`card p-5 ${c.cls}`}>
          <p className="text-[12px] font-semibold uppercase tracking-wider text-ink-3">{c.k}</p>
          <p className="mb-2 text-[17px] font-semibold">{c.th}</p>
          <Bullets items={c.items} />
        </div>
      ))}
    </div>
  );
}

export function ProductTable({ products }: { products: Product[] }) {
  const rows = [...products].sort((a, b) => (a.price.amount ?? Infinity) - (b.price.amount ?? Infinity));
  return (
    <div className="card overflow-x-auto">
      <table className="w-full min-w-[820px] text-[13px]">
        <thead>
          <tr className="border-b border-line-2 text-left text-[12px] text-ink-3">
            {["สินค้า", "แบรนด์", "Variant", "ราคา", "ราคาเดิม", "ส่วนลด", "ช่องทาง", "แหล่ง"].map((h) => (
              <th key={h} className="px-4 py-3 font-medium">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((p, i) => (
            <tr key={i} className="border-b border-line-2 last:border-0 hover:bg-canvas/60">
              <td className="max-w-[320px] truncate px-4 py-2.5 font-medium" title={p.product_name}>{p.product_name}</td>
              <td className="px-4 py-2.5 text-ink-2">{p.brand_name ?? "—"}</td>
              <td className="max-w-[140px] truncate px-4 py-2.5 text-ink-2">{p.variant ?? "—"}</td>
              <td className="px-4 py-2.5 whitespace-nowrap font-semibold">{thb(p.price.amount, p.price.currency)}</td>
              <td className="px-4 py-2.5 whitespace-nowrap text-ink-3 line-through">{p.price.original_price ? thb(p.price.original_price, p.price.currency) : ""}</td>
              <td className="px-4 py-2.5 text-ink-2">{p.price.discount_percentage ? `${p.price.discount_percentage}%` : "—"}</td>
              <td className="px-4 py-2.5 text-ink-2">{p.sales_channels.map((c) => c.channel_name).join(", ") || "—"}</td>
              <td className="px-4 py-2.5"><a href={p.data_source_url} target="_blank" rel="noreferrer" className="btn-link text-[12px]">เปิด ↗</a></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export function ImageGallery({ taskId, images }: { taskId: string; images: ImageAsset[] }) {
  if (!images.length) return null;
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
      {images.map((im) => (
        <a
          key={im.image_id}
          href={im.image_url}
          target="_blank"
          rel="noreferrer"
          className="card group overflow-hidden transition hover:-translate-y-0.5 hover:shadow-[var(--shadow-float)]"
        >
          <div className="aspect-square bg-canvas p-3">
            {/* eslint-disable-next-line @next/next/no-img-element -- served by our own API, not optimisable */}
            <img
              src={api.assetUrl(taskId, im.local_file_path)}
              alt={im.alt_text}
              className="h-full w-full object-contain transition group-hover:scale-[1.03]"
              loading="lazy"
            />
          </div>
          <div className="px-3 py-2.5">
            <p className="text-[12px] font-semibold">{im.brand_name ?? "—"}</p>
            <p className="line-clamp-2 text-[12px] leading-snug text-ink-2">{im.product_name}</p>
          </div>
        </a>
      ))}
    </div>
  );
}
