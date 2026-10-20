(function () {
  const defaults = {
    title: "9 Ligatures",
    lineOne: "ADCAQO",
    lineTwo: "STSZTTZS",
    scale: 1,
    glyphWidth: 1.42,
    tracking: -0.035,
    ground: "#131615",
    chalk: "#fdfcf3",
    orange: "#fe6900",
    cyan: "#00d8ff",
  };

  const ribbons = `
    <svg class="ribbon-art" viewBox="0 0 1200 800" preserveAspectRatio="none" aria-hidden="true" focusable="false">
      <path d="M-55 210 C34 236 150 91 302 91 L302 174 C195 176 97 275 -55 319Z" fill="var(--orange)"/>
      <path d="M877 91 C1004 89 1091 32 1162 -20 L1252 -20 C1167 48 1076 121 877 174Z" fill="var(--orange)"/>
      <path d="M-46 724 C10 700 96 780 164 812 L164 858 C78 850 4 840 -46 792Z" fill="var(--orange)"/>
    </svg>`;

  const arrowSvg = `<svg class="arrow-row" viewBox="0 0 540 92" preserveAspectRatio="none" role="img" aria-label="Seven directional arrows">
    <g fill="none" stroke="var(--cyan)" stroke-width="7" stroke-linecap="square" stroke-linejoin="miter">
      <g transform="translate(38 46) rotate(45)"><path d="M0 36V-36M-22-14 0-36 22-14"/></g>
      <g transform="translate(115 46) rotate(90)"><path d="M0 36V-36M-22-14 0-36 22-14"/></g>
      <g transform="translate(192 46) rotate(135)"><path d="M0 36V-36M-22-14 0-36 22-14"/></g>
      <g transform="translate(269 46) rotate(180)"><path d="M0 36V-36M-22-14 0-36 22-14"/></g>
      <g transform="translate(346 46) rotate(225)"><path d="M0 36V-36M-22-14 0-36 22-14"/></g>
      <g transform="translate(423 46) rotate(270)"><path d="M0 36V-36M-22-14 0-36 22-14"/></g>
      <g transform="translate(500 46) rotate(315)"><path d="M0 36V-36M-22-14 0-36 22-14"/></g>
    </g>
  </svg>`;

  const design = {
    id: "contour32",
    title: "Contour · Ligature study",
    defaults,
    controls: [
      { key: "title", label: "Specimen caption", type: "text", value: defaults.title },
      { key: "lineOne", label: "Upper glyph row", type: "text", value: defaults.lineOne },
      { key: "lineTwo", label: "Lower glyph row", type: "text", value: defaults.lineTwo },
      { key: "scale", label: "Glyph scale", min: 0.84, max: 1.08, step: 0.01 },
      { key: "glyphWidth", label: "Glyph width", min: 0.9, max: 1.5, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.09, max: 0.02, step: 0.005 },
      { key: "ground", label: "Board", type: "color", value: defaults.ground },
      { key: "chalk", label: "Specimen ink", type: "color", value: defaults.chalk },
      { key: "orange", label: "Ribbon", type: "color", value: defaults.orange },
      { key: "cyan", label: "Arrow ink", type: "color", value: defaults.cyan },
    ],
    render(board, state) {
      const values = state.props || state;
      design.warnings = values.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--ground", values.ground ?? state.ground);
      board.style.setProperty("--chalk", values.chalk ?? state.chalk);
      board.style.setProperty("--orange", values.orange ?? state.orange);
      board.style.setProperty("--cyan", values.cyan ?? state.cyan);
      board.style.setProperty("--glyph-width", Number(values.glyphWidth ?? state.glyphWidth));
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");

      const frame = document.createElement("div");
      frame.className = "specimen-frame";
      frame.dataset.layoutItem = "source-frame";
      frame.setAttribute("aria-hidden", "true");
      board.append(frame);

      board.insertAdjacentHTML("beforeend", ribbons);
      board.insertAdjacentHTML("beforeend", arrowSvg);

      const addText = (className, key, itemName, fallback, box, maxRatio, minRatio) => {
        const element = document.createElement("div");
        element.className = className;
        element.dataset.layoutItem = itemName;
        element.dataset.displayItem = "true";
        element.textContent = values[key] ?? state[key] ?? fallback;
        board.append(element);
        const size = window.SupportLayout.fitLine(element, {
          width: board.clientWidth * box.width,
          height: board.clientHeight * box.height,
          maxSize: board.clientHeight * maxRatio * Number(values.scale ?? state.scale),
          minSize: board.clientHeight * minRatio,
          tracking: Number(values.tracking ?? state.tracking),
          inkAware: true,
        });
        element.style.letterSpacing = `${Number(values.tracking ?? state.tracking)}em`;
        element.dataset.fittedSize = String(size);
        return element;
      };

      addText("ligature-caption", "title", "ligature-caption", defaults.title,
        { width: 0.34, height: 0.052 }, 0.041, 0.022);
      const fittedGlyphWidth = 0.88 / Number(values.glyphWidth ?? state.glyphWidth);
      addText("glyph-row glyph-row-one", "lineOne", "upper-glyph-row", defaults.lineOne,
        { width: fittedGlyphWidth, height: 0.245 }, 0.224, 0.08);
      addText("glyph-row glyph-row-two", "lineTwo", "lower-glyph-row", defaults.lineTwo,
        { width: fittedGlyphWidth, height: 0.235 }, 0.216, 0.08);
    },
    getContrast() {
      const board = document.getElementById("artboard");
      return window.SupportLayout.contrast(
        getComputedStyle(board).getPropertyValue("--chalk").trim(),
        getComputedStyle(board).getPropertyValue("--ground").trim(),
      );
    },
    getWarnings() { return design.warnings || []; },
  };

  window.Contour32 = design;
})();
