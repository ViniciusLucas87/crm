"use client";

import { useEffect, useState } from "react";

type CompatibilityState = "loading" | "compatible" | "mismatch" | "error";

interface BackendVersion {
  build_id: string;
  git_commit: string;
  model_fingerprint: string;
  status: string;
  phase: string;
}

/**
 * Frontend / Backend Compatibility Check
 *
 * On mount, fetches /health from the API and compares the Build ID
 * with the frontend's own version.json.
 *
 * If they don't match, renders a developer overlay showing the mismatch.
 * In production, this is a console warning only.
 */
export function VersionCompatibilityCheck() {
  const [state, setState] = useState<CompatibilityState>("loading");
  const [backend, setBackend] = useState<BackendVersion | null>(null);
  const [frontendVersion, setFrontendVersion] = useState<string>("unknown");

  useEffect(() => {
    let cancelled = false;

    async function check() {
      // Read frontend version (non-blocking, may not exist in dev)
      try {
        const feResp = await fetch("/version.json");
        if (feResp.ok && !cancelled) {
          const feData = await feResp.json();
          setFrontendVersion(feData.image_version || "unknown");
        }
      } catch {
        // version.json may not exist in dev — expected
      }

      // Read backend version via health endpoint
      try {
        const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "";
        const beResp = await fetch(`${apiBase}/api/health`);
        if (!beResp.ok) {
          // Health endpoint not available — skip check, not critical
          if (!cancelled) setState("compatible");
          return;
        }

        const beData: BackendVersion = await beResp.json();
        if (cancelled) return;

        setBackend(beData);

        if (beData.build_id === frontendVersion || beData.build_id === "unknown") {
          setState("compatible");
        } else {
          setState("mismatch");
          console.warn(
            "[PNS] Frontend/Backend version mismatch:",
            `\n  Frontend: ${frontendVersion}`,
            `\n  Backend:  ${beData.build_id}`,
            `\n  Fingerprint: ${beData.model_fingerprint}`,
            "\n  Run 'make rebuild' to sync.",
          );
        }
      } catch (err) {
        if (!cancelled) setState("error");
        console.warn("[PNS] Unable to verify backend compatibility:", err);
      }
    }

    check();
    return () => { cancelled = true; };
  }, [frontendVersion]);

  // Only show the overlay in development when there's a mismatch
  if (state !== "mismatch" || process.env.NODE_ENV === "production") {
    return null;
  }

  return (
    <div
      role="alert"
      style={{
        position: "fixed",
        bottom: 16,
        right: 16,
        zIndex: 99999,
        background: "#1a0a0a",
        border: "1px solid #ff4444",
        borderRadius: 12,
        padding: "16px 20px",
        maxWidth: 420,
        fontFamily: "monospace",
        fontSize: 12,
        color: "#ffcccc",
        boxShadow: "0 4px 24px rgba(255,0,0,0.15)",
      }}
    >
      <div style={{ fontWeight: "bold", color: "#ff6666", marginBottom: 8, fontSize: 13 }}>
        ⚠ Version Mismatch Detected
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "4px 12px" }}>
        <span style={{ color: "#ff8888" }}>Frontend:</span>
        <span>{frontendVersion}</span>
        <span style={{ color: "#ff8888" }}>Backend:</span>
        <span>{backend?.build_id || "unreachable"}</span>
      </div>
      <div style={{ marginTop: 8, fontSize: 11, color: "#ff9966" }}>
        Expected: <span style={{ color: "#ffcc99" }}>{frontendVersion}</span>
        &nbsp;|&nbsp; Actual:{" "}
        <span style={{ color: "#ffcc99" }}>{backend?.build_id || "unknown"}</span>
      </div>
      <div style={{ marginTop: 6, fontSize: 10, color: "#996666" }}>
        Run <code style={{ background: "#331111", padding: "1px 4px", borderRadius: 3 }}>make rebuild</code> to sync versions
      </div>
    </div>
  );
}
