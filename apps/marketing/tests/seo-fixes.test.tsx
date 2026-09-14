import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { describe, expect, it } from "vitest";

const read = (path: string) => readFileSync(resolve(__dirname, "..", path), "utf8");

describe("public-site SEO fixes", () => {
  it("uses a visible H1 from each tool's shared page title", () => {
    const source = read("src/components/free-tools/tool-page.tsx");
    expect(source.match(/<h1\b/g)).toHaveLength(1);
    expect(source).toMatch(/<h1[^>]*>\s*\{config\.title\}\s*<\/h1>/);
    expect(source).toMatch(/\{config\.description\}/);
  });

  it("sets HSTS without forcing HTTPS on unrelated subdomains", () => {
    const source = read("next.config.mjs");
    expect(source).toContain('key: "Strict-Transport-Security", value: "max-age=31536000"');
  });
});
