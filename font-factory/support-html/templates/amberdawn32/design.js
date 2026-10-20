(function () {
  const design = {
    id: "amberdawn32",
    title: "Amber Dawn",
    defaults: { lineOne: "Amber", lineTwo: "Dawn", caption: "Lively Brush Font", scale: 1, tracking: -0.035 },
    controls: [
      { key: "lineOne", label: "First headline line", type: "text", value: "Amber" },
      { key: "lineTwo", label: "Second headline line", type: "text", value: "Dawn" },
      { key: "scale", label: "Headline scale", min: 0.78, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Headline spacing", min: -0.10, max: 0.01, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");

      const veil = document.createElement("div");
      veil.className = "amber-veil";
      board.append(veil);
      const lines = [
        { text: props.lineOne ?? state.lineOne ?? "Amber", cls: "amber-line-one", name: "amber-headline-one", height: .30, scale: 1 },
        { text: props.lineTwo ?? state.lineTwo ?? "Dawn", cls: "amber-line-two", name: "amber-headline-two", height: .30, scale: .82 },
      ];
      for (const spec of lines) {
        const line = document.createElement("div");
        line.className = `amber-headline ${spec.cls}`;
        line.dataset.layoutItem = spec.name;
        line.dataset.displayItem = "true";
        line.textContent = spec.text;
        board.append(line);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * .75,
          height: board.clientHeight * spec.height,
          maxSize: 400 * state.scale * spec.scale,
          minSize: 64,
          tracking: state.tracking,
        });
        line.style.letterSpacing = `${state.tracking}em`;
      }

      const badge = document.createElement("div");
      badge.className = "amber-badge";
      badge.dataset.layoutItem = "amber-glyph-badge";
      badge.innerHTML = `<svg viewBox="0 0 200 200" aria-hidden="true">
        <defs><path id="amber-circle-copy" d="M 27 118 A 76 76 0 1 1 173 118" /></defs>
        <path class="amber-ring" d="M 24 101 A 76 76 0 0 0 100 176" />
        <text class="amber-arc-type" text-anchor="middle"><textPath href="#amber-circle-copy" startOffset="50%">Three Fonts Included</textPath></text>
      </svg>`;
      const count = document.createElement("span");
      count.className = "amber-count";
      count.textContent = props.glyphCount || "482";
      const glyphLabel = document.createElement("span");
      glyphLabel.className = "amber-glyph-label";
      glyphLabel.textContent = "Glyphs";
      badge.append(count, glyphLabel);
      board.append(badge);

      const rule = document.createElement("div");
      rule.className = "amber-rule";
      rule.dataset.layoutItem = "amber-footer-rule";
      board.append(rule);
      const caption = document.createElement("div");
      caption.className = "amber-footer amber-footer-left";
      caption.dataset.layoutItem = "amber-caption";
      caption.textContent = props.caption ?? state.caption ?? "Lively Brush Font";
      board.append(caption);
      const footer = document.createElement("div");
      footer.className = "amber-footer amber-footer-right";
      footer.dataset.layoutItem = "amber-footer-right";
      footer.textContent = "By Set Sail Studios";
      board.append(footer);
    },
    getContrast() { return window.SupportLayout.contrast("#ffe51c", "#4b4130"); },
    getWarnings() { return design.warnings || []; },
  };
  window.AmberDawn32 = design;
})();
