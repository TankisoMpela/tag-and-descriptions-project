(function () {
  const SVG_NS = "http://www.w3.org/2000/svg";
  const coral = "#d9655f";
  const paperGrainCache = new Map();

  function paperGrain(width, height) {
    const key = `${width}x${height}`;
    if (paperGrainCache.has(key)) return paperGrainCache.get(key);
    const canvas = document.createElement("canvas");
    canvas.className = "paper-grain";
    canvas.width = width;
    canvas.height = height;
    canvas.setAttribute("aria-hidden", "true");
    const context = canvas.getContext("2d", { alpha: true });
    const pixels = context.createImageData(width, height);
    let seed = 24507;
    const random = () => {
      seed = (seed * 1664525 + 1013904223) >>> 0;
      return seed / 4294967296;
    };
    for (let i = 0; i < pixels.data.length; i += 4) {
      const light = random() > .5;
      pixels.data[i] = light ? 255 : 44;
      pixels.data[i + 1] = light ? 249 : 53;
      pixels.data[i + 2] = light ? 225 : 35;
      pixels.data[i + 3] = 92;
    }
    context.putImageData(pixels, 0, 0);
    paperGrainCache.set(key, canvas);
    return canvas;
  }

  function starPath(cx, cy, outer, inner) {
    const points = [];
    for (let i = 0; i < 10; i += 1) {
      const angle = -Math.PI / 2 + i * Math.PI / 5;
      const radius = i % 2 === 0 ? outer : inner;
      points.push(`${cx + Math.cos(angle) * radius},${cy + Math.sin(angle) * radius}`);
    }
    return `M${points.join(" L")} Z`;
  }

  function horseshoeSvg(color) {
    const svg = document.createElementNS(SVG_NS, "svg");
    svg.setAttribute("viewBox", "0 0 100 150");
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = `
      <path d="M15 14 C13 72 23 130 50 132 C77 130 87 72 85 14"
        fill="none" stroke="${color}" stroke-width="3.2" stroke-linecap="round"/>
      <path d="M31 17 C29 72 36 108 50 111 C64 108 71 72 69 17"
        fill="none" stroke="${color}" stroke-width="2.1" stroke-linecap="round"/>
      <path d="M15 14 L25 17 M85 14 L75 17" fill="none"
        stroke="${color}" stroke-width="3.2" stroke-linecap="round"/>
      ${[[22,42,4.6],[28,82,5],[50,116,6],[72,82,5],[78,42,4.6]]
        .map(([x,y,r]) => `<path d="${starPath(x,y,r,r*.39)}" fill="${color}"/>`).join("")}
      ${[[17,30],[20,58],[27,103],[36,121],[50,129],[64,121],[73,103],[80,58],[83,30]]
        .map(([x,y]) => `<circle cx="${x}" cy="${y}" r="1.1" fill="${color}"/>`).join("")}
      <path d="M37 23 C39 52 40 79 50 96 C60 79 61 52 63 23"
        fill="none" stroke="${color}" stroke-width="1.1" opacity=".65"/>
    `;
    return svg;
  }

  const design = {
    id: "boots32",
    title: "Wild Boots",
    defaults: {
      title: "Wild Boots",
      subtitle: "photography",
      titleScale: 1,
      subtitleScale: 1,
      photoScale: 1,
      horseshoeScale: 1,
      bootScale: 1.07,
      bootX: 78.5,
      bootY: 63.2,
      tracking: -0.005,
    },
    controls: [
      { key: "title", label: "Main lettering", type: "text" },
      { key: "subtitle", label: "Subline", type: "text" },
      { key: "titleScale", label: "Main lettering scale", min: 0.78, max: 1.12, step: 0.01 },
      { key: "subtitleScale", label: "Subline scale", min: 0.76, max: 1.14, step: 0.01 },
      { key: "photoScale", label: "Portrait framing", min: 0.9, max: 1.12, step: 0.01 },
      { key: "horseshoeScale", label: "Horseshoe scale", min: 0.8, max: 1.2, step: 0.01 },
      { key: "bootScale", label: "Boot scale", min: 0.8, max: 1.12, step: 0.01 },
      { key: "bootX", label: "Boot horizontal position", min: 76, max: 82, step: 0.2 },
      { key: "bootY", label: "Boot vertical position", min: 60, max: 66, step: 0.2 },
      { key: "tracking", label: "Letter spacing", min: -0.05, max: 0.04, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--boots-ground", props.ground || "#d6debe");
      board.style.setProperty("--boots-ink", props.ink || "#1b522c");
      board.style.setProperty("--boots-accent", props.accent || coral);
      board.style.setProperty("--display-face", "SupportDisplay, Z003, cursive");
      board.append(paperGrain(Math.max(1, Math.ceil(board.clientWidth)),
                              Math.max(1, Math.ceil(board.clientHeight))));

      const portrait = document.createElement("div");
      portrait.className = "boots-portrait";
      portrait.dataset.layoutItem = "portrait-panel";
      const sky = document.createElement("div");
      sky.className = "portrait-sky";
      const landscape = document.createElement("img");
      landscape.className = "portrait-ground";
      landscape.src = "../../../support-references/materials/T24507_04_saltflat-photo-crop.png";
      landscape.alt = "";
      landscape.style.transform = `scale(${state.photoScale})`;
      portrait.append(sky, landscape);
      board.append(portrait);

      const positions = [
        { cx: .065, cy: .145, width: .105, height: .19, rotation: -14 },
        { cx: .145, cy: .115, width: .125, height: .22, rotation: 0 },
        { cx: .225, cy: .15, width: .095, height: .18, rotation: 13 },
      ];
      for (const shoe of positions) {
        const size = state.horseshoeScale;
        const svg = horseshoeSvg(props.accent || coral);
        svg.classList.add("western-horseshoe");
        svg.style.left = `${(shoe.cx - shoe.width * size / 2) * 100}%`;
        svg.style.top = `${(shoe.cy - shoe.height * size / 2) * 100}%`;
        svg.style.width = `${shoe.width * size * 100}%`;
        svg.style.height = `${shoe.height * size * 100}%`;
        svg.style.transform = `rotate(${shoe.rotation}deg)`;
        board.append(svg);
      }

      const boot = document.createElement("div");
      boot.className = "engraved-boot";
      boot.dataset.layoutItem = "engraved-boot";
      boot.setAttribute("aria-hidden", "true");
      const bootWidth = board.clientWidth * .175 * state.bootScale;
      boot.style.left = `${state.bootX}%`;
      boot.style.top = `${state.bootY}%`;
      boot.style.width = `${bootWidth}px`;
      boot.style.height = `${bootWidth / (1100 / 1334)}px`;
      board.append(boot);

      const makeCopy = (key, text, className, box) => {
        const element = document.createElement("div");
        element.className = className;
        element.dataset.layoutItem = key;
        element.dataset.displayItem = "true";
        element.textContent = text;
        board.append(element);
        window.SupportLayout.fitLine(element, {
          width: board.clientWidth * box.width,
          height: board.clientHeight * box.height,
          maxSize: board.clientHeight * box.max * (box.scale || 1),
          minSize: board.clientHeight * box.min,
          tracking: state.tracking,
        });
        element.style.letterSpacing = `${state.tracking}em`;
      };

      makeCopy("main-lettering", props.title ?? state.title ?? "Wild Boots", "boots-title", {
        width: .44, height: .16, max: .138, min: .07, scale: state.titleScale,
      });
      makeCopy("poster-subline", props.subtitle ?? state.subtitle ?? "photography", "boots-subtitle", {
        width: .30, height: .09, max: .061, min: .04, scale: state.subtitleScale,
      });
    },
    getContrast() {
      const board = document.getElementById("artboard");
      const style = getComputedStyle(board);
      return window.SupportLayout.contrast(
        style.getPropertyValue("--boots-ink").trim(),
        style.getPropertyValue("--boots-ground").trim(),
      );
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Boots32 = design;
})();
