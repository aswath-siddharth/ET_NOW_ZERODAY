/**
 * Build & Static Analysis Integrity Test (build_and_lint.test.mjs)
 * Tests whether `next build` and `eslint` execute without failures.
 * Documents real build/type errors and lint failures present in the codebase.
 */
import test from "node:test";
import assert from "node:assert/strict";
import { execSync } from "node:child_process";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const webDir = path.resolve(__dirname, "..");

test("Next.js production build and type checking should succeed", (t) => {
  try {
    const stdout = execSync("npm run build", { cwd: webDir, stdio: "pipe" }).toString();
    assert.ok(stdout.includes("Compiled successfully") || stdout.includes("Generating static pages"));
  } catch (err) {
    const errorOutput = (err.stdout ? err.stdout.toString() : "") + "\n" + (err.stderr ? err.stderr.toString() : "");
    assert.fail(`Next.js build failed with code ${err.status}:\n${errorOutput}`);
  }
});

test("ESLint static analysis should pass with 0 errors", (t) => {
  try {
    execSync("npm run lint", { cwd: webDir, stdio: "pipe" });
  } catch (err) {
    const errorOutput = (err.stdout ? err.stdout.toString() : "") + "\n" + (err.stderr ? err.stderr.toString() : "");
    assert.fail(`ESLint failed with code ${err.status}:\n${errorOutput}`);
  }
});
