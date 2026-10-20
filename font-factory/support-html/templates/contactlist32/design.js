(function () {
  const rows = [
    "01.Misread",
    "02.Cayman Island",
    "03.Homesick",
    "04.Boat Behind",
    "05.Rumours",
    "06.Renegade",
    "07.Summer on",
    "The Westhill",
  ];
  const design = {
    id: "contactlist32",
    title: "Pastel index board",
    defaults: {
      rows,
      scale: 1,
      rowStep: .091,
      top: .12,
      left: .12,
      width: .76,
      trackLabel: "Track List",
      numberLabel: "NO. 07",
    },
    controls: [
      { key: "scale", label: "Shared list scale", min: .88, max: 1.12, step: .01 },
      { key: "rowStep", label: "Row spacing", min: .088, max: .093, step: .001 },
      { key: "top", label: "First row position", min: .105, max: .135, step: .001 },
      { key: "left", label: "List column start", min: .105, max: .14, step: .005 },
      { key: "width", label: "List column width", min: .70, max: .80, step: .005 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();

      const scale = Number(props.scale ?? state.scale ?? 1);
      const rowStep = Number(props.rowStep ?? state.rowStep ?? .091);
      const top = Number(props.top ?? state.top ?? .12);
      const left = Number(props.left ?? state.left ?? .12);
      const width = Number(props.width ?? state.width ?? .76);
      const copy = props.rows ?? state.rows ?? rows;
      board.style.setProperty("--index-scale", String(scale));
      board.style.setProperty("--index-row-step", String(rowStep));
      board.style.setProperty("--index-top", String(top));
      board.style.setProperty("--index-left", `${left * 100}%`);
      board.style.setProperty("--index-width", `${width * 100}%`);
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "ContactListLabel, sans-serif");

      const plate = document.createElement("img");
      plate.className = "index-plate";
      plate.dataset.layoutItem = "clean-source-index-plate";
      plate.src = "../../../support-references/materials/T30332_06-clean-index-plate.png";
      plate.alt = "";
      plate.draggable = false;
      board.append(plate);

      const lineElements = [];
      copy.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "index-row";
        row.style.top = `${(top + index * rowStep) * 100}%`;
        row.dataset.layoutItem = `index-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "index-line";
        line.dataset.layoutItem = `index-copy-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        lineElements.push(line);
        row.append(line);
        board.append(row);
      });

      const track = document.createElement("span");
      track.className = "index-tab-label index-tab-label-track";
      track.dataset.layoutItem = "track-list-tab-label";
      track.textContent = String(props.trackLabel ?? state.trackLabel ?? "Track List");
      board.append(track);

      const number = document.createElement("span");
      number.className = "index-tab-label index-tab-label-number";
      number.dataset.layoutItem = "catalogue-number-tab-label";
      number.textContent = String(props.numberLabel ?? state.numberLabel ?? "NO. 07");
      board.append(number);

      const availableWidth = board.clientWidth * width * .965;
      const lineHeight = board.clientHeight * .07;
      window.SupportLayout.fitLinesTogether(lineElements, {
        width: availableWidth,
        height: lineHeight,
        maxSize: board.clientHeight * .072 * scale,
        minSize: board.clientHeight * .04,
        tracking: -.012,
        inkAware: true,
      });
      window.SupportLayout.fitLine(track, {
        width: board.clientWidth * .114,
        height: board.clientHeight * .035,
        maxSize: board.clientHeight * .0225,
        minSize: board.clientHeight * .012,
        tracking: .025,
        inkAware: true,
      });
      window.SupportLayout.fitLine(number, {
        width: board.clientWidth * .074,
        height: board.clientHeight * .026,
        maxSize: board.clientHeight * .021,
        minSize: board.clientHeight * .012,
        tracking: .025,
        inkAware: true,
      });
    },
    getContrast() {
      return window.SupportLayout.contrast("#1a293c", "#e7b5dd");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.ContactList32 = design;
})();
