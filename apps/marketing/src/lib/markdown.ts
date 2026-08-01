/**
 * Lightweight Markdown-to-HTML renderer.
 * Handles the subset of Markdown used in blog articles.
 */
export function renderMarkdown(raw: string): string {
  const lines = raw.split(/\r?\n/);
  const output: string[] = [];
  let inCodeBlock = false;
  let codeContent = "";
  let codeLang = "";
  let inList: "ul" | "ol" | null = null;

  function flushList(): void {
    if (inList) {
      output.push(`</${inList}>`);
      inList = null;
    }
  }

  function processInline(text: string): string {
    // Bold
    text = text.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
    // Italic
    text = text.replace(/\*(.+?)\*/g, "<em>$1</em>");
    // Inline code
    text = text.replace(/`(.+?)`/g, "<code>$1</code>");
    // Links
    text = text.replace(
      /\[(.+?)\]\((.+?)\)/g,
      '<a href="$2">$1</a>',
    );
    return text;
  }

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];

    // Code blocks
    if (line.startsWith("```")) {
      if (inCodeBlock) {
        const langAttr = codeLang ? ` class="language-${codeLang}"` : "";
        output.push(`<pre><code${langAttr}>${escapeHtml(codeContent.trim())}</code></pre>`);
        codeContent = "";
        codeLang = "";
        inCodeBlock = false;
      } else {
        flushList();
        codeLang = line.slice(3).trim();
        inCodeBlock = true;
      }
      continue;
    }

    if (inCodeBlock) {
      codeContent += line + "\n";
      continue;
    }

    // Empty line
    if (!line.trim()) {
      flushList();
      continue;
    }

    // Headings
    const h2Match = line.match(/^## (.+)$/);
    if (h2Match) {
      flushList();
      output.push(`<h2>${processInline(h2Match[1])}</h2>`);
      continue;
    }
    const h3Match = line.match(/^### (.+)$/);
    if (h3Match) {
      flushList();
      output.push(`<h3>${processInline(h3Match[1])}</h3>`);
      continue;
    }

    // Horizontal rule
    if (/^---+\s*$/.test(line)) {
      flushList();
      output.push("<hr />");
      continue;
    }

    // Unordered list
    const ulMatch = line.match(/^-\s+(.+)$/);
    if (ulMatch) {
      if (inList !== "ul") {
        flushList();
        output.push("<ul>");
        inList = "ul";
      }
      output.push(`<li>${processInline(ulMatch[1])}</li>`);
      continue;
    }

    // Ordered list
    const olMatch = line.match(/^\d+\.\s+(.+)$/);
    if (olMatch) {
      if (inList !== "ol") {
        flushList();
        output.push("<ol>");
        inList = "ol";
      }
      output.push(`<li>${processInline(olMatch[1])}</li>`);
      continue;
    }

    // Paragraph
    flushList();
    output.push(`<p>${processInline(line)}</p>`);
  }

  flushList();

  return output.join("\n");
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
