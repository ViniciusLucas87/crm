import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

const apiRoot = join(process.cwd(), "src", "app", "api");

function routeFiles(directory: string): string[] {
  return readdirSync(directory).flatMap((entry) => {
    const path = join(directory, entry);
    return statSync(path).isDirectory()
      ? routeFiles(path)
      : entry === "route.ts" ? [path] : [];
  });
}

describe("CRM API proxy wiring", () => {
  it("routes every browser API call through the authenticated proxy", () => {
    for (const file of routeFiles(apiRoot)) {
      expect(readFileSync(file, "utf8"), file).toContain("proxyAuthenticatedApi");
    }
  });

  it("forwards non-GET bodies as raw bytes so uploads are not corrupted", () => {
    const helper = readFileSync(join(apiRoot, "_utils.ts"), "utf8");
    expect(helper).toContain("request.arrayBuffer()");
    expect(helper).not.toContain("await request.text()");
  });

  it("includes proxies used by document actions and decision-maker screens", () => {
    expect(readFileSync(join(apiRoot, "documents", "[id]", "route.ts"), "utf8"))
      .toContain("/documents/${id}");
    expect(readFileSync(join(apiRoot, "decision-maker", "[companyId]", "route.ts"), "utf8"))
      .toContain("/decision-maker/${companyId}");
  });
});
