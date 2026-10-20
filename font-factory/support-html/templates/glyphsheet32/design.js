(function () {
  const green = "#149d26";
  const cream = "#fffbed";
  const ink = "#133c1a";
  const defaultSymbols = "$&%£€!?()";

  function addRun(board, { name, className, text, maxSize, minSize, width, height, tracking, color }) {
    const slot = document.createElement("div");
    slot.className = `glyph-copy ${className}`;
    slot.style.color = color;
    const run = document.createElement("span");
    run.className = "glyph-run";
    run.dataset.layoutItem = name;
    run.dataset.displayItem = "true";
    run.textContent = text;
    slot.append(run);
    board.append(slot);
    const size = window.SupportLayout.fitLine(run, {
      width: board.clientWidth * width,
      height: board.clientHeight * height,
      maxSize,
      minSize,
      tracking,
    });
    run.style.letterSpacing = `${tracking}em`;
    return size;
  }

  const design = {
    id: "glyphsheet32",
    title: "Green glyph sheet",
    defaults: { scale: 1 },
    controls: [
      { key: "scale", label: "Specimen scale", min: 0.78, max: 1.08, step: 0.01 },
    ],
    contrastException: {
      minimum: 3,
      rationale: "The cream and dark green source colors are reserved for the sheet’s oversized display rows.",
    },
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--green", green);
      board.style.setProperty("--cream", cream);
      board.style.setProperty("--ink", ink);
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");

      const grain = document.createElement("div");
      grain.className = "glyph-grain";
      grain.setAttribute("aria-hidden", "true");
      board.append(grain);

      const top = addRun(board, {
        name: "glyphsheet-digits", className: "digits", text: "0123456789",
        maxSize: 126 * state.scale, minSize: 38, width: .89, height: .21,
        tracking: -.025, color: cream,
      });
      addRun(board, {
        name: "glyphsheet-pangram", className: "pangram",
        text: props.pangram || "Pack my box with five dozen liquor jugs!",
        maxSize: 45 * state.scale, minSize: 22, width: .86, height: .11,
        tracking: -.01, color: ink,
      });
      addRun(board, {
        name: "glyphsheet-symbols", className: "symbols",
        text: props.symbols || defaultSymbols,
        maxSize: 132 * state.scale, minSize: 36, width: .88, height: .28,
        tracking: -.035, color: cream,
      });

      const rule = document.createElement("div");
      rule.className = "glyph-rule";
      rule.setAttribute("aria-hidden", "true");
      board.append(rule);
      const footer = document.createElement("div");
      footer.className = "glyph-footer";
      footer.dataset.layoutItem = "glyphsheet-footer";
      footer.textContent = "Figures / Signs / Punctuation";
      board.append(footer);
      const left = document.createElement("div");
      left.className = "glyph-stamp glyph-stamp-left";
      left.dataset.layoutItem = "glyphsheet-footer-left";
      left.textContent = "Letterforms";
      board.append(left);
      const right = document.createElement("div");
      right.className = "glyph-stamp glyph-stamp-right";
      right.dataset.layoutItem = "glyphsheet-footer-right";
      right.textContent = "Specimen 01";
      board.append(right);
      board.dataset.displaySize = String(top);
    },
    getContrast() {
      return Math.min(
        window.SupportLayout.contrast(cream, green),
        window.SupportLayout.contrast(ink, green),
      );
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Glyphsheet32 = design;
})();
