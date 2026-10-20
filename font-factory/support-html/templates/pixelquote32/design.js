(function () {
  const lines = [
    { text: "A Little", left: .28, top: .169, width: .44 },
    { text: "Nonsense", left: .27, top: .302, width: .46 },
    { text: "Now & Then", left: .20, top: .435, width: .60 },
    { text: "Is Relished By", left: .17, top: .570, width: .66 },
    { text: "The Wisest Man", left: .14, top: .720, width: .74 },
  ];
  const ornaments = [
    { name: "pixel-stitches-top", src: "T30332_09_pixel-stitches-top.png", x: 889, y: 49, w: 235, h: 26 },
    { name: "pixel-stitches-bottom", src: "T30332_09_pixel-stitches-bottom.png", x: 67, y: 720, w: 234, h: 26 },
    { name: "pixel-heart", src: "T30332_09_pixel-heart.png", x: 495, y: 96, w: 49, h: 41 },
    { name: "pixel-mascot", src: "T30332_09_pixel-mascot.png", x: 341, y: 689, w: 63, h: 57 },
  ];

  const design = {
    id: "pixelquote32",
    title: "Pixel quote",
    defaults: { scale: 1, lineSpacing: 0, tracking: -.018 },
    controls: [
      { key: "scale", label: "Quote scale", min: .92, max: 1.08, step: .01 },
      { key: "lineSpacing", label: "Line rhythm", min: -.006, max: .006, step: .001 },
      { key: "tracking", label: "Letter spacing", min: -.03, max: -.004, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scale = Number(props.scale ?? state.scale ?? 1);
      const lineSpacing = Number(props.lineSpacing ?? state.lineSpacing ?? 0);
      const tracking = Number(props.tracking ?? state.tracking ?? -.018);
      const dims = { width: board.clientWidth, height: board.clientHeight };

      for (const art of ornaments) {
        const image = document.createElement("img");
        image.className = "pixel-ornament";
        image.dataset.layoutItem = art.name;
        image.src = `../../../support-references/materials/${art.src}`;
        image.alt = "";
        image.draggable = false;
        image.style.left = `${art.x / 1184 * 100}%`;
        image.style.top = `${art.y / 792 * 100}%`;
        image.style.width = `${art.w / 1184 * 100}%`;
        image.style.height = `${art.h / 792 * 100}%`;
        board.append(image);
      }

      const quoteLines = [];
      lines.forEach((spec, index) => {
        const row = document.createElement("div");
        row.className = "quote-row";
        row.style.left = `${spec.left * 100}%`;
        row.style.top = `${(spec.top + index * lineSpacing) * 100}%`;
        row.style.width = `${spec.width * 100}%`;
        row.style.height = "13.2%";
        row.dataset.layoutItem = `quote-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "quote-line";
        line.dataset.layoutItem = `quote-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = spec.text;
        row.append(line);
        board.append(row);
        quoteLines.push({ element: line, spec });
      });

      for (const { element, spec } of quoteLines) {
        window.SupportLayout.fitLine(element, {
          width: dims.width * spec.width * .97,
          height: dims.height * .132 * .88,
          maxSize: dims.height * .158 * scale,
          minSize: dims.height * .035,
          tracking,
          inkAware: true,
        });
      }
    },
    getContrast() {
      return window.SupportLayout.contrast("#f44c9d", "#040406");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.PixelQuote32 = design;
})();
