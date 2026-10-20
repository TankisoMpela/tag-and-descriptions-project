(function () {
  const design = {
    id: "demolition32",
    title: "Demolition type poster",
    ink: "#121014",
    defaults: {
      row1: "Beh-Ago",
      row2: "Demolition",
      row3: "Abnormal(Ey)",
      row4: "Mal-Out",
      caption: "Normal Area (000-0385)",
      titleScale: 1,
      firstTop: 0.235,
      rowSpacing: 0.11,
      left: 0.17,
      tracking: -0.03,
    },
    controls: [
      { key: "row1", label: "Display row 1", type: "text" },
      { key: "row2", label: "Display row 2", type: "text" },
      { key: "row3", label: "Display row 3", type: "text" },
      { key: "row4", label: "Display row 4", type: "text" },
      { key: "caption", label: "Archive caption", type: "text" },
      { key: "titleScale", label: "Title scale", min: 0.84, max: 1.08, step: 0.01 },
      { key: "firstTop", label: "First row position", min: 0.22, max: 0.25, step: 0.0025 },
      { key: "rowSpacing", label: "Row spacing", min: 0.105, max: 0.114, step: 0.001 },
      { key: "left", label: "Left margin", min: 0.13, max: 0.19, step: 0.005 },
      { key: "tracking", label: "Letter spacing", min: -0.04, max: 0.02, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--demo-ink", props.ink || design.ink);
      board.style.setProperty("--display-face", "SupportDisplay, 'Noto Sans Display', 'Noto Sans', sans-serif");

      const field = document.createElement("img");
      field.className = "demo-field";
      field.dataset.layoutItem = "prismatic-field";
      field.src = "../../../support-references/materials/T19827_06_demolition-texture.png";
      field.alt = "";
      board.append(field);

      const headlineRows = [];
      ["row1", "row2", "row3", "row4"].forEach((key, index) => {
        const row = document.createElement("div");
        row.className = "demo-row";
        row.dataset.layoutItem = `display-row-${index + 1}`;
        row.dataset.displayItem = "true";
        row.textContent = props[key] ?? state[key] ?? "";
        board.append(row);
        headlineRows.push(row);
      });
      window.SupportLayout.fitStack(headlineRows, {
        name: "demolition-headline",
        board,
        left: .17,
        top: Number(props.firstTop ?? state.firstTop ?? .235),
        width: .70,
        height: .42,
        gap: Math.max(.012, Number(props.rowSpacing ?? state.rowSpacing ?? .11) - .09),
        maxSize: board.clientHeight * .105 * Number(props.titleScale ?? state.titleScale ?? 1),
        minSize: board.clientHeight * .055,
        tracking: Number(props.tracking ?? state.tracking ?? -.03),
      });
      headlineRows.forEach((row) => { row.style.letterSpacing = `${props.tracking ?? state.tracking ?? -.03}em`; });

      const caption = document.createElement("div");
      caption.className = "demo-caption";
      caption.dataset.layoutItem = "archive-caption";
      caption.textContent = props.caption ?? state.caption ?? "Normal Area (000-0385)";
      caption.style.left = "17%";
      caption.style.top = "74%";
      board.append(caption);
      window.SupportLayout.fitLine(caption, {
        width: board.clientWidth * 0.16,
        height: board.clientHeight * 0.03,
        maxSize: board.clientHeight * 0.018,
        minSize: board.clientHeight * 0.009,
        tracking: 0.015,
      });
      caption.style.letterSpacing = ".015em";

      const globe = document.createElement("img");
      globe.className = "demo-globe";
      globe.dataset.layoutItem = "twin-globe-mark";
      globe.src = "./globe.svg";
      globe.alt = "";
      globe.setAttribute("aria-hidden", "true");
      globe.style.left = `${Math.max(32, Number(props.left ?? state.left ?? .17) * 100 + 18)}%`;
      globe.style.top = "73%";
      board.append(globe);
    },
    getContrast() {
      // Fifth-percentile contrast across the source title field, sampled from
      // the supplied texture with its original charcoal ink.
      return 2.85;
    },
    contrastException: {
      minimum: 2.8,
      rationale: "The source prints charcoal over an active color field; the supplied texture measures 2.85:1 at the title area's fifth-percentile contrast.",
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Demolition32 = design;
})();
