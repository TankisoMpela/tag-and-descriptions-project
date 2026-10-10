import {copyFileSync, existsSync, mkdirSync, readFileSync} from "node:fs";
import {basename, dirname, resolve} from "node:path";
import {spawnSync} from "node:child_process";

const args = new Map();
for (let i = 2; i < process.argv.length; i += 2) {
  args.set(process.argv[i].replace(/^--/, ""), process.argv[i + 1]);
}

const font = args.get("font");
const name = args.get("name");
const slug = args.get("slug") ?? name?.toLowerCase().replace(/[^a-z0-9]+/g, "-");
const output = args.get("output") ?? `out/${slug}-font-showcase.mp4`;
const width = Number(args.get("width") ?? 1920);
const height = Number(args.get("height") ?? 1080);

if (!font || !name || !slug) {
  throw new Error("Usage: node scripts/render-showcase.mjs --font <woff2> --name <name> [--slug <slug>] [--config <json>] [--output <mp4>]");
}

if (!Number.isInteger(width) || !Number.isInteger(height) || width <= 0 || height <= 0) {
  throw new Error("Width and height must be positive integers");
}

const root = resolve(dirname(new URL(import.meta.url).pathname), "..");
const configPath = args.get("config") ?? resolve(root, "showcase.config.json");
const outputPath = resolve(process.cwd(), output);
const publicFont = resolve(root, "public/fonts/ShowcaseFont.woff2");
mkdirSync(dirname(publicFont), {recursive: true});
copyFileSync(resolve(font), publicFont);

const config = configPath
  ? JSON.parse(readFileSync(resolve(configPath), "utf8"))
  : {fontName: name};
const props = JSON.stringify({
  fontName: name,
  ...config,
  width,
  height,
  segments: config.segments,
});

if (!Array.isArray(config.segments) || config.segments.length === 0) {
  throw new Error("Showcase config must contain a non-empty segments array");
}

if (config.segments.length !== 5) {
  throw new Error("Showcase config must contain exactly five 7-second scenes");
}

config.segments.forEach((segment, index) => {
  if (typeof segment.text !== "string" || segment.text.trim() === "") {
    throw new Error(`Scene ${index + 1} must contain non-empty text`);
  }
  if (!Number.isInteger(segment.fontSize) || segment.fontSize < 200) {
    throw new Error(
      `Scene ${index + 1} must define an integer fontSize of at least 200px ` +
        `(found ${JSON.stringify(segment.fontSize)})`,
    );
  }
  if (segment.fontSize > 600) {
    throw new Error(
      `Scene ${index + 1} fontSize ${segment.fontSize} exceeds the 600px maximum`,
    );
  }
  const wordCount = segment.text.trim().split(/\s+/).length;
  if (wordCount > 4) {
    throw new Error(`Scene ${index + 1} must contain no more than four words (found ${wordCount})`);
  }
  if (segment.seconds !== 7) {
    throw new Error(`Scene ${index + 1} must last exactly 7 seconds`);
  }
  if (segment.text.split("\n").length > 2) {
    throw new Error(`Scene ${index + 1} may contain at most two lines`);
  }
  const expectedSpeed = index === 4 ? 8 : 10;
  if (segment.charactersPerSecond !== expectedSpeed) {
    throw new Error(`Scene ${index + 1} must use ${expectedSpeed} characters per second`);
  }
  if (index < 4 && /\p{L}/u.test(segment.text) && segment.text === segment.text.toLocaleUpperCase()) {
    throw new Error(`Scene ${index + 1} must use sentence case, not an all-uppercase sentence`);
  }
});

if (config.segments[4].text !== name) {
  throw new Error("Scene 5 must contain exactly the supplied font name");
}

mkdirSync(dirname(outputPath), {recursive: true});
const result = spawnSync(
  "npx",
  [
    "remotion",
    "render",
    "src/index.ts",
    "MyComp",
    outputPath,
    `--props=${props}`,
    "--codec=h264",
    "--crf=16",
    "--overwrite",
  ],
  {cwd: root, stdio: "inherit"},
);

if (result.status !== 0) process.exit(result.status ?? 1);
if (!existsSync(outputPath)) {
  throw new Error(`Render completed without creating the expected MP4: ${outputPath}`);
}
console.log(`Rendered ${basename(output)} using ${basename(font)}`);
