(function () {
  const design = {
    id: "strongweak32",
    title: "Strongest / Weakest",
    labelFace: "StrongWeakLabel",
    defaults: {
      kicker: "Youngtype Studio",
      strongest: "Strongest",
      weakest: "Weakest",
      leftBadge: "Hand Drawn",
      rightBadge: "Stroke Regular Outline",
      footer: "Organic Hand Drawn",
      scale: 1,
      tracking: -0.04,
    },
    controls: [
      { key: "kicker", label: "Top caption", type: "text", value: "Youngtype Studio" },
      { key: "strongest", label: "Upper specimen", type: "text", value: "Strongest" },
      { key: "weakest", label: "Lower specimen", type: "text", value: "Weakest" },
      { key: "leftBadge", label: "Left sticker", type: "text", value: "Hand Drawn" },
      { key: "rightBadge", label: "Right sticker", type: "text", value: "Stroke Regular Outline" },
      { key: "footer", label: "Bottom specimen caption", type: "text", value: "Organic Hand Drawn" },
      { key: "scale", label: "Display scale", min: 0.82, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.10, max: 0.01, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "StrongWeakLabel");

      const mat = document.createElement("div");
      mat.className = "strong-mat";
      mat.dataset.layoutItem = "scalloped-pink-mat";
      board.append(mat);
      const putDot = (left, top, width, height) => {
        const dot = document.createElement("div");
        dot.className = "strong-edge-dot";
        dot.style.left = left + "%";
        dot.style.top = top + "%";
        dot.style.width = width + "%";
        dot.style.height = height + "%";
        mat.append(dot);
      };
      for (let i = 0; i < 19; i += 1) {
        const centerX = (3.5 + i * 5.15 - 2.5) / .95;
        putDot(centerX - 1.75, -1.6, 3.5, 5.3);
        putDot(centerX - 1.75, 96.3, 3.5, 5.3);
      }
      for (let i = 0; i < 11; i += 1) {
        const centerY = (.09 + i * .082 - .025) / .95 * 100;
        putDot(-.2, centerY - 1.9, 2.55, 3.8);
        putDot(97.6, centerY - 1.9, 2.55, 3.8);
      }

      const card = document.createElement("div");
      card.className = "strong-card";
      card.dataset.layoutItem = "cobalt-specimen-panel";
      board.append(card);

      const addText = (text, cls, name, top, width, height, maxSize, minSize) => {
        const line = document.createElement("div");
        line.className = cls;
        line.dataset.layoutItem = name;
        line.dataset.displayItem = "true";
        line.textContent = text;
        if (top) line.style.top = top;
        board.append(line);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * width,
          height: board.clientHeight * height,
          maxSize: maxSize * state.scale,
          minSize,
          tracking: state.tracking,
        });
        line.style.letterSpacing = state.tracking + "em";
        return line;
      };

      const kicker = addText(props.kicker ?? state.kicker ?? "Youngtype Studio",
        "strong-kicker", "strongweak-kicker", "12%", .48, .075, 43, 16);
      kicker.style.letterSpacing = ".055em";
      addText(props.strongest ?? state.strongest ?? "Strongest",
        "strong-word strongest", "strongweak-strongest", null, .78, .255, 310, 54);
      addText(props.weakest ?? state.weakest ?? "Weakest",
        "strong-word weakest", "strongweak-weakest", null, .78, .275, 330, 54);

      for (const [key, cls, name, fallback] of [
        ["leftBadge", "strong-badge strong-badge-left", "strongweak-left-sticker", "Hand Drawn"],
        ["rightBadge", "strong-badge strong-badge-right", "strongweak-right-sticker", "Stroke Regular Outline"],
      ]) {
        const badge = document.createElement("div");
        badge.className = cls;
        badge.dataset.layoutItem = name;
        badge.textContent = String(props[key] ?? state[key] ?? fallback)
          .trim().split(/\s+/).slice(0, 3).join("\n");
        badge.style.whiteSpace = "pre-line";
        board.append(badge);
      }

      const footer = addText(props.footer ?? state.footer ?? "Organic Hand Drawn",
        "strong-footer", "strongweak-footer", "82.5%", .64, .09, 68, 22);
      footer.style.letterSpacing = ".015em";
    },
    getContrast() { return window.SupportLayout.contrast("#fff0e7", "#11488f"); },
    getWarnings() { return design.warnings || []; },
  };
  window.StrongWeak32 = design;
})();
