"use client";

import { useReports } from "@/hooks/useReports";
import { DepartmentResolutionChart } from "@/components/Charts";
import type { Report, ReportStatus } from "@/types/api";

const STATUS_OPTIONS: ReportStatus[] = ["Pending", "In Progress", "Resolved", "Rejected"];

function priorityColor(p: number): string {
  return p > 70 ? "#FF5A66" : p > 40 ? "#F5A623" : "#22D3B8";
}

function buildRecommendations(reports: Report[]): string[] {
  if (reports.length === 0) return ["No reports yet — recommendations will appear once citizens start reporting issues."];
  const sorted = [...reports].sort((a, b) => b.priority - a.priority);
  const top = sorted[0];
  const recs: string[] = [];
  if (top) {
    recs.push(
      `Prioritize <b>${top.category}</b> in the field — highest composite priority score (${top.priority}).`
    );
  }
  const byCategory = new Map<string, number>();
  reports.forEach((r) => byCategory.set(r.category, (byCategory.get(r.category) ?? 0) + 1));
  const topEntry = [...byCategory.entries()].sort((a, b) => b[1] - a[1])[0];
  if (topEntry) {
    const [topCategory, topCount] = topEntry;
    recs.push(`${topCategory} accounts for ${topCount} of ${reports.length} open reports — consider a targeted response shift.`);
  }
  const pendingHighPriority = reports.filter((r) => r.status === "Pending" && r.priority > 70).length;
  if (pendingHighPriority > 0) {
    recs.push(`${pendingHighPriority} high-priority (P70+) reports are still pending — recommend expedited dispatch.`);
  }
  return recs;
}

export function AuthorityView() {
  const { reports, changeStatus } = useReports();
  const sorted = [...reports].sort((a, b) => b.priority - a.priority);
  const resolvedPct = reports.length ? Math.round((reports.filter((r) => r.status === "Resolved").length / reports.length) * 100) : 0;

  return (
    <section className="animate-fadeIn">
      <div className="section-title">
        Operations Overview <div className="line" />
      </div>
      <div className="mb-5 flex flex-wrap gap-4">
        <StatCard value={reports.length} label="Total Complaints" />
        <StatCard value={reports.filter((r) => r.status === "Pending").length} label="Pending Review" />
        <StatCard value={reports.filter((r) => r.priority > 70).length} label="High Priority (P70+)" />
        <StatCard value={`${resolvedPct}%`} label="Resolved" />
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <div className="panel">
          <h3 className="mb-3 font-display text-[14.5px] font-semibold">📋 Complaint Priority Ranking</h3>
          <div className="max-h-[420px] overflow-y-auto">
            <table>
              <thead>
                <tr>
                  <th>Issue</th>
                  <th>Priority</th>
                  <th>Dept</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {sorted.length === 0 ? (
                  <tr>
                    <td colSpan={4} className="py-6 text-center text-muted">
                      No reports yet.
                    </td>
                  </tr>
                ) : (
                  sorted.map((r) => (
                    <tr key={r.id}>
                      <td>{r.category}</td>
                      <td>
                        <b style={{ color: priorityColor(r.priority) }}>{r.priority}</b>
                      </td>
                      <td>{r.department}</td>
                      <td>
                        <select
                          value={r.status}
                          onChange={(e) => changeStatus(r.id, e.target.value as ReportStatus)}
                          className="rounded-[7px] border border-border bg-panel2 px-2 py-1.5 text-xs text-text"
                        >
                          {STATUS_OPTIONS.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
        <div>
          <div className="panel mb-4">
            <h3 className="mb-3 font-display text-[14.5px] font-semibold">🤖 AI Recommendations for Authorities</h3>
            {buildRecommendations(reports).map((text, i) => (
              <div key={i} className="flex gap-2.5 border-b border-border py-3 text-[13px] last:border-none">
                <div className="flex h-5.5 w-5.5 flex-shrink-0 items-center justify-center rounded-[6px] bg-panel2 font-mono text-[11px] text-pulse">
                  {i + 1}
                </div>
                <div dangerouslySetInnerHTML={{ __html: text }} />
              </div>
            ))}
          </div>
          <div className="panel">
            <h3 className="mb-3 font-display text-[14.5px] font-semibold">📈 Resolution Rate by Department</h3>
            <DepartmentResolutionChart reports={reports} />
          </div>
        </div>
      </div>
    </section>
  );
}

function StatCard({ value, label }: { value: number | string; label: string }) {
  return (
    <div className="min-w-[150px] flex-1 rounded-xl border border-border bg-panel p-4">
      <b className="block font-display text-2xl">{value}</b>
      <span className="text-xs text-muted">{label}</span>
    </div>
  );
}
