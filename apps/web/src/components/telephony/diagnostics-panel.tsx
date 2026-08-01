"use client";

import { X, Activity, Wifi, Mic, Radio, Code, BarChart3, MessageSquare, Lightbulb } from "lucide-react";
import { useState } from "react";
import { useTelephony } from "@/lib/telephony-context";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function DiagnosticsPanel() {
  const { diagnostics, transcription, call } = useTelephony();
  const [expanded, setExpanded] = useState(false);
  const d = diagnostics;
  const t = transcription;

  if (!expanded) {
    return (
      <button
        onClick={() => setExpanded(true)}
        className="fixed bottom-4 right-4 z-50 bg-gray-900 border border-gray-700 rounded-full p-3 shadow-lg hover:bg-gray-800 transition-colors"
        title="WebRTC Diagnostics"
      >
        <Activity className="w-5 h-5 text-emerald-400" />
      </button>
    );
  }

  return (
    <Card className="fixed bottom-4 right-4 z-50 w-96 max-h-[70vh] overflow-y-auto bg-gray-900 border-gray-700 text-gray-200 p-4 shadow-xl">
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-sm font-semibold flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          WebRTC Diagnostics
        </h3>
        <Button variant="ghost" size="sm" onClick={() => setExpanded(false)} className="p-1 h-auto">
          <X className="w-4 h-4" />
        </Button>
      </div>

      <div className="space-y-3 text-xs font-mono">
        {/* Client Status */}
        <Section icon={<Wifi className="w-3.5 h-3.5" />} label="SDK Connection">
          <Row label="SDK Loaded" value={d.sdkLoaded ? "✓" : "✗"} ok={d.sdkLoaded} />
          <Row label="Client State" value={d.clientState} ok={d.clientState === "connected"} />
        </Section>

        {/* Call State */}
        <Section icon={<Radio className="w-3.5 h-3.5" />} label="Call">
          <Row label="Call State" value={d.callState} ok={d.callState === "active"} />
          <Row label="Muted" value={d.muted ? "Yes" : "No"} ok={!d.muted} />
          <Row label="Held" value={d.held ? "Yes" : "No"} ok={!d.held} />
        </Section>

        {/* Media */}
        <Section icon={<Mic className="w-3.5 h-3.5" />} label="Media">
          <Row label="Mic Permission" value={d.micGranted ? "Granted" : "Denied"} ok={d.micGranted} />
          <Row label="Local Track" value={d.localTrack ? "Live" : "None"} ok={d.localTrack} />
          <Row label="Remote Track" value={d.remoteTrack ? "Receiving" : "None"} ok={d.remoteTrack} />
        </Section>

        {/* WebRTC Stats */}
        <Section icon={<BarChart3 className="w-3.5 h-3.5" />} label="WebRTC">
          <Row label="Peer State" value={d.peerState} ok={d.peerState === "connected"} />
          <Row label="ICE State" value={d.iceState} ok={d.iceState === "connected" || d.iceState === "completed"} />
          <Row label="Codec" value={d.codec || "—"} ok={!!d.codec} />
        </Section>

        {/* Selected ICE Pair */}
        {d.selectedIcePair && (
          <Section icon={<Code className="w-3.5 h-3.5" />} label="ICE Pair">
            <div className="text-gray-400 break-all">{d.selectedIcePair}</div>
          </Section>
        )}

        {/* Network */}
        <Section icon={<Activity className="w-3.5 h-3.5" />} label="Network">
          <Row label="Packets Sent" value={d.packetsSent.toLocaleString()} ok={d.packetsSent > 0} />
          <Row label="Packets Recv" value={d.packetsReceived.toLocaleString()} ok={d.packetsReceived > 0} />
          <Row label="Bytes Sent" value={formatBytes(d.bytesSent)} ok={d.bytesSent > 0} />
          <Row label="Bytes Recv" value={formatBytes(d.bytesReceived)} ok={d.bytesReceived > 0} />
          {d.packetsSent > 0 && d.bytesSent > 0 && (
            <Row label="Avg Pkt Size" value={`${Math.round(d.bytesSent / d.packetsSent)} B`} ok />
          )}
        </Section>

        {/* Call Duration & Provider */}
        <Section icon={<Radio className="w-3.5 h-3.5" />} label="Session">
          <Row label="Call Duration" value={formatDuration(call.duration)} ok={call.state === "connected"} />
          <Row label="Phone Number" value={call.phoneNumber || "—"} ok={!!call.phoneNumber} />
          <Row label="Connection" value={call.connectionQuality} ok={call.connectionQuality === "good"} />
        </Section>

        {/* Transcription (Sprint 42+) */}
        <Section icon={<MessageSquare className="w-3.5 h-3.5" />} label="Transcription">
          <Row label="Phase" value={t.phase} ok={t.phase === "streaming"} />
          <Row label="Provider" value={t.provider || "—"} ok={!!t.provider} />
          <Row label="Streaming" value={t.isStreaming ? "Live" : "Idle"} ok={t.isStreaming} />
          <Row label="Segments" value={String((t.segments || []).length)} ok />
          <Row label="Word Count" value={String(t.wordCount)} ok={t.wordCount > 0} />
          <Row label="Finals" value={String((t.segments || []).filter(s => s.isFinal).length)} ok={(t.segments || []).length > 0} />
          <Row label="Error" value={t.error || "—"} ok={!t.error} />
        </Section>

        {/* Coach */}
        <Section icon={<Lightbulb className="w-3.5 h-3.5" />} label="AI Coach">
          <Row label="Connected" value={call.state !== "idle" ? "Active" : "Standby"} ok={call.state !== "idle"} />
          <Row label="Call State" value={call.state} ok={call.state === "connected"} />
        </Section>
      </div>
    </Card>
  );
}

function Section({ icon, label, children }: { icon: React.ReactNode; label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1">
      <div className="flex items-center gap-1.5 text-gray-400 uppercase tracking-wider text-[10px] mb-1">
        {icon}
        {label}
      </div>
      {children}
    </div>
  );
}

function Row({ label, value, ok }: { label: string; value: string; ok?: boolean }) {
  return (
    <div className="flex justify-between">
      <span className="text-gray-500">{label}</span>
      <span className={ok === true ? "text-emerald-400" : ok === false ? "text-red-400" : "text-gray-300"}>
        {value}
      </span>
    </div>
  );
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDuration(s: number): string {
  const m = Math.floor(s / 60);
  const sec = s % 60;
  return `${m}:${sec.toString().padStart(2, "0")}`;
}
