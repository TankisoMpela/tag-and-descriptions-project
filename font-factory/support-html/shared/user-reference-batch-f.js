(function () {
  const platePath = "../../../support-references/materials/reference-batch-2026-10-26-d/T20482_01-background-3x2.png";

  function createGoodTimeRoll() {
    const config = {
      title: "Good Times roller-skate poster",
      lineOne: "Let the Good",
      lineTwo: "Times Roll!",
    };
    const design = {
      id: "goodtimeroll32",
      title: config.title,
      literalKeys: ["lineOne", "lineTwo"],
      defaults: {
        lineOne: config.lineOne,
        lineTwo: config.lineTwo,
        displayScale: 1,
      },
      controls: [
        { key: "lineOne", type: "text", label: "Poster line one" },
        { key: "lineTwo", type: "text", label: "Poster line two" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-goodtimeroll");
        board.replaceChildren();

        const plate = document.createElement("img");
        plate.className = "gtr-plate";
        plate.dataset.layoutItem = "goodtimeroll32-photo-plate";
        plate.src = platePath;
        plate.alt = "";
        plate.draggable = false;
        board.append(plate);

        const lineSpecs = square
          ? [
              { key: "lineOne", top: 48, width: 92, height: 15 },
              { key: "lineTwo", top: 65, width: 90, height: 17 },
            ]
          : [
              { key: "lineOne", top: 39, width: 86, height: 16 },
              { key: "lineTwo", top: 59, width: 84, height: 18 },
            ];
        for (const spec of lineSpecs) {
          const line = document.createElement("div");
          line.className = `gtr-line gtr-${spec.key}`;
          line.style.top = `${spec.top}%`;
          line.style.width = `${spec.width}%`;
          line.style.height = `${spec.height}%`;
          line.textContent = String(state[spec.key] ?? config[spec.key]);
          line.dataset.layoutItem = `goodtimeroll32-${spec.key}`;
          line.dataset.displayItem = "true";
          board.append(line);
          window.SupportLayout.fitLine(line, {
            width: board.clientWidth * spec.width / 100,
            height: board.clientHeight * spec.height / 100,
            maxSize: board.clientHeight * (square ? .155 : .17) * scale,
            minSize: 38,
            tracking: -.035,
          });
        }
      },
      getContrast() {
        return window.SupportLayout.contrast("#ffffff", "#302820");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  window.UserReferenceBatchF = {
    ids: ["goodtimeroll32"],
    create(id) {
      if (id !== "goodtimeroll32") throw new Error(`Unknown reference template: ${id}`);
      return createGoodTimeRoll();
    },
  };
})();
