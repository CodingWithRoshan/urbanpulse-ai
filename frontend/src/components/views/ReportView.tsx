"use client";

import { useRef, useState } from "react";
import { createReport } from "@/lib/apiClient";
import { useAuth } from "@/lib/AuthContext";
import { useReports } from "@/hooks/useReports";
import { useRuntimeConfig } from "@/lib/RuntimeConfigContext";
import type { Report } from "@/types/api";

function severityColor(s: number): string {
  return s > 70 ? "#FF5A66" : s > 40 ? "#F5A623" : "#22D3B8";
}
function statusColor(s: string): string {
  return s === "Resolved" ? "#22D3B8" : s === "In Progress" ? "#5B9DF9" : "#F5A623";
}

export function ReportView() {
  const { user } = useAuth();
  const { reports, refresh } = useReports();
  const { defaultLat, defaultLng } = useRuntimeConfig();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<Report | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  async function handleFile(file: File) {
    setPreviewUrl(URL.createObjectURL(file));
    setResult(null);
    setErrorMsg(null);
    setIsAnalyzing(true);
    try {
      const coords = await new Promise<{ lat: number; lng: number }>((resolve) => {
        if (!navigator.geolocation) return resolve({ lat: defaultLat, lng: defaultLng });
        navigator.geolocation.getCurrentPosition(
          (pos) => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
          () => resolve({ lat: defaultLat, lng: defaultLng }),
          { timeout: 4000 }
        );
      });
      const report = await createReport(file, coords.lat, coords.lng);
      setResult(report);
      refresh();
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "Classification failed. Please try again.");
    } finally {
      setIsAnalyzing(false);
    }
  }

  const myReports = reports.filter((r) => r.reported_by === user?.id);

  return (
    <section className="animate-fadeIn">
      <div className="section-title">
        Report a Civic Issue <div className="line" />
      </div>

      {!user ? (
        <div className="panel flex flex-col items-center gap-3 py-10 text-center">
          <p className="text-sm text-muted">Sign in with Google to submit and track civic issue reports.</p>
          <a href="/login" className="rounded-[10px] bg-pulse px-4 py-2 text-xs font-bold text-[#04140F]">
            Sign in
          </a>
        </div>
      ) : (
        <div className="panel">
          <div
            onClick={() => fileInputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setIsDragging(true);
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              setIsDragging(false);
            }}
            onDrop={(e) => {
              e.preventDefault();
              setIsDragging(false);
              const file = e.dataTransfer.files[0];
              if (file) handleFile(file);
            }}
            className={`cursor-pointer rounded-panel border-2 border-dashed p-10 text-center transition-colors ${
              isDragging ? "border-pulse bg-pulse/5" : "border-border"
            }`}
          >
            <div className="mb-2.5 text-[34px]">📷</div>
            <h4 className="mb-1.5 font-display text-base font-semibold">Drop a photo, or click to upload</h4>
            <p className="text-[13px] text-muted">
              Pothole · Garbage overflow · Waterlogging · Broken streetlight — Gemini Vision will classify it
              automatically
            </p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              className="hidden"
              onChange={(e) => {
                const file = e.target.files?.[0];
                if (file) handleFile(file);
              }}
            />
          </div>

          {previewUrl && (
            <div className="mt-4.5 flex flex-wrap items-start gap-4">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={previewUrl} alt="Report preview" className="h-40 w-[220px] rounded-[10px] border border-border object-cover" />
              <div className="min-w-[260px] flex-1">
                {isAnalyzing && (
                  <div className="flex items-center gap-2.5 py-3.5 text-[13px] text-muted">
                    <span className="spinner" /> Analyzing image with Gemini Vision…
                  </div>
                )}
                {errorMsg && <div className="py-3 text-[13px] text-red">{errorMsg}</div>}
                {result && (
                  <>
                    <div className="mb-1 text-[13px] text-muted">AI Vision Classification</div>
                    <div className="grid grid-cols-2 gap-2.5">
                      <ResultTile label="Issue Type" value={result.category} />
                      <ResultTile label="Severity" value={`${result.severity}/100`} color={severityColor(result.severity)} />
                      <ResultTile label="Priority Score" value={`${result.priority}/100`} />
                      <ResultTile label="Routed To" value={result.department} />
                    </div>
                    <div className="mt-3.5 rounded-[10px] border border-border bg-panel2 p-3 text-[12.5px] text-muted">
                      {result.justification}
                    </div>
                    <div className="mt-3 font-semibold text-pulse">✓ Report submitted — thank you! Tracking ID: {result.id}</div>
                  </>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      <div className="section-title">
        Your Submitted Reports <div className="line" />
      </div>
      <div className="panel overflow-x-auto">
        <table>
          <thead>
            <tr>
              <th>Issue</th>
              <th>Severity</th>
              <th>Priority</th>
              <th>Department</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {myReports.length === 0 ? (
              <tr>
                <td colSpan={5} className="py-6 text-center text-muted">
                  No reports submitted yet — upload a photo above to get started.
                </td>
              </tr>
            ) : (
              myReports.map((r) => (
                <tr key={r.id}>
                  <td>{r.category}</td>
                  <td>
                    <span className="mr-1.5 inline-block h-1.5 w-[60px] overflow-hidden rounded-md bg-panel2 align-middle">
                      <span
                        className="block h-full rounded-md"
                        style={{ width: `${r.severity}%`, background: severityColor(r.severity) }}
                      />
                    </span>
                    {r.severity}
                  </td>
                  <td>{r.priority}</td>
                  <td>{r.department}</td>
                  <td>
                    <span
                      className="pill"
                      style={{ background: `${statusColor(r.status)}22`, color: statusColor(r.status) }}
                    >
                      {r.status}
                    </span>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function ResultTile({ label, value, color }: { label: string; value: string; color?: string }) {
  return (
    <div className="rounded-[10px] border border-border bg-panel2 p-3">
      <label className="font-mono text-[10.5px] uppercase tracking-wide text-muted">{label}</label>
      <div className="mt-1 text-[14.5px] font-semibold" style={color ? { color } : undefined}>
        {value}
      </div>
    </div>
  );
}
