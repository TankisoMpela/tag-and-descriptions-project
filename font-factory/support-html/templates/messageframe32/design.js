(function () {
  const lines = [
    { text: "You Will Look Back", x: .12, width: .76 },
    { text: "On These Days And", x: .12, width: .76 },
    { text: "Be So Grateful You", x: .12, width: .76 },
    { text: "Made It Through", x: .18, width: .64 },
  ];
  const design = {
    id: "messageframe32",
    title: "Message frame",
    contrastException: {
      minimum: 2.5,
      rationale: "The source keeps its small white labels on a textured lavender print band.",
    },
    defaults: { scale: 1, top: .245, rowStep: .13, tracking: -.012 },
    controls: [
      { key: "scale", label: "Quote scale", min: .88, max: 1.12, step: .01 },
      { key: "top", label: "First line position", min: .235, max: .255, step: .001 },
      { key: "rowStep", label: "Line spacing", min: .124, max: .135, step: .001 },
      { key: "tracking", label: "Letter spacing", min: -.025, max: .005, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--quote-scale", String(props.scale ?? state.scale ?? 1));
      board.style.setProperty("--quote-top", String(props.top ?? state.top ?? .245));
      board.style.setProperty("--quote-step", String(props.rowStep ?? state.rowStep ?? .13));
      board.style.setProperty("--quote-tracking", String(props.tracking ?? state.tracking ?? -.012));
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "MessageFrameLabel, sans-serif");

      const plate = document.createElement("img");
      plate.className = "message-plate";
      plate.dataset.layoutItem = "source-message-card-and-print-plate";
      plate.src = "../../../support-references/materials/T30332_05-clean-message-plate.png";
      plate.alt = "";
      plate.draggable = false;
      board.append(plate);

      const lineElements = [];
      lines.forEach((item, index) => {
        const row = document.createElement("div");
        row.className = "quote-row";
        row.style.left = `${item.x * 100}%`;
        row.style.width = `${item.width * 100}%`;
        row.style.top = `${(Number(props.top ?? state.top ?? .245) + index * Number(props.rowStep ?? state.rowStep ?? .13)) * 100}%`;
        row.dataset.layoutItem = `quote-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "quote-line";
        line.dataset.layoutItem = `quote-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = item.text;
        lineElements.push(line);
        row.append(line);
        board.append(row);
      });

      const topLabel = document.createElement("span");
      topLabel.className = "message-label message-label-top";
      topLabel.dataset.layoutItem = "top-source-label";
      topLabel.textContent = "Field Notes";
      board.append(topLabel);

      const bottomLabel = document.createElement("span");
      bottomLabel.className = "message-label message-label-bottom";
      bottomLabel.dataset.layoutItem = "bottom-source-label";
      bottomLabel.textContent = "A Note To Keep";
      board.append(bottomLabel);

      const rowHeight = board.clientHeight * .125 * .96;
      window.SupportLayout.fitLinesTogether(lineElements, {
        width: board.clientWidth * .64 * .96,
        height: rowHeight,
        maxSize: board.clientHeight * .1725 * Number(props.scale ?? state.scale ?? 1),
        // Keep the four long reference lines together on both artboards. The
        // square frame is narrower, so a 7.2% floor made this quote fail its
        // own safe-width check with wide display faces.
        minSize: board.clientHeight * .06,
        tracking: Number(props.tracking ?? state.tracking ?? -.012),
        inkAware: true,
      });
      window.SupportLayout.fitLine(topLabel, {
        width: board.clientWidth * .26,
        height: board.clientHeight * .05,
        maxSize: board.clientHeight * .03,
        minSize: board.clientHeight * .015,
        tracking: .08,
        inkAware: true,
      });
      window.SupportLayout.fitLine(bottomLabel, {
        width: board.clientWidth * .20,
        height: board.clientHeight * .05,
        maxSize: board.clientHeight * .03,
        minSize: board.clientHeight * .015,
        tracking: .08,
        inkAware: true,
      });
    },
    getContrast() {
      return window.SupportLayout.contrast("#ffffff", "#827bda");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.MessageFrame32 = design;
})();
