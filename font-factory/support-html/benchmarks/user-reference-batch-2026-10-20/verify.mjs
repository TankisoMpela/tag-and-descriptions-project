#!/usr/bin/env node
import { chromium } from "playwright";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const project = path.resolve(".");
const fontRoot = path.join(project, "font-factory", "fonts");
const out = path.join(project, "font-factory", "support-html", "benchmarks",
  "user-reference-batch-2026-10-20", "output");
const templateRoot = path.join(project, "font-factory", "support-html", "templates");
const ids = [
  "palmello32", "quietattempt32", "hushglow32", "italianhorror32",
  "dreamwarriors32", "nesting32", "erotica32", "conspiracytheory32",
  "overglow32", "pinkvice32", "attitude32", "indieground32",
  "caramelsundae32", "sweettreat32",
];
const fonts = [
  ["Maidega script", path.join(fontRoot, "Maidega", "Maidega-Regular.ttf")],
  ["Esviga blackletter", path.join(fontRoot, "archive", "Esviga", "Esviga – Blackletter Font 7DZ3HHR", "Esviga.ttf")],
  ["Markile rounded script", path.join(fontRoot, "Markile", "Markile – Bold Rounded Script U7MQV4U", "Markile.ttf")],
  ["Dragon Striker brush", path.join(fontRoot, "4-Dragon Striker", "Dragon Striker.ttf")],
];
const showcaseFont = {
  palmello32: 0, quietattempt32: 0, hushglow32: 2,
  italianhorror32: 3, dreamwarriors32: 3, nesting32: 3,
  erotica32: 3, conspiracytheory32: 3, overglow32: 2,
  pinkvice32: 2, attitude32: 2, indieground32: 2,
  caramelsundae32: 1, sweettreat32: 1,
};

await mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: "/usr/bin/chromium", headless: true,
  args: ["--no-sandbox", "--allow-file-access-from-files"] });
const results = [];
const failures = [];
try {
  const page = await browser.newPage({ viewport: { width: 1540, height: 1040 }, deviceScaleFactor: 1 });
  for (const id of ids) {
    for (let fontIndex = 0; fontIndex < fonts.length; fontIndex += 1) {
      const [fontLabel, fontPath] = fonts[fontIndex];
      await page.goto(pathToFileURL(path.join(templateRoot, id, "editor.html")).href,
        { waitUntil: "networkidle" });
      await page.locator("#font-file").setInputFiles(fontPath);
      await page.waitForFunction(() => document.querySelector("#font-status")?.textContent.includes("loaded as the live display font"));
      const config = await page.evaluate((templateId) =>
        window.UserReferenceBatch.getConfig(templateId), id);
      const longCopy = Object.fromEntries(config.fields
        .filter((field) => !["caption", "footer"].includes(field.key))
        .map((field) => [field.key, field.key.startsWith("line")
          ? "Extraordinary" : "Extraordinary Letterforms Dancing"]));
      for (const ratio of ["3x2", "1x1"]) {
        const dims = ratio === "1x1" ? [800, 800] : [1200, 800];
        await page.locator("#artboard").evaluate((element, size) => Object.assign(element.style, {
          position: "fixed", left: "0", top: "0", width: `${size[0]}px`,
          height: `${size[1]}px`, maxWidth: "none", margin: "0", zIndex: "2147483647",
        }), dims);
        await page.evaluate((value) => window.setSupportRatio(value), ratio);
        const defaultValues = Object.fromEntries(config.fields.map((field) => [field.key, field.value]));
        await page.evaluate((values) => window.configureTemplate(values), defaultValues);
        const standard = await page.evaluate(() => window.getLayoutReport());
        await page.evaluate((values) => window.configureTemplate(values), longCopy);
        const stress = await page.evaluate(() => window.getLayoutReport());
        for (const [kind, report] of [["standard", standard], ["long-copy", stress]]) {
          const issue = {
            template: id, font: fontLabel, ratio, kind,
            outOfBounds: report.outOfBounds,
            fitFailures: report.fitFailures,
            displaySize: report.headlineFontSize,
            slots: report.slots.map(({ name, text, fontSize, x, y, width, height }) =>
              ({ name, text, fontSize, x, y, width, height })),
          };
          results.push(issue);
          if (issue.outOfBounds.length || issue.fitFailures.length ||
              (kind === "standard" && parseFloat(issue.displaySize) < 38)) failures.push(issue);
        }
        if (fontIndex === showcaseFont[id] && ratio === "3x2") {
          await page.evaluate((values) => window.configureTemplate(values), defaultValues);
          const imagePath = path.join(out, `${id}.png`);
          await page.locator("#artboard").screenshot({ path: imagePath, animations: "disabled" });
        }
      }
    }
  }
} finally {
  await browser.close();
}
const report = { templates: ids.length, representativeFonts: fonts.map(([name]) => name),
  ratios: ["3x2", "1x1"], cases: results.length, failures,
  results };
await writeFile(path.join(out, "font-fit-report.json"), JSON.stringify(report, null, 2) + "\n");
console.log(JSON.stringify({ templates: report.templates, fonts: report.representativeFonts,
  cases: report.cases, failureCount: failures.length,
  failureSummary: failures.map(({ template, font, ratio, kind, outOfBounds, fitFailures, displaySize }) =>
    ({ template, font, ratio, kind, outOfBounds, fitFailures, displaySize })) }, null, 2));
if (failures.length) process.exitCode = 1;
