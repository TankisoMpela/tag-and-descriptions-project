(function () {
  const defaults = {
    line1: "People Hasten",
    line2: "To Judge",
    line3: "In Order",
    line4: "Not To Be",
    line5: "Judged",
    line6: "Themselves",
    scale: 1,
    tracking: -.026,
    portraitScale: 1,
    portraitX: 5,
  };
  const design = {
    id: "mirror32",
    title: "Mirror Quote",
    defaults,
    controls: [
      { key: "line1", label: "Quote · row 1", type: "text", value: defaults.line1 },
      { key: "line2", label: "Quote · row 2", type: "text", value: defaults.line2 },
      { key: "line3", label: "Quote · row 3", type: "text", value: defaults.line3 },
      { key: "line4", label: "Quote · row 4", type: "text", value: defaults.line4 },
      { key: "line5", label: "Quote · row 5", type: "text", value: defaults.line5 },
      { key: "line6", label: "Quote · row 6", type: "text", value: defaults.line6 },
      { key: "scale", label: "Quote scale", min: .82, max: 1.12, step: .01 },
      { key: "tracking", label: "Quote tracking", min: -.07, max: .005, step: .005 },
      { key: "portraitScale", label: "Portrait scale", min: .9, max: 1.12, step: .01 },
      { key: "portraitX", label: "Portrait left position", min: 3.5, max: 7.5, step: .1 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", 'SupportDisplay, "Bodoni MT", "Didot", Georgia, serif');

      const portrait = document.createElement("img");
      portrait.className = "mirror-portrait";
      portrait.dataset.layoutItem = "mirror-portrait";
      portrait.src = "../../../support-references/materials/T13692_mirror-portrait.png";
      portrait.alt = "";
      portrait.setAttribute("aria-hidden", "true");
      const portraitScale = Number(props.portraitScale ?? state.portraitScale ?? defaults.portraitScale);
      const portraitX = Number(props.portraitX ?? state.portraitX ?? defaults.portraitX);
      portrait.style.left = `${portraitX}%`;
      portrait.style.height = `${67 * portraitScale}%`;
      board.append(portrait);

      const scale = Number(props.scale ?? state.scale ?? defaults.scale);
      const tracking = Number(props.tracking ?? state.tracking ?? defaults.tracking);
      const quoteLines = [];
      const quoteRows = [];
      for (let index = 0; index < 6; index += 1) {
        const text = String(props[`line${index + 1}`] ?? state[`line${index + 1}`] ?? defaults[`line${index + 1}`]).trim();
        const row = document.createElement("div");
        row.className = "mirror-copy-row";
        row.dataset.layoutItem = `mirror-row-${index + 1}`;
        const quote = document.createElement("span");
        quote.className = "mirror-quote";
        quote.dataset.layoutItem = `mirror-quote-${index + 1}`;
        quote.dataset.displayItem = "true";
        quote.textContent = text;
        row.append(quote);
        board.append(row);
        quote.style.letterSpacing = `${tracking}em`;
        quoteLines.push(quote);
        quoteRows.push(row);
      }
      window.SupportLayout.fitStack(quoteLines, {
        name: "mirror-quote",
        containers: quoteRows,
        board,
        left: .385,
        top: .145,
        width: .565,
        height: .715,
        gap: .012,
        maxSize: board.clientHeight * .105 * scale,
        minSize: board.clientHeight * .045,
        tracking,
      });
    },
    getContrast() {
      return window.SupportLayout.contrast("#f6f4ef", "#050607");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Mirror32 = design;
})();
