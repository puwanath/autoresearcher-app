export function StatTile({ label, value, sub, accent = false }: { label: string; value: string; sub?: string; accent?: boolean }) {
  return (
    <div className="card relative overflow-hidden p-5">
      {accent && <span className="absolute inset-x-0 top-0 h-[3px]" style={{ background: "var(--grad-ai)" }} />}
      <p className="text-[12px] font-medium text-ink-3">{label}</p>
      <p className={`mt-1 text-[28px] font-semibold tracking-tight ${accent ? "ai-text" : ""}`}>{value}</p>
      {sub && <p className="mt-0.5 text-[12px] text-ink-3">{sub}</p>}
    </div>
  );
}
