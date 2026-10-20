(function () {
  const paper = "#faf9ef";
  const ink = "#141414";
  const orange = "#e7651b";
  const muted = "#706d64";
  const lines = [
    { id: "alphabet-uppercase-0", className: "upper-0", text: "ABCDEFGHIJKLM", accent: [0, 12], max: 118, min: 38, tracking: -0.035 },
    { id: "alphabet-uppercase-1", className: "upper-1", text: "NOPQRSTUVWXYZ", accent: [8], max: 118, min: 38, tracking: -0.035 },
    { id: "alphabet-lowercase-0", className: "lower-0", text: "abcdefghijklm", accent: [0], max: 91, min: 36, tracking: -0.035 },
    { id: "alphabet-lowercase-1", className: "lower-1", text: "nopqrstuvwxyz", accent: [11], max: 91, min: 36, tracking: -0.035 },
    { id: "alphabet-figures", className: "figures", text: "#0123456789", accent: [3], max: 104, min: 36, tracking: -0.035 },
  ];

  function makeRow(spec) {
    const slot = document.createElement("div");
    slot.className = `alphabet-row ${spec.className}`;
    const row = document.createElement("span");
    row.className = "alphabet-run";
    row.dataset.layoutItem = spec.id;
    row.dataset.displayItem = "true";
    row.setAttribute("aria-label", spec.text);
    [...spec.text].forEach((character, index) => {
      const glyph = document.createElement("span");
      glyph.textContent = character;
      if (spec.accent.includes(index)) glyph.className = "accent";
      row.append(glyph);
    });
    slot.append(row);
    return { slot, row };
  }

  const design = {
    id: "alphabet32",
    title: "Alphabet specimen",
    defaults: { scale: 1, tracking: -0.035, paper, orange },
    controls: [
      { key: "scale", label: "Specimen scale", min: 0.78, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.08, max: 0, step: 0.005 },
      { key: "paper", label: "Paper", type: "color", value: paper },
      { key: "orange", label: "Accent ink", type: "color", value: orange },
    ],
    render(board, state) {
      board.replaceChildren();
      board.style.setProperty("--paper", state.paper);
      board.style.setProperty("--ink", ink);
      board.style.setProperty("--orange", state.orange);
      board.style.setProperty("--muted", muted);
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      for (const className of ["separator separator-upper", "separator separator-lower"]) {
        const rule = document.createElement("div");
        rule.className = className;
        rule.setAttribute("aria-hidden", "true");
        board.append(rule);
      }
      const descriptor = document.createElement("div");
      descriptor.className = "descriptor";
      descriptor.dataset.layoutItem = "alphabet-descriptor";
      descriptor.textContent = "Variable\nGeometric\nSans Serif";
      board.append(descriptor);
      for (const spec of lines) {
        const { slot, row } = makeRow(spec);
        board.append(slot);
        const width = board.clientWidth * (spec.className.startsWith("lower") ? 0.615 : spec.className === "figures" ? 0.62 : 0.89);
        const height = board.clientHeight * (spec.className.startsWith("upper") ? 0.12 : spec.className === "figures" ? 0.16 : 0.115);
        const size = window.SupportLayout.fitLine(row, {
          width,
          height,
          maxSize: spec.max * state.scale,
          minSize: spec.min,
          tracking: state.tracking,
        });
        row.style.letterSpacing = `${state.tracking}em`;
        row.dataset.fittedSize = String(size);
      }
      const maker = document.createElement("div");
      maker.className = "metadata metadata-primary";
      maker.dataset.layoutItem = "alphabet-metadata-primary";
      maker.textContent = "Letterform Study";
      board.append(maker);
      const kind = document.createElement("div");
      kind.className = "metadata metadata-secondary";
      kind.dataset.layoutItem = "alphabet-metadata-secondary";
      kind.textContent = "Glyph Specimen";
      board.append(kind);
    },
    getContrast() { return window.SupportLayout.contrast(ink, paper); },
  };
  window.Alphabet32 = design;
})();
