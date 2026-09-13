"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { api, type TaskSummary } from "@/lib/api";
import { relativeTime } from "@/lib/format";
import { StatusBadge } from "./StatusBadge";

export function TaskList() {
  const [tasks, setTasks] = useState<TaskSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let alive = true;
    const load = () =>
      api
        .list(24)
        .then((t) => alive && (setTasks(t), setError(null)))
        .catch((e) => alive && setError(e.message));
    load();
    const id = setInterval(load, 5000);
    return () => {
      alive = false;
      clearInterval(id);
    };
  }, []);

  if (error)
    return (
      <p className="card p-6 text-[14px] text-ink-2">
        เชื่อมต่อ API ไม่ได้ ({error}) — ตรวจสอบว่า backend รันอยู่ที่ <code>localhost:8010</code>
      </p>
    );
  if (tasks === null)
    return (
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <div key={i} className="card h-32 animate-pulse" />
        ))}
      </div>
    );
  if (!tasks.length) return <p className="py-10 text-center text-[14px] text-ink-3">ยังไม่มีงานวิจัย — เริ่มงานแรกได้จากด้านบน</p>;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {tasks.map((t, i) => (
        <Link
          key={t.task_id}
          href={`/research/${t.task_id}`}
          className={`card fade-up group flex flex-col gap-3 p-5 transition hover:-translate-y-0.5 hover:shadow-[var(--shadow-float)]`}
          style={{ animationDelay: `${Math.min(i, 8) * 40}ms` }}
        >
          <div className="flex items-start justify-between gap-3">
            <h3 className="line-clamp-2 text-[17px] font-semibold leading-snug tracking-tight">{t.query}</h3>
            <StatusBadge status={t.status} />
          </div>
          {t.target_competitors.length > 0 && (
            <p className="line-clamp-1 text-[13px] text-ink-2">vs {t.target_competitors.join(", ")}</p>
          )}
          <div className="mt-auto flex items-center justify-between text-[12px] text-ink-3">
            <span>{relativeTime(t.created_at)}</span>
            {t.products > 0 && <span>{t.products} สินค้า</span>}
          </div>
        </Link>
      ))}
    </div>
  );
}
