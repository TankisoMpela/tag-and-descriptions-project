(function () {
  const source = "../../../support-references/originals/reference-batch-2026-10-26-d/T35520_03.webp";
  const lineKeys = [
    "coolLineOne", "coolLineTwo", "coolLineThree",
    "giveLineOne", "giveLineTwo",
    "hireLineOne", "hireLineTwo",
    "brandsLineOne", "brandsLineTwo", "brandsLineThree",
    "familyLabel",
  ];
  const config = {
    title: "Bold Campaign color-grid specimen",
    coolLineOne: "Cool Sh*t",
    coolLineTwo: "We've Done",
    coolLineThree: "This Week",
    giveLineOne: "GIVE",
    giveLineTwo: "AWAY",
    hireLineOne: "We're",
    hireLineTwo: "HIRING",
    brandsLineOne: "8 Brands",
    brandsLineTwo: "Killin' it",
    brandsLineThree: "Right Now",
    familyLabel: "Family Name",
  };
  const panels = [
    {
      className: "bc-panel-one",
      left: 9.9, top: 6.2, width: 39.6, height: 42.2,
      keys: ["coolLineOne", "coolLineTwo", "coolLineThree"],
      tops: [10, 38, 66],
    },
    {
      className: "bc-panel-two",
      left: 51.9, top: 6.2, width: 39.6, height: 42.2,
      keys: ["giveLineOne", "giveLineTwo"],
      tops: [18, 52],
    },
    {
      className: "bc-panel-three",
      left: 9.9, top: 52.5, width: 39.6, height: 42.2,
      keys: ["hireLineOne", "hireLineTwo"],
      tops: [18, 52],
    },
    {
      className: "bc-panel-four",
      left: 51.9, top: 52.5, width: 39.6, height: 42.2,
      keys: ["brandsLineOne", "brandsLineTwo", "brandsLineThree"],
      tops: [10, 38, 66],
    },
  ];

  function createBoldCampaign() {
    const design = {
      id: "boldcampaign32",
      title: config.title,
      literalKeys: lineKeys,
      defaults: {
        ...Object.fromEntries(lineKeys.map((key) => [key, config[key]])),
        displayScale: 1,
      },
      controls: [
        { key: "coolLineOne", type: "text", label: "Panel 1 · top line" },
        { key: "coolLineTwo", type: "text", label: "Panel 1 · middle line" },
        { key: "coolLineThree", type: "text", label: "Panel 1 · lower line" },
        { key: "giveLineOne", type: "text", label: "Panel 2 · top line" },
        { key: "giveLineTwo", type: "text", label: "Panel 2 · lower line" },
        { key: "hireLineOne", type: "text", label: "Panel 3 · top line" },
        { key: "hireLineTwo", type: "text", label: "Panel 3 · lower line" },
        { key: "brandsLineOne", type: "text", label: "Panel 4 · top line" },
        { key: "brandsLineTwo", type: "text", label: "Panel 4 · middle line" },
        { key: "brandsLineThree", type: "text", label: "Panel 4 · lower line" },
        { key: "familyLabel", type: "text", label: "Vertical family label" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-boldcampaign");
        board.replaceChildren();

        const plate = document.createElement("img");
        plate.className = "bc-plate";
        plate.dataset.layoutItem = "boldcampaign32-source-plate";
        plate.src = source;
        plate.alt = "";
        plate.draggable = false;
        board.append(plate);

        for (let panelIndex = 0; panelIndex < panels.length; panelIndex += 1) {
          const spec = panels[panelIndex];
          const panel = document.createElement("div");
          panel.className = `bc-panel ${spec.className}`;
          panel.style.left = `${spec.left}%`;
          panel.style.top = `${spec.top}%`;
          panel.style.width = `${spec.width}%`;
          panel.style.height = `${spec.height}%`;
          panel.dataset.layoutItem = `boldcampaign32-panel-${panelIndex + 1}`;
          board.append(panel);

          const lineHeight = spec.keys.length === 2 ? 29 : 22;
          const lineWidth = panelIndex === 3 ? 82 : 85;
          const lineLeft = 4;
          for (let lineIndex = 0; lineIndex < spec.keys.length; lineIndex += 1) {
            const key = spec.keys[lineIndex];
            const line = document.createElement("div");
            line.className = `bc-line bc-line-${lineIndex + 1}`;
            if ((panelIndex === 1 && lineIndex === 1) ||
                (panelIndex === 2 && lineIndex === 1)) {
              line.classList.add("bc-underlined");
            }
            line.style.left = `${lineLeft}%`;
            line.style.top = `${spec.tops[lineIndex]}%`;
            line.style.width = `${lineWidth}%`;
            line.style.height = `${lineHeight}%`;
            line.textContent = String(state[key] ?? config[key]);
            line.dataset.layoutItem = `boldcampaign32-${key}`;
            line.dataset.displayItem = "true";
            panel.append(line);
            window.SupportLayout.fitLine(line, {
              width: board.clientWidth * spec.width / 100 * lineWidth / 100,
              height: board.clientHeight * spec.height / 100 * lineHeight / 100,
              maxSize: board.clientHeight * (spec.keys.length === 2 ? .145 : .115) * scale,
              minSize: 38,
              tracking: -.025,
            });
          }

          const label = document.createElement("div");
          label.className = "bc-family-label";
          label.textContent = String(state.familyLabel ?? config.familyLabel);
          label.dataset.layoutItem = `boldcampaign32-family-label-${panelIndex + 1}`;
          panel.append(label);
          const labelMax = Math.min(12, board.clientHeight * .018,
            board.clientHeight * spec.height / 100 * .7 /
              Math.max(1, label.textContent.length));
          label.style.fontSize = `${Math.max(8, labelMax)}px`;
        }
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#e6ee47", "#2e02b5"),
          window.SupportLayout.contrast("#3b16a8", "#f3f66e"),
          window.SupportLayout.contrast("#3715a4", "#42e5f5"),
          window.SupportLayout.contrast("#49dff2", "#691bc5"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  window.UserReferenceBatchE = {
    ids: ["boldcampaign32"],
    create(id) {
      if (id !== "boldcampaign32") throw new Error(`Unknown reference template: ${id}`);
      return createBoldCampaign();
    },
  };
})();
