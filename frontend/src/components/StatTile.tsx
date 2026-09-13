export function StatTile({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="card p-5">
      <p className="text-[12px] font-medium text-ink-3">{label}</p>
      <p className="mt-1 text-[28px] font-semibold tracking-tight">{value}</p>
      {sub && <p className="mt-0.5 text-[12px] text-ink-3">{sub}</p>}
    </div>
  );
}
