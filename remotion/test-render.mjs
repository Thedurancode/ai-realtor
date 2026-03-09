/**
 * Automated render test — verifies all Remotion compositions produce valid frames.
 *
 * Usage: node test-render.mjs
 *
 * This renders frame 0 and a mid-frame of each composition to catch:
 * - Import errors
 * - Missing assets
 * - Runtime crashes in animation code
 * - Invalid React component trees
 */

import { bundle } from "@remotion/bundler";
import { renderStill } from "@remotion/renderer";
import { existsSync, mkdirSync, statSync, rmSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const OUTPUT_DIR = join(__dirname, ".test-renders");

// All compositions and their default durations
const COMPOSITIONS = [
  { id: "CaptionedReel", testFrames: [0, 150] },
  { id: "Slideshow", testFrames: [0] },
  { id: "TimelineEditor", testFrames: [0] },
  { id: "PropertyShowcase", testFrames: [0, 45] },
  { id: "CinematicEventRecap", testFrames: [0, 60] },
];

async function main() {
  console.log("Bundling Remotion project...");
  const bundleLocation = await bundle({
    entryPoint: join(__dirname, "src/index.tsx"),
    onProgress: (progress) => {
      if (progress === 100) console.log("  Bundle complete.");
    },
  });

  // Clean/create output dir
  if (existsSync(OUTPUT_DIR)) {
    rmSync(OUTPUT_DIR, { recursive: true });
  }
  mkdirSync(OUTPUT_DIR, { recursive: true });

  let passed = 0;
  let failed = 0;
  const failures = [];

  for (const comp of COMPOSITIONS) {
    for (const frameNum of comp.testFrames) {
      const testName = `${comp.id}@frame${frameNum}`;
      const outputPath = join(OUTPUT_DIR, `${comp.id}_frame${frameNum}.png`);

      try {
        console.log(`  Rendering ${testName}...`);
        await renderStill({
          composition: {
            id: comp.id,
            durationInFrames: 900,
            fps: 30,
            width: 1080,
            height: 1920,
            defaultProps: {},
            defaultCodec: null,
          },
          serveUrl: bundleLocation,
          frame: frameNum,
          output: outputPath,
        });

        // Verify output exists and has content
        if (!existsSync(outputPath)) {
          throw new Error("Output file not created");
        }
        const stats = statSync(outputPath);
        if (stats.size < 1000) {
          throw new Error(`Output too small (${stats.size} bytes) — likely blank`);
        }

        console.log(`  PASS ${testName} (${(stats.size / 1024).toFixed(1)}KB)`);
        passed++;
      } catch (err) {
        console.error(`  FAIL ${testName}: ${err.message}`);
        failed++;
        failures.push({ test: testName, error: err.message });
      }
    }
  }

  // Cleanup
  if (failed === 0 && existsSync(OUTPUT_DIR)) {
    rmSync(OUTPUT_DIR, { recursive: true });
  }

  console.log(`\nResults: ${passed} passed, ${failed} failed out of ${passed + failed} tests`);
  if (failures.length > 0) {
    console.log("\nFailures:");
    for (const f of failures) {
      console.log(`  ${f.test}: ${f.error}`);
    }
  }

  process.exit(failed > 0 ? 1 : 0);
}

main().catch((err) => {
  console.error("Fatal error:", err);
  process.exit(1);
});
