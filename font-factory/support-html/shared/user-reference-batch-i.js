(function () {
  const svgNS = "http://www.w3.org/2000/svg";
  const config = {
    topText: "RABBITS · GO ASK ALICE",
    bottomText: "FOLLOW THE WHITE RABBIT",
  };

  function element(name, attrs = {}) {
    const node = document.createElementNS(svgNS, name);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, String(value));
    return node;
  }

  function starPath(cx, cy, outer = 23, inner = 10, count = 7) {
    const points = [];
    for (let index = 0; index < count * 2; index += 1) {
      const angle = -Math.PI / 2 + index * Math.PI / count;
      const radius = index % 2 === 0 ? outer : inner;
      points.push(`${cx + Math.cos(angle) * radius},${cy + Math.sin(angle) * radius}`);
    }
    return `M${points.join(" L")} Z`;
  }

  function createAliceBadge() {
    const design = {
      id: "alicebadge32",
      title: "Go Ask Alice round badge specimen",
      literalKeys: ["topText", "bottomText"],
      defaults: { ...config, displayScale: 1 },
      controls: [
        { key: "topText", type: "text", label: "Upper circular line" },
        { key: "bottomText", type: "text", label: "Lower circular line" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-alicebadge");
        board.replaceChildren();

        const svg = element("svg", {
          class: "ab-art",
          viewBox: "0 0 1000 1000",
          preserveAspectRatio: "xMidYMid meet",
          role: "img",
          "aria-label": "Round Alice-inspired badge with a sunset, stars, and curved live type",
        });
        const defs = element("defs");
        const clip = element("clipPath", { id: "ab-circle-clip" });
        clip.append(element("circle", { cx: 500, cy: 500, r: 328 }));
        defs.append(clip);
        const topPath = element("path", {
          id: "ab-top-arc",
          d: "M 90 500 A 410 410 0 0 1 910 500",
          fill: "none",
        });
        const bottomPath = element("path", {
          id: "ab-bottom-arc",
          d: "M 910 500 A 410 410 0 0 1 90 500",
          fill: "none",
        });
        defs.append(topPath, bottomPath);
        svg.append(defs);

        const scene = element("g", { "clip-path": "url(#ab-circle-clip)" });
        scene.append(element("circle", { cx: 500, cy: 500, r: 328, fill: "#ffe0a2" }));
        scene.append(element("path", {
          d: "M 170 600 C 300 525 408 555 500 516 C 630 458 742 508 830 578 L 830 865 L 170 865 Z",
          fill: "#ffa719",
        }));
        scene.append(element("path", {
          d: "M 230 815 C 345 765 430 790 520 772 C 642 748 730 788 790 824 L 825 900 L 180 900 Z",
          fill: "#85a8c7",
        }));
        scene.append(element("path", {
          d: "M 470 450 A 105 105 0 0 1 680 450 L 680 555 L 470 555 Z",
          fill: "#ec7287",
        }));
        scene.append(element("path", {
          d: "M 470 450 A 105 105 0 0 0 680 450 L 680 555 L 470 555 Z",
          fill: "#f4a9b8",
        }));
        scene.append(element("path", {
          d: "M 302 804 C 314 690 313 536 319 350 C 356 485 375 638 375 788 Z",
          fill: "#242328",
        }));
        scene.append(element("path", {
          d: "M 372 812 C 392 690 430 515 464 360 C 450 540 455 700 435 824 Z",
          fill: "#242328",
        }));
        scene.append(element("path", {
          d: "M 399 825 C 485 724 594 664 695 628 C 616 704 531 778 471 844 Z",
          fill: "#242328",
        }));
        svg.append(scene);

        svg.append(element("circle", {
          cx: 500, cy: 500, r: 338, fill: "none", stroke: "#242328", "stroke-width": 12,
        }));
        svg.append(element("path", { d: starPath(90, 500, 21, 9), fill: "#85a8c7" }));
        svg.append(element("path", { d: starPath(910, 500, 21, 9), fill: "#85a8c7" }));

        const top = element("text", { class: "ab-ring ab-ring-top", "data-layout-item": "alicebadge32-top-copy", "data-display-item": "true" });
        const topText = element("textPath", { href: "#ab-top-arc", startOffset: "50%", "text-anchor": "middle", textLength: 1120, lengthAdjust: "spacingAndGlyphs" });
        topText.textContent = String(state.topText ?? config.topText);
        top.append(topText);
        svg.append(top);

        const bottom = element("text", { class: "ab-ring ab-ring-bottom", "data-layout-item": "alicebadge32-bottom-copy", "data-display-item": "true" });
        const bottomText = element("textPath", { href: "#ab-bottom-arc", startOffset: "50%", "text-anchor": "middle", textLength: 1120, lengthAdjust: "spacingAndGlyphs" });
        bottomText.textContent = String(state.bottomText ?? config.bottomText);
        bottom.append(bottomText);
        svg.append(bottom);
        board.append(svg);

        window.SupportLayout.fitLine(top, {
          width: 1280,
          height: 110,
          maxSize: 72 * scale,
          minSize: 38,
          tracking: .015,
        });
        window.SupportLayout.fitLine(bottom, {
          width: 1280,
          height: 110,
          maxSize: 72 * scale,
          minSize: 38,
          tracking: .015,
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#ff526d", "#242328");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  window.UserReferenceBatchI = {
    ids: ["alicebadge32"],
    create(id) {
      if (id !== "alicebadge32") throw new Error(`Unknown reference template: ${id}`);
      return createAliceBadge();
    },
  };
})();
