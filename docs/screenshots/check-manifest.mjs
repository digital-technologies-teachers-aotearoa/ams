#!/usr/bin/env node
// Verifies docs/screenshots/manifest.json has no orphaned entries:
// - every manifest image exists on disk (i.e. has been generated);
// - every manifest image is actually embedded in each doc page it claims to be;
// - every image reference found in the docs is a manifest entry;
// - every image file on disk is a manifest entry.
// Run: `npm run docs:screenshots:check`.

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..", "..");
const DOCS_ROOT = path.join(REPO_ROOT, "docs", "docs");
const IMAGES_ROOT = path.join(DOCS_ROOT, "images");
const MANIFEST_PATH = path.join(__dirname, "manifest.json");

function walk(dir, extensions) {
  const results = [];
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      results.push(...walk(full, extensions));
    } else if (extensions.some((ext) => entry.name.endsWith(ext))) {
      results.push(full);
    }
  }
  return results;
}

function findImageReferences(markdownPath) {
  const text = fs.readFileSync(markdownPath, "utf8");
  const patterns = [
    /\]\(([^)]*images\/[^)]+)\)/g, // markdown ![alt](../images/foo.png)
    /src=["']([^"']*images\/[^"']+)["']/g, // <img src="../images/foo.png">
  ];
  const refs = [];
  for (const pattern of patterns) {
    for (const match of text.matchAll(pattern)) {
      refs.push(match[1].replace(/^.*images\//, ""));
    }
  }
  return refs;
}

function main() {
  const manifest = JSON.parse(fs.readFileSync(MANIFEST_PATH, "utf8"));
  const manifestFiles = new Map(manifest.map((entry) => [entry.file, entry]));
  const problems = [];

  // 1. Every manifest entry has been generated on disk.
  for (const entry of manifest) {
    const onDisk = path.join(IMAGES_ROOT, entry.file);
    if (!fs.existsSync(onDisk)) {
      problems.push(
        `Manifest entry "${entry.id}" declares ${entry.file}, but it doesn't exist on disk. Run \`npm run docs:screenshots\`.`,
      );
    }
  }

  // 2. Every manifest entry's declared pages actually reference the image, and
  //    every image reference in the docs is a manifest entry.
  const markdownFiles = fs.existsSync(DOCS_ROOT) ? walk(DOCS_ROOT, [".md"]) : [];
  const referencedFiles = new Set();

  for (const mdPath of markdownFiles) {
    const relDocPath = path.relative(DOCS_ROOT, mdPath).split(path.sep).join("/");
    const references = findImageReferences(mdPath);
    for (const ref of references) {
      referencedFiles.add(ref);
      if (!manifestFiles.has(ref)) {
        problems.push(
          `${relDocPath} embeds images/${ref}, which has no manifest entry. Add it to manifest.json.`,
        );
      }
    }
  }

  for (const entry of manifest) {
    for (const declaredPage of entry.pages) {
      const pagePath = path.join(DOCS_ROOT, declaredPage);
      if (!fs.existsSync(pagePath)) {
        problems.push(
          `Manifest entry "${entry.id}" declares page "${declaredPage}", which doesn't exist.`,
        );
        continue;
      }
      const references = findImageReferences(pagePath);
      if (!references.includes(entry.file)) {
        problems.push(
          `Manifest entry "${entry.id}" declares that ${declaredPage} embeds ${entry.file}, but no such reference was found there.`,
        );
      }
    }
  }

  // 3. Orphans on disk: images that exist but have no manifest entry.
  const filesOnDisk = fs.existsSync(IMAGES_ROOT)
    ? walk(IMAGES_ROOT, [".png", ".jpg", ".jpeg"]).map((f) =>
        path.relative(IMAGES_ROOT, f).split(path.sep).join("/"),
      )
    : [];
  for (const file of filesOnDisk) {
    if (!manifestFiles.has(file)) {
      problems.push(`${file} exists in docs/docs/images/ but has no manifest entry.`);
    }
  }

  // 4. Orphans in manifest: entries not embedded anywhere in the docs.
  for (const entry of manifest) {
    if (!referencedFiles.has(entry.file)) {
      problems.push(
        `Manifest entry "${entry.id}" (${entry.file}) isn't embedded in any doc page.`,
      );
    }
  }

  if (problems.length > 0) {
    console.error(`Found ${problems.length} problem(s):\n`);
    for (const problem of problems) {
      console.error(`- ${problem}`);
    }
    process.exitCode = 1;
    return;
  }

  console.log(`OK: ${manifest.length} manifest entr${manifest.length === 1 ? "y" : "ies"}, no orphans.`);
}

main();
