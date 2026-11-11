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
    id: "numeralfolio32",
    title: "Numeral Folio",
    defaults: { scale: 1 },
    controls: [
      { key: "scale", label: "Numeral scale", min: .86, max: 1.08, step: .01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      const square = board.dataset.ratio === "1x1";
      board.classList.toggle("numeral-folio-square", square);
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Georgia, serif");

      const heading = document.createElement("div");
      heading.className = "folio-heading";
      heading.dataset.layoutItem = "numeral-folio-heading";
      heading.textContent = "Numeral Set";
      board.append(heading);

      const type = document.createElement("div");
      type.className = "folio-type";
      type.dataset.layoutItem = "numeral-folio-type";
      type.textContent = labelFor(props.fontType);
      board.append(type);

      const grid = document.createElement("div");
      grid.className = "folio-grid";
      grid.dataset.layoutItem = "numeral-folio-grid";
      for (const digit of "0123456789") {
        const cell = document.createElement("div");
        cell.className = "folio-digit-cell";
        const specimen = document.createElement("span");
        specimen.className = "folio-digit";
        specimen.dataset.layoutItem = `numeral-folio-digit-${digit}`;
        specimen.dataset.displayItem = "true";
        specimen.textContent = digit;
        cell.append(specimen);
        grid.append(cell);
        window.SupportLayout.fitLine(specimen, {
          width: board.clientWidth * (square ? .158 : .168),
          height: board.clientHeight * (square ? .205 : .235),
          maxSize: board.clientHeight * (square ? .28 : .33) * Number(state.scale || 1),
          minSize: board.clientHeight * .13,
          tracking: -.055,
        });
      }
      board.append(grid);

      const footer = document.createElement("div");
      footer.className = "folio-footer";
      footer.dataset.layoutItem = "numeral-folio-footer";
      footer.textContent = "Figures  /  Counting Forms  /  0–9";
      board.append(footer);

      const issue = document.createElement("div");
      issue.className = "folio-issue";
      issue.dataset.layoutItem = "numeral-folio-issue";
      issue.textContent = "Specimen 01";
      board.append(issue);
    },
    getContrast() { return window.SupportLayout.contrast("#101010", "#f3f0e9"); },
    getWarnings() { return design.warnings || []; },
  };
  window.NumeralFolio32 = design;
})();
