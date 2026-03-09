/**
 * Automated render test — verifies each composition produces valid frames.
 *
 * Renders frame 0 (first frame) and a mid-point frame from each composition
 * as still images, checking they produce non-empty PNG output.
 *
 * Usage: node tests/render-test.mjs
 */

import { bundle } from "@remotion/bundler";
import { renderStill, getCompositions } from "@remotion/renderer";
import { existsSync, mkdirSync, unlinkSync, statSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = join(__dirname, "..");
const ENTRY = join(ROOT, "src", "index.tsx");
const OUT_DIR = join(ROOT, "tests", "output");

// Ensure output dir exists
if (!existsSync(OUT_DIR)) {
  mkdirSync(OUT_DIR, { recursive: true });
}

async function main() {
  console.log("Bundling Remotion project...");
  const bundleLocation = await bundle({
    entryPoint: ENTRY,
    onProgress: (pct) => {
      if (pct % 25 === 0) process.stdout.write(`  bundle: ${pct}%\r`);
    },
  });
  console.log("Bundle complete.\n");

  // Get all compositions
  const compositions = await getCompositions(bundleLocation);
  console.log(`Found ${compositions.length} compositions: ${compositions.map((c) => c.id).join(", ")}\n`);

  let passed = 0;
  let failed = 0;

  for (const comp of compositions) {
    const testFrames = [0, Math.floor(comp.durationInFrames / 2)];

    for (const frameNum of testFrames) {
      const outFile = join(OUT_DIR, `${comp.id}_frame${frameNum}.png`);
      const label = `${comp.id} @ frame ${frameNum}`;

      try {
        await renderStill({
          composition: comp,
          serveUrl: bundleLocation,
          output: outFile,
          frame: frameNum,
          imageFormat: "png",
        });

        // Verify output exists and has content
        if (!existsSync(outFile)) {
          throw new Error("Output file was not created");
        }

        const stats = statSync(outFile);
        if (stats.size < 100) {
          throw new Error(`Output file too small: ${stats.size} bytes`);
        }

        console.log(`  PASS  ${label} (${(stats.size / 1024).toFixed(1)} KB)`);
        passed++;

        // Clean up test output
        unlinkSync(outFile);
      } catch (err) {
        console.error(`  FAIL  ${label}: ${err.message}`);
        failed++;
      }
    }
  }

  console.log(`\n${"=".repeat(50)}`);
  console.log(`Results: ${passed} passed, ${failed} failed, ${passed + failed} total`);

  if (failed > 0) {
    process.exit(1);
  }
}

main().catch((err) => {
  console.error("Render test crashed:", err);
  process.exit(1);
});
