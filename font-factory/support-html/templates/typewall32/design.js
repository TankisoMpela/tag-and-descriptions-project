(function () {
  const rowDefaults = [
    "Classic Culture",
    "Musical Synchrony",
    "Cargo Manual",
    "Magical Unicorns",
    "Practical Pony",
    "Bright Zenith",
    "Culture In Motion",
    "Lovely People",
  ];
  const defaults = {
    ...Object.fromEntries(rowDefaults.map((value, index) => ["row" + (index + 1), value])),
    scale: 1,
    rotation: -8,
    spacing: 15.2,
    stagger: 7,
  };
  const design = {
    id: "typewall32",
    title: "Typewall",
    defaults,
    controls: [
      ...rowDefaults.map((value, index) => ({
        key: "row" + (index + 1), label: "Specimen row " + (index + 1), type: "text", value,
      })),
      { key: "scale", label: "Type scale", min: 0.82, max: 1.08, step: 0.01 },
      { key: "rotation", label: "Field angle", min: -12, max: -3, step: 0.1 },
      { key: "spacing", label: "Row spacing", min: 14.2, max: 17.0, step: 0.1 },
      { key: "stagger", label: "Horizontal rhythm", min: 0, max: 14, step: 0.5 },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      const viewport = document.createElement("div");
      viewport.className = "typewall-viewport";
      viewport.dataset.layoutItem = "typewall-composition-viewport";
      viewport.dataset.displayItem = "true";
      viewport.setAttribute("aria-label", "Cropped eight-row type specimen surface");
      board.append(viewport);
      const field = document.createElement("div");
      field.className = "typewall-field";
      field.style.setProperty("--wall-rotation", (props.rotation ?? state.rotation) + "deg");
      field.style.setProperty("--wall-scale", String(props.scale ?? state.scale));
      viewport.append(field);
      const rows = props.rows || [];
      const topStart = -7.4;
      const spacing = Number(props.spacing ?? state.spacing);
      const stagger = Number(props.stagger ?? state.stagger);
      let largestText = 0;
      rowDefaults.forEach((fallback, index) => {
        const row = document.createElement("div");
        row.className = "typewall-row";
        row.style.top = (topStart + index * spacing) + "%";
        row.style.left = (-1 + ((index % 3) - 1) * stagger) + "%";
        field.append(row);
        const line = document.createElement("span");
        const key = "row" + (index + 1);
        line.textContent = props[key] ?? rows[index] ?? state[key] ?? fallback;
        row.append(line);
        largestText = Math.max(largestText, window.SupportLayout.fitLine(line, {
          width: board.clientWidth * .82,
          height: board.clientHeight * .15,
          maxSize: board.clientHeight * .17 * Number(props.scale ?? state.scale),
          minSize: board.clientHeight * .075,
          tracking: .005,
        }));
        line.style.letterSpacing = ".005em";
        const phraseWidth = Math.max(1, line.getBoundingClientRect().width);
        const repeats = Math.max(2, Math.min(7, Math.ceil(board.clientWidth * 1.9 / phraseWidth)));
        for (let copy = 1; copy < repeats; copy += 1) {
          const repeat = document.createElement("span");
          repeat.textContent = line.textContent;
          repeat.style.fontSize = line.style.fontSize;
          repeat.style.letterSpacing = line.style.letterSpacing;
          row.append(repeat);
        }
      });
      viewport.style.fontSize = largestText + "px";
    },
    getContrast() { return window.SupportLayout.contrast("#1b1815", "#ffe200"); },
    getWarnings() { return design.warnings || []; },
  };
  window.Typewall32 = design;
})();
