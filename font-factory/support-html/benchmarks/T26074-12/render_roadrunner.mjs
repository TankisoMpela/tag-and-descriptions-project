#!/usr/bin/env node
import { chromium } from "playwright";
import { mkdir, writeFile, stat } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const get = (key, fallback) => {
  const index = process.argv.indexOf("--" + key);
  return index < 0 ? fallback : process.argv[index + 1];
};
const out = path.resolve(get("out", path.join(here, "output/roadrunner-cli.png")));
const font = get("font", "");
const labelFont = get("label-font", "");
const headline = get("headline", "Got the radio\non, I'm like the\nroadrunner.").replaceAll("\\n", "\n");
const descriptor = get("descriptor", "A soft sans serif with spirit,\npersonality and distinction.").replaceAll("\\n", "\n");
const body = get("body", "This bold and semi-condensed typeface is lively and eye-catching,\nideal for where and when you want to make a lasting impression.").replaceAll("\\n", "\n");
const badge = get("badge", "Nektar");
const values = {
  angle: get("angle", "-7"),
  size: get("size", "160"),
  y: get("y", "0"),
  lime: get("lime", "#d7e814"),
  ink: get("ink", "#302a31"),
  pink: get("pink", "#f68bb6"),
};
const url = get("url", pathToFileURL(path.join(here, "layout-editor.html")).href);

await mkdir(path.dirname(out), { recursive: true });
const browser = await chromium.launch({
  executablePath: "/usr/bin/chromium",
  headless: true,
  args: ["--no-sandbox"],
});
try {
  const page = await browser.newPage({
    viewport: { width: 1520, height: 1024 },
    deviceScaleFactor: 2,
  });
  await page.goto(url, { waitUntil: "networkidle" });
  await page.evaluate(() => document.fonts.ready);
  for (const key of ["angle", "size", "y"]) {
    const value = values[key];
    await page.evaluate(([id, next]) => {
      const input = document.querySelector("#" + id);
      input.value = next;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }, [key === "y" ? "hy" : key, value]);
  }
  await page.locator("#copy").fill(headline);
  await page.locator("#descriptor-copy").fill(descriptor);
  await page.locator("#body-copy").fill(body);
  await page.locator("#badge-copy").fill(badge);
  for (const key of ["lime", "ink", "pink"]) {
    await page.evaluate(([id, next]) => {
      const input = document.querySelector("#" + id);
      input.value = next;
      input.dispatchEvent(new Event("input", { bubbles: true }));
    }, [key, values[key]]);
  }
  if (font) {
    await page.locator("#font-file").setInputFiles(path.resolve(font));
    await page.getByText(/loaded as the live headline font/).waitFor();
  }
  if (labelFont) {
    await page.locator("#label-font-file").setInputFiles(path.resolve(labelFont));
    await page.getByText(/loaded as the live label font/).waitFor();
  }
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(80);

  const frame = page.locator("#artboard");
  await frame.evaluate((el) => {
    Object.assign(el.style, {
      position: "fixed",
      left: "0",
      top: "0",
      width: "1200px",
      maxWidth: "none",
      margin: "0",
      zIndex: "2147483647",
    });
  });
  const bounds = await frame.boundingBox();
  if (!bounds || Math.round(bounds.width) !== 1200 || Math.round(bounds.height) !== 800) {
    throw new Error("Expected a 1200 × 800 CSS artboard, got " + JSON.stringify(bounds));
  }
  await page.evaluate(() => window.updateLayout());
  await page.evaluate(() => new Promise(requestAnimationFrame));
  const layoutReport = await page.evaluate(() => {
    const board = document.querySelector("#artboard");
    const frame = board.getBoundingClientRect();
    const selectors = [".hero span", ".descriptor", ".bodycopy", ".topmark", ".nektar"];
    const slots = selectors.flatMap((selector) => [...board.querySelectorAll(selector)].map((el) => {
      const r = el.getBoundingClientRect();
      return {
        name: selector === ".hero span" ? "headline_line" : selector.slice(1),
        text: el.textContent.trim(),
        x: Number((r.left - frame.left).toFixed(1)),
        y: Number((r.top - frame.top).toFixed(1)),
        width: Number(r.width.toFixed(1)),
        height: Number(r.height.toFixed(1)),
      };
    }));
    const outOfBounds = slots.filter((s) =>
      s.x < -1 || s.y < -1 || s.x + s.width > frame.width + 1 ||
      s.y + s.height > frame.height + 1);
    const luminance = (hex) => {
      const rgb = hex.slice(1).match(/.{2}/g).map((pair) => parseInt(pair, 16) / 255);
      const linear = rgb.map((v) => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
      return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2];
    };
    const style = getComputedStyle(board);
    const ink = style.getPropertyValue("--ink").trim() || "#302a31";
    const lime = style.getPropertyValue("--lime").trim() || "#d7e814";
    const pair = [luminance(ink), luminance(lime)].sort((a, b) => b - a);
    return {
      frame: { width: frame.width, height: frame.height },
      headlineFontSize: getComputedStyle(document.querySelector("#hero")).fontSize,
      descriptorFontSize: getComputedStyle(document.querySelector(".descriptor")).fontSize,
      bodyFontSize: getComputedStyle(document.querySelector(".bodycopy")).fontSize,
      badgeFontSize: getComputedStyle(document.querySelector(".nektar")).fontSize,
      inkOnLimeContrast: Number(((pair[0] + 0.05) / (pair[1] + 0.05)).toFixed(2)),
      slots,
      outOfBounds,
    };
  });
  if (layoutReport.outOfBounds.length) {
    throw new Error("HTML layout has off-canvas elements: " + JSON.stringify(layoutReport.outOfBounds));
  }
  if (parseFloat(layoutReport.headlineFontSize) < 38) {
    throw new Error("HTML headline fell below the 38px legibility floor: "
      + layoutReport.headlineFontSize);
  }
  if (layoutReport.inkOnLimeContrast < 4.5) {
    throw new Error("HTML text contrast is below 4.5:1: "
      + layoutReport.inkOnLimeContrast + ":1");
  }
  await frame.screenshot({ path: out, scale: "device" });
  const result = {
    renderer: "HTML/CSS + headless Chromium",
    browser: browser.version(),
    source: "T26074_12",
    exportPixels: { width: 2400, height: 1600 },
    font: font ? path.resolve(font) : "LilitaOne-Regular.ttf",
    labelFont: labelFont ? path.resolve(labelFont) : "NotoSans-CondensedExtraBold.ttf",
    headline,
    descriptor,
    body,
    badge,
    layout: { angle: values.angle, size: values.size, y: values.y },
    colors: { lime: values.lime, ink: values.ink, pink: values.pink },
    layoutReport,
    output: out,
    outputBytes: (await stat(out)).size,
  };
  if (!process.argv.includes("--no-record")) {
    await writeFile(out.replace(/\.png$/i, ".json"), JSON.stringify(result, null, 2) + "\n");
  }
  console.log(JSON.stringify(result, null, 2));
} finally {
  await browser.close();
}
