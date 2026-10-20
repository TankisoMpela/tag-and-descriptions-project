(function () {
  const words = [
    "Diabolically",
    "Equalizing",
    "Revaluation",
    "Pandemic",
    "Submachine",
    "Challenger",
  ];
  const design = {
    id: "mountain32",
    title: "Mountain · six specimens",
    defaults: {
      scale: 1,
      artScale: 1,
      wordScale: 1,
      numberScale: 1,
      rowStep: .145,
      wordLeft: .455,
    },
    controls: [
      { key: "scale", label: "Specimen scale", min: .88, max: 1.08, step: .01 },
      { key: "artScale", label: "Illustration scale", min: .94, max: 1.04, step: .005 },
      { key: "wordScale", label: "Word width", min: .93, max: 1.03, step: .005 },
      { key: "numberScale", label: "Number size", min: .85, max: 1.15, step: .01 },
      { key: "rowStep", label: "Row spacing", min: .137, max: .15, step: .001 },
      { key: "wordLeft", label: "Word column start", min: .445, max: .465, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scale = Number(props.scale ?? state.scale ?? 1);
      const wordScale = Number(props.wordScale ?? state.wordScale ?? 1);
      board.style.setProperty("--mountain-ground", "#1b1b1b");
      board.style.setProperty("--mountain-paper", "#f4efe0");
      board.style.setProperty("--mountain-rule", "#e5decc");
      board.style.setProperty("--mountain-art-scale", String(props.artScale ?? state.artScale ?? 1));
      board.style.setProperty("--mountain-word-scale", String(wordScale));
      board.style.setProperty("--mountain-number-scale", String(props.numberScale ?? state.numberScale ?? 1));
      const rowStep = Number(props.rowStep ?? state.rowStep ?? .145);
      board.style.setProperty("--mountain-row-step", String(rowStep));
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "MountainLabel, sans-serif");

      const illustration = document.createElement("div");
      illustration.className = "mountain-illustration";
      illustration.dataset.layoutItem = "original-mountain-engraving";
      const image = document.createElement("img");
      image.src = "../../../support-references/originals/T33631_05-illustration.jpg";
      image.alt = "";
      image.draggable = false;
      illustration.append(image);
      board.append(illustration);

      const wordElements = [];
      words.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "mountain-row";
        row.style.setProperty("--row-index", String(index));
        row.style.top = `${6.5 + index * rowStep * 100}%`;
        row.dataset.layoutItem = `specimen-row-${index + 1}`;

        const number = document.createElement("span");
        number.className = "mountain-number";
        number.dataset.layoutItem = `row-number-${index + 1}`;
        number.style.left = `${((.405 - .39) / (.956 - .39)) * 100}%`;
        number.style.fontSize = `${board.clientHeight * .02875 * Number(props.numberScale ?? state.numberScale ?? 1)}px`;
        number.textContent = `${String(index + 1).padStart(2, "0")}.`;

        const word = document.createElement("span");
        word.className = "mountain-word";
        word.dataset.layoutItem = `specimen-word-${index + 1}`;
        word.dataset.displayItem = "true";
        const start = Number(props.wordLeft ?? state.wordLeft ?? .455);
        word.style.left = `${((start - .39) / (.956 - .39)) * 100}%`;
        word.style.width = `${((.956 - start) / (.956 - .39)) * 100}%`;
        word.textContent = text;
        wordElements.push(word);
        row.append(number, word);

        const rule = document.createElement("span");
        rule.className = "mountain-rule";
        rule.dataset.layoutItem = `row-rule-${index + 1}`;
        rule.setAttribute("aria-hidden", "true");
        row.append(rule);
        board.append(row);

      });
      const start = Number(props.wordLeft ?? state.wordLeft ?? .455);
      const rowWidth = board.clientWidth * (.956 - start);
      const rowHeight = board.clientHeight * .105;
      window.SupportLayout.fitLinesTogether(wordElements, {
        width: rowWidth * .94 / Math.max(1, wordScale),
        height: rowHeight * .96,
        maxSize: board.clientHeight * .155 * scale,
        minSize: board.clientHeight * .052,
        tracking: -.015,
        inkAware: true,
      });
    },
    getContrast() {
      return window.SupportLayout.contrast("#f4efe0", "#1b1b1b");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Mountain32 = design;
})();
