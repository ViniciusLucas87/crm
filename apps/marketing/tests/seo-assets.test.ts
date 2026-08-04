import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";
import sitemap from "../src/app/sitemap";

const root = resolve(__dirname, "..");
const read = (path: string) => readFileSync(resolve(root, path), "utf8");

describe("search and AI discovery assets", () => {
  it("allows search crawlers and blocks selected training crawlers", () => {
    const robots = read("public/robots.txt").replaceAll("\r\n", "\n");
    for (const crawler of ["Googlebot", "Bingbot", "OAI-SearchBot"]) {
      expect(robots).toContain(`User-agent: ${crawler}\nAllow: /`);
    }
    for (const crawler of ["GPTBot", "Google-Extended", "ClaudeBot", "CCBot"]) {
      expect(robots).toContain(`User-agent: ${crawler}\nDisallow: /`);
    }
    expect(robots).toContain("Sitemap: https://pacificnorthsystems.com/sitemap.xml");
  });

  it("publishes transparent LLM guidance without unsupported benchmark claims", () => {
    const full = read("public/llms-full.txt");
    expect(full).toContain("/methodology");
    expect(full).toContain("not a representative survey");
    expect(full).not.toMatch(/typical(?:ly)? \d|industry literature|guarantees business outcomes/i);
  });

  it("includes tools, guides, research, methodology and contact in the sitemap", async () => {
    const urls = (await sitemap()).map((entry) => entry.url);
    for (const path of [
      "/free-tools",
      "/business-guides/do-i-need-a-crm",
      "/research/manual-work-cost-benchmark-2026",
      "/methodology",
      "/contact",
    ]) {
      expect(urls).toContain(`https://pacificnorthsystems.com${path}`);
    }
  });

  it("does not publish invented guide case studies or unsourced ranges", () => {
    const guides = read("src/lib/guides-data.ts");
    expect(guides).not.toMatch(/Vancouver-based logistics|Victoria-based service|Manitoba insurance|BC service company/i);
    expect(guides).not.toMatch(/industry benchmarks for recovery|average SMB loses|studies consistently show/i);
  });
});
