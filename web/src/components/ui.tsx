import type { ReactNode } from "react";

const SEVERITY_STYLE: Record<string, string> = {
  NORMAL: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  CAUTION: "bg-amber-50 text-amber-700 ring-amber-200",
  WARNING: "bg-amber-100 text-amber-800 ring-amber-300",
  CRITICAL: "bg-red-50 text-red-700 ring-red-200",
};

export function SeverityPill({ severity }: { severity: string }) {
  const style = SEVERITY_STYLE[severity] ?? "bg-slate-100 text-slate-600 ring-slate-200";
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${style}`}>{severity}</span>;
}

export function Pill({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "blue" | "red" | "green" }) {
  const styles: Record<string, string> = {
    neutral: "bg-slate-100 text-slate-600 ring-slate-200",
    blue: "bg-signal-50 text-signal-700 ring-signal-100",
    red: "bg-red-50 text-red-700 ring-red-200",
    green: "bg-emerald-50 text-emerald-700 ring-emerald-200",
  };
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${styles[tone]}`}>{children}</span>;
}

export function SectionHeading({ children, action }: { children: ReactNode; action?: ReactNode }) {
  return (
    <div className="mb-3 flex items-center justify-between">
      <h2 className="text-base font-bold text-slate-900">{children}</h2>
      {action}
    </div>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`rounded-xl border border-slate-200 bg-white p-5 shadow-panel ${className}`}>{children}</section>;
}

export function MetricCard({ label, value, sub }: { label: string; value: ReactNode; sub?: string }) {
  return (
    <div className="rounded-xl border border-slate-200 bg-white p-4">
      <div className="text-xs font-semibold text-slate-500">{label}</div>
      <div className="tabular mt-1 text-3xl font-extrabold text-slate-900">{value}</div>
      {sub ? <div className="mt-0.5 text-xs text-slate-400">{sub}</div> : null}
    </div>
  );
}
