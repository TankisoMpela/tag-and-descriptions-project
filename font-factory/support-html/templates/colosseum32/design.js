(function () {
  const defaults = {
    lineOne: "Colosseum",
    lineTwo: "Gröngöling",
    lineThree: "Antarctica",
    tagline: "Distinctive Display Typeface",
    url: "Designed For Bold Headlines",
    scale: 1,
    tracking: .01,
    rowGap: 1,
    paper: "#f1eddf",
    navy: "#12387e",
    red: "#ea0003",
  };
  const design = {
    id: "colosseum32",
    title: "Colosseum",
    labelFace: "ColosseumLabel",
    defaults,
    contrastException: {
      minimum: 3.0,
      rationale: "The source uses saturated scarlet ink for both oversized specimen lettering and small publisher marks.",
    },
    controls: [
      { key: "lineOne", label: "Navy specimen", type: "text", value: defaults.lineOne },
      { key: "lineTwo", label: "Red specimen", type: "text", value: defaults.lineTwo },
      { key: "lineThree", label: "Navy specimen", type: "text", value: defaults.lineThree },
      { key: "tagline", label: "Publisher line", type: "text", value: defaults.tagline },
      { key: "url", label: "Publisher URL", type: "text", value: defaults.url },
      { key: "scale", label: "Specimen scale", min: .86, max: 1.12, step: .01 },
      { key: "tracking", label: "Letter spacing", min: -.09, max: .05, step: .005 },
      { key: "rowGap", label: "Row spacing", min: .86, max: 1.16, step: .01 },
      { key: "paper", label: "Paper", type: "color", value: defaults.paper },
      { key: "navy", label: "Navy ink", type: "color", value: defaults.navy },
      { key: "red", label: "Red ink", type: "color", value: defaults.red },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "ColosseumLabel");
      board.style.setProperty("--paper", props.paper ?? state.paper);
      board.style.setProperty("--navy", props.navy ?? state.navy);
      board.style.setProperty("--red", props.red ?? state.red);

      const add = (tag, className, name, parent = board) => {
        const node = document.createElement(tag);
        node.className = className;
        node.dataset.layoutItem = name;
        parent.append(node);
        return node;
      };
      const scale = Number(props.scale ?? state.scale);
      const tracking = Number(props.tracking ?? state.tracking);
      const rowGap = Number(props.rowGap ?? state.rowGap);
      const square = board.dataset.ratio === "1x1";
      const rows = square ? [
        { key: "lineOne", fallback: defaults.lineOne, name: "colosseum-first-specimen", className: "specimen-word specimen-one", width: .88, height: .18, max: .205, top: 9.5 },
        { key: "lineTwo", fallback: defaults.lineTwo, name: "colosseum-second-specimen", className: "specimen-word specimen-two", width: .88, height: .20, max: .225, top: 36.5 },
        { key: "lineThree", fallback: defaults.lineThree, name: "colosseum-third-specimen", className: "specimen-word specimen-three", width: .88, height: .18, max: .205, top: 64 },
      ] : [
        { key: "lineOne", fallback: defaults.lineOne, name: "colosseum-first-specimen", className: "specimen-word specimen-one", width: .72, height: .185, max: .205, top: 12.93 },
        { key: "lineTwo", fallback: defaults.lineTwo, name: "colosseum-second-specimen", className: "specimen-word specimen-two", width: .74, height: .23, max: .235, top: 35.9 },
        { key: "lineThree", fallback: defaults.lineThree, name: "colosseum-third-specimen", className: "specimen-word specimen-three", width: .72, height: .185, max: .20, top: 61 },
      ];
      rows.forEach((row, index) => {
        const line = add("div", row.className, row.name);
        line.textContent = props[row.key] ?? state[row.key] ?? row.fallback;
        line.dataset.copyText = line.textContent;
        line.dataset.displayItem = "true";
        const shiftedTop = row.top + (index - 1) * (rowGap - 1) * 6.5;
        line.style.top = `${shiftedTop}%`;
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * row.width,
          height: board.clientHeight * row.height,
          maxSize: board.clientHeight * row.max * scale,
          minSize: board.clientHeight * (square ? .055 : .075),
          tracking,
          inkAware: true,
        });
        line.style.letterSpacing = `${tracking}em`;
      });

      const footer = add("div", "publisher-footer", "colosseum-publisher-footer");
      const copy = add("div", "publisher-copy", "colosseum-publisher-copy", footer);
      const tagline = add("div", "publisher-tagline", "colosseum-publisher-tagline", copy);
      tagline.textContent = props.tagline ?? state.tagline ?? defaults.tagline;
      window.SupportLayout.fitLine(tagline, {
        width: board.clientWidth * .342, height: board.clientHeight * .026,
        maxSize: board.clientHeight * .022, minSize: board.clientHeight * .012,
        tracking: .005, inkAware: true,
      });
      const url = add("div", "publisher-url", "colosseum-publisher-url", copy);
      url.textContent = props.url ?? state.url ?? defaults.url;
      window.SupportLayout.fitLine(url, {
        width: board.clientWidth * .342, height: board.clientHeight * .018,
        maxSize: board.clientHeight * .014, minSize: board.clientHeight * .009,
        tracking: .03, inkAware: true,
      });

    },
    getContrast() {
      const paper = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--paper").trim();
      const navy = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--navy").trim();
      const red = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--red").trim();
      return Math.min(window.SupportLayout.contrast(navy, paper),
        window.SupportLayout.contrast(red, paper));
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Colosseum32 = design;
})();
