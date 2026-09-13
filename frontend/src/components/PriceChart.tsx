"use client";

import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { Product } from "@/lib/api";
import { thb } from "@/lib/format";

export function brandRows(products: Product[]) {
  const groups = new Map<string, number[]>();
  for (const p of products) {
    if (p.price.amount == null || p.price.currency !== "THB") continue;
    const b = p.brand_name?.trim() || "อื่นๆ";
    groups.set(b, [...(groups.get(b) ?? []), p.price.amount]);
  }
  return [...groups.entries()]
    .map(([brand, amounts]) => {
      const s = [...amounts].sort((a, b) => a - b);
      const median = s.length % 2 ? s[(s.length - 1) / 2] : (s[s.length / 2 - 1] + s[s.length / 2]) / 2;
      return { brand, median, min: s[0], max: s[s.length - 1], n: s.length };
    })
    .sort((a, b) => a.median - b.median);
}

export function PriceChart({ products, highlight }: { products: Product[]; highlight: string[] }) {
  const rows = brandRows(products).slice(0, 14);
  if (rows.length < 2) return null;
  const hl = new Set(highlight.map((h) => h.toLowerCase()));
  return (
    <div className="card p-6">
      <div className="mb-4 flex items-baseline justify-between">
        <h3 className="text-[17px] font-semibold tracking-tight">ราคามัธยฐานตามแบรนด์</h3>
        <span className="text-[12px] text-ink-3">THB · {rows.length} แบรนด์</span>
      </div>
      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={rows} margin={{ top: 4, right: 8, left: 8, bottom: 4 }}>
            <CartesianGrid vertical={false} stroke="#e8e8ed" />
            <XAxis dataKey="brand" tick={{ fontSize: 11, fill: "#86868b" }} axisLine={false} tickLine={false} interval={0} angle={-25} textAnchor="end" height={54} />
            <YAxis tick={{ fontSize: 11, fill: "#86868b" }} axisLine={false} tickLine={false} tickFormatter={(v) => `฿${v.toLocaleString()}`} width={64} />
            <Tooltip
              cursor={{ fill: "rgba(0,0,0,0.03)" }}
              contentStyle={{ borderRadius: 12, border: "1px solid #e8e8ed", boxShadow: "0 8px 24px rgba(0,0,0,.08)", fontSize: 13 }}
              formatter={(v, _n, item) => {
                const r = item.payload as (typeof rows)[number];
                return [`${thb(Number(v))} (ช่วง ${thb(r.min)}–${thb(r.max)}, ${r.n} รายการ)`, "มัธยฐาน"];
              }}
            />
            <Bar dataKey="median" radius={[6, 6, 0, 0]} isAnimationActive={false}>
              {rows.map((r) => {
                const target = hl.has(r.brand.toLowerCase());
                return <Cell key={r.brand} fill={target ? "#0071e3" : "#1d1d1f"} opacity={hl.size && !target ? 0.35 : 1} />;
              })}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      {hl.size > 0 && <p className="mt-2 text-[12px] text-ink-3">สีน้ำเงิน = คู่แข่งเป้าหมาย</p>}
    </div>
  );
}
