(function () {
  const design = {
    id: "yearposter32",
    title: "Year poster",
    defaults: { year: "1982", scale: 1, tracking: -0.06 },
    controls: [
      { key: "year", label: "Year", type: "text", value: "1982" },
      { key: "scale", label: "Numeral scale", min: 0.78, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Numeral spacing", min: -0.12, max: 0.01, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");

      const year = document.createElement("div");
      year.className = "year-run";
      year.dataset.layoutItem = "year-numerals";
      const digits = Array.from(String(props.year ?? state.year ?? "1982").replace(/\s+/gu, ""));
      const fittedDigits = digits.length ? digits : ["1", "9", "8", "2"];
      fittedDigits.forEach((digit, index) => {
        const cell = document.createElement("span");
        cell.className = "year-digit";
        cell.dataset.layoutItem = `year-digit-${index + 1}`;
        cell.dataset.displayItem = "true";
        cell.textContent = digit;
        year.append(cell);
      });
      board.append(year);
      const gap = fittedDigits.length === 4 ? .014 : .004;
      year.style.gridTemplateColumns = `repeat(${fittedDigits.length}, minmax(0, 1fr))`;
      year.style.columnGap = `${gap * 100}%`;
      window.SupportLayout.fitLinesTogether([...year.children], {
        width: board.clientWidth * ((.96 - gap * (fittedDigits.length - 1)) / fittedDigits.length) * .94,
        height: board.clientHeight * .70,
        maxSize: board.clientHeight * .76 * state.scale,
        minSize: board.clientHeight * .14,
        tracking: state.tracking,
      });

      const labels = [
        ["year-top-left", "Type Study / Edition 82"],
        ["year-top-right", "A Distressed Display Face"],
        ["year-bottom-left", "Printed Form / Archive"],
        ["year-bottom-right", "Series No. 04"],
      ];
      for (const [className, text] of labels) {
        const label = document.createElement("div");
        label.className = `year-furniture ${className}`;
        label.textContent = text;
        board.append(label);
      }
      const license = document.createElement("div");
      license.className = "year-furniture year-license";
      license.textContent = "Personal & Commercial Type Specimen / Print Series";
      board.append(license);
      const seal = document.createElement("div");
      seal.className = "year-seal";
      seal.setAttribute("aria-hidden", "true");
      seal.innerHTML = "<span>Y</span>";
      board.append(seal);
    },
    getContrast() { return window.SupportLayout.contrast("#fff1dc", "#bd2028"); },
    getWarnings() { return design.warnings || []; },
  };
  window.YearPoster32 = design;
})();
