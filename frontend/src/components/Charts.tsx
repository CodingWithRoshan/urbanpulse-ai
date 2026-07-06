"use client";

import {
  ArcElement,
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  Filler,
  Legend,
  LineElement,
  LinearScale,
  PointElement,
  Tooltip,
} from "chart.js";
import { Bar, Doughnut, Line } from "react-chartjs-2";
import { useTheme } from "@/lib/ThemeContext";
import type { Report } from "@/types/api";

ChartJS.register(
  BarElement,
  LineElement,
  PointElement,
  ArcElement,
  CategoryScale,
  LinearScale,
  Filler,
  Legend,
  Tooltip
);

const CATEGORIES = ["Pothole", "Garbage Overflow", "Waterlogging", "Broken Streetlight"];

function useChartColors() {
  const { theme } = useTheme();
  const dark = theme === "dark";
  return { grid: dark ? "#22304a" : "#E1E6EE", text: dark ? "#8496AD" : "#5A6579" };
}

// Fixed height container prevents unbounded chart growth
const CHART_HEIGHT_CLASS = "relative h-[240px] w-full sm:h-[260px]";
const DOUGHNUT_HEIGHT_CLASS = "relative mx-auto h-[220px] w-full max-w-[260px] sm:h-[240px] sm:max-w-[280px]";

export function CategoryChart({ reports }: { reports: Report[] }) {
  const cc = useChartColors();
  const counts = CATEGORIES.map((c) => reports.filter((r) => r.category === c).length);

  return (
    <div className={CHART_HEIGHT_CLASS}>
      <Bar
        data={{
          labels: CATEGORIES,
          datasets: [
            {
              label: "Reports",
              data: counts,
              backgroundColor: ["#22D3B8", "#F5A623", "#5B9DF9", "#FF5A66"],
              borderRadius: 6,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: cc.text, font: { size: 11 } } },
            y: { grid: { color: cc.grid }, ticks: { color: cc.text }, beginAtZero: true },
          },
        }}
      />
    </div>
  );
}

export function HealthTrendChart({ history }: { history: number[] }) {
  const cc = useChartColors();
  const labels = history.length
    ? history.map((_, i) => (i === history.length - 1 ? "Now" : `T-${history.length - 1 - i}`))
    : ["Now"];
  const data = history.length ? history : [0];

  return (
    <div className={CHART_HEIGHT_CLASS}>
      <Line
        data={{
          labels,
          datasets: [
            {
              label: "Health Score",
              data,
              borderColor: "#22D3B8",
              backgroundColor: "rgba(34,211,184,.12)",
              fill: true,
              tension: 0.4,
              pointRadius: 3,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { grid: { display: false }, ticks: { color: cc.text } },
            y: { grid: { color: cc.grid }, ticks: { color: cc.text }, min: 0, max: 100 },
          },
        }}
      />
    </div>
  );
}

export function DepartmentResolutionChart({ reports }: { reports: Report[] }) {
  const cc = useChartColors();
  const departments = Array.from(new Set(reports.map((r) => r.department)));
  const resolutionRate = departments.map((dept) => {
    const deptReports = reports.filter((r) => r.department === dept);
    if (deptReports.length === 0) return 0;
    const resolved = deptReports.filter((r) => r.status === "Resolved").length;
    return Math.round((resolved / deptReports.length) * 100);
  });

  return (
    <div className={DOUGHNUT_HEIGHT_CLASS}>
      <Doughnut
        data={{
          labels: departments.length ? departments : ["No data yet"],
          datasets: [
            {
              data: resolutionRate.length ? resolutionRate : [1],
              backgroundColor: ["#22D3B8", "#F5A623", "#5B9DF9", "#FF5A66", "#8496AD"],
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          cutout: "62%",
          plugins: {
            legend: { position: "bottom", labels: { color: cc.text, boxWidth: 10, font: { size: 10.5 } } },
          },
        }}
      />
    </div>
  );
}
