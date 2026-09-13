import { ResearchForm } from "@/components/ResearchForm";
import { TaskList } from "@/components/TaskList";

export default function Home() {
  return (
    <>
      <section className="pt-20 pb-14 text-center sm:pt-28">
        <p className="eyebrow fade-up">AutoResearch Agent</p>
        <h1 className="fade-up mt-3 text-[40px] font-semibold leading-[1.05] tracking-[-0.02em] sm:text-[56px]">
          วิจัยคู่แข่ง<span className="text-ink-3">.</span> อัตโนมัติ<span className="text-ink-3">.</span>
        </h1>
        <p className="fade-up fade-up-1 mx-auto mt-5 max-w-xl text-[19px] leading-relaxed text-ink-2">
          พิมพ์สินค้าหรือคู่แข่ง แล้วปล่อยให้เอเจนต์ค้นหา ดึงราคา วิเคราะห์ตลาด
          และเขียนรายงานให้ในไม่กี่นาที
        </p>
        <div className="mt-10">
          <ResearchForm />
        </div>
      </section>

      <section id="history" className="scroll-mt-20 pt-6">
        <div className="mb-5 flex items-end justify-between">
          <h2 className="text-[24px] font-semibold tracking-tight">งานวิจัยล่าสุด</h2>
          <span className="text-[13px] text-ink-3">อัปเดตอัตโนมัติ</span>
        </div>
        <TaskList />
      </section>
    </>
  );
}
