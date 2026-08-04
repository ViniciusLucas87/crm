import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

describe("API client functions", () => {
  const apiFile = join(process.cwd(), "src", "lib", "api.ts");

  it("has fetchAuditEntries calling /audit (via Next.js proxy, not direct /api/v1)", () => {
    const content = readFileSync(apiFile, "utf8");
    // Uses template literal ${API_BASE_URL}/audit which becomes /api/audit
    expect(content).toMatch(/\$\{API_BASE_URL\}\/audit/);
    // Must NOT call /api/v1/audit directly
    expect(content).not.toMatch(/\/v1\/audit/);
  });

  it("has fetchOperationsStatus calling /operations/status (via Next.js proxy)", () => {
    const content = readFileSync(apiFile, "utf8");
    expect(content).toMatch(/\$\{API_BASE_URL\}\/operations\/status/);
    expect(content).not.toMatch(/\/v1\/operations\/status/);
  });

  it("exports AuditEntry, AuditListResponse, AuditListParams types", () => {
    const content = readFileSync(apiFile, "utf8");
    expect(content).toContain("export interface AuditEntry");
    expect(content).toContain("export interface AuditListResponse");
    expect(content).toContain("export interface AuditListParams");
  });

  it("exports OperationsStatus type", () => {
    const content = readFileSync(apiFile, "utf8");
    expect(content).toContain("export interface OperationsStatus");
  });
});

describe("Shell navigation", () => {
  const shellFile = join(process.cwd(), "src", "components", "dashboard", "shell.tsx");

  it("includes Audit Log in navigation with correct href", () => {
    const content = readFileSync(shellFile, "utf8");
    expect(content).toContain("Audit Log");
    expect(content).toContain('"/audit"');
  });

  it("includes System Status in navigation with correct href", () => {
    const content = readFileSync(shellFile, "utf8");
    expect(content).toContain("System Status");
    expect(content).toContain('"/operations"');
  });

  it("has Operations nav group with Shield and Activity icons imported", () => {
    const content = readFileSync(shellFile, "utf8");
    expect(content).toContain("Shield");
    expect(content).toContain("Activity");
  });
});

describe("Middleware protection", () => {
  const mwFile = join(process.cwd(), "src", "middleware.ts");

  it("protects /audit route", () => {
    const content = readFileSync(mwFile, "utf8");
    expect(content).toContain("/audit");
  });

  it("protects /operations route", () => {
    const content = readFileSync(mwFile, "utf8");
    expect(content).toContain("/operations");
  });

  it("uses auth.protect() for protected routes", () => {
    const content = readFileSync(mwFile, "utf8");
    expect(content).toContain("auth.protect()");
  });
});
