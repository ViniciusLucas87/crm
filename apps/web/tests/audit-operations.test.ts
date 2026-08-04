import { readFileSync, existsSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const apiRoot = join(process.cwd(), "src", "app", "api");
const pageRoot = join(process.cwd(), "src", "app", "(dashboard)");

describe("Audit and Operations proxy routes", () => {
  it("has an audit proxy route that uses proxyAuthenticatedApi", () => {
    const routeFile = join(apiRoot, "audit", "route.ts");
    expect(existsSync(routeFile), "audit proxy route must exist").toBe(true);
    expect(readFileSync(routeFile, "utf8")).toContain("proxyAuthenticatedApi");
  });

  it("has an operations status proxy route that uses proxyAuthenticatedApi", () => {
    const routeFile = join(apiRoot, "operations", "status", "route.ts");
    expect(existsSync(routeFile), "operations/status proxy route must exist").toBe(true);
    expect(readFileSync(routeFile, "utf8")).toContain("proxyAuthenticatedApi");
  });

  it("audit proxy forwards to /audit path", () => {
    const content = readFileSync(join(apiRoot, "audit", "route.ts"), "utf8");
    expect(content).toContain("/audit");
  });

  it("operations proxy forwards to /operations/status path", () => {
    const content = readFileSync(join(apiRoot, "operations", "status", "route.ts"), "utf8");
    expect(content).toContain("/operations/status");
  });
});

describe("Audit and Operations pages", () => {
  it("audit page exists and is a client component", () => {
    const pageFile = join(pageRoot, "audit", "page.tsx");
    expect(existsSync(pageFile), "audit page must exist").toBe(true);
    const content = readFileSync(pageFile, "utf8");
    expect(content).toContain('"use client"');
    expect(content).toContain("export default");
  });

  it("operations page exists and is a client component", () => {
    const pageFile = join(pageRoot, "operations", "page.tsx");
    expect(existsSync(pageFile), "operations page must exist").toBe(true);
    const content = readFileSync(pageFile, "utf8");
    expect(content).toContain('"use client"');
    expect(content).toContain("export default");
  });

  it("audit page contains no mojibake", () => {
    const content = readFileSync(join(pageRoot, "audit", "page.tsx"), "utf8");
    expect(content).not.toMatch(/\u2014/);  // em-dash
    expect(content).not.toMatch(/\u00e2/);  // latin a with circumflex
  });

  it("operations page uses ReactNode for MetricCard value prop to support JSX", () => {
    const content = readFileSync(join(pageRoot, "operations", "page.tsx"), "utf8");
    // Must use ReactNode (not string|number) so StatusBadge JSX can be passed
    expect(content).toMatch(/value:\s*ReactNode/);
  });

  it("operations page contains no mojibake", () => {
    const content = readFileSync(join(pageRoot, "operations", "page.tsx"), "utf8");
    expect(content).not.toMatch(/\u2014/);
    expect(content).not.toMatch(/\u00e2/);
  });
});
