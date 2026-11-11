(function () {
  function labelFor(type) {
    const labels = {
      blackletter: "Blackletter", brush: "Brush", display: "Display",
      "display-bold": "Display", grotesk: "Sans Serif", hairline: "Hairline",
      mono: "Monospaced", pixel: "Pixel", script: "Script", serif: "Serif",
      swashy: "Swashy",
    };
    const key = String(type || "typeface").trim().toLowerCase();
    return labels[key] || key.replace(/[-_]+/gu, " ").replace(/\b\p{L}/gu,
      (letter) => letter.toUpperCase());
  }

  const design = {
    id: "timechange32",
    title: "Time Change",
    defaults: { scale: 1 },
    controls: [
      { key: "scale", label: "Display scale", min: .86, max: 1.08, step: .01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      const square = board.dataset.ratio === "1x1";
      board.classList.toggle("time-change-square", square);
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Georgia, serif");

      const leftLabel = document.createElement("div");
      leftLabel.className = "time-label time-label-left";
      leftLabel.dataset.layoutItem = "time-change-label-left";
      leftLabel.textContent = "Type Study";
      board.append(leftLabel);

      const typeLabel = document.createElement("div");
      typeLabel.className = "time-label time-label-right";
      typeLabel.dataset.layoutItem = "time-change-label-type";
      typeLabel.textContent = labelFor(props.fontType);
      board.append(typeLabel);

      const rows = [
        { key: "Time", name: "time-change-time", className: "time-word", top: square ? .12 : .095,
          height: square ? .22 : .255, width: .86, max: square ? .255 : .30 },
        { key: "Change", name: "time-change-change", className: "change-word", top: square ? .365 : .38,
          height: square ? .245 : .285, width: .91, max: square ? .29 : .34 },
        { key: "(380)", name: "time-change-number", className: "number-word", top: square ? .64 : .69,
          height: square ? .17 : .19, width: .74, max: square ? .21 : .24 },
      ];
      for (const row of rows) {
        const element = document.createElement("div");
        element.className = `time-display ${row.className}`;
        element.dataset.layoutItem = row.name;
        element.dataset.displayItem = "true";
        element.textContent = row.key;
        element.style.top = `${row.top * 100}%`;
        element.style.width = `${row.width * 100}%`;
        element.style.height = `${row.height * 100}%`;
        board.append(element);
        window.SupportLayout.fitLine(element, {
          width: board.clientWidth * row.width * .98,
          height: board.clientHeight * row.height * .9,
          maxSize: board.clientHeight * row.max * Number(state.scale || 1),
          minSize: board.clientHeight * .12,
          tracking: row.className === "number-word" ? -.055 : -.06,
        });
      }
    },
    getContrast() { return window.SupportLayout.contrast("#cbe4e7", "#090a0b"); },
    getWarnings() { return design.warnings || []; },
  };
  window.TimeChange32 = design;
})();
