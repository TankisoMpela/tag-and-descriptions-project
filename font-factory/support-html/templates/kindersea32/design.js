(function () {
  const headlines = ["I Wish You", "A Kinder Sea."];
  const design = {
    id: "kindersea32",
    title: "Kinder sea postcard",
    defaults: { scale: 1, artScale: 1, top: .648, rowStep: .15, tracking: -.012 },
    controls: [
      { key: "scale", label: "Headline scale", min: .88, max: 1.08, step: .01 },
      { key: "artScale", label: "Seascape scale", min: .96, max: 1.04, step: .005 },
      { key: "top", label: "Headline position", min: .635, max: .665, step: .001 },
      { key: "rowStep", label: "Line spacing", min: .142, max: .158, step: .001 },
      { key: "tracking", label: "Letter spacing", min: -.04, max: .01, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scale = Number(props.scale ?? state.scale ?? 1);
      const artScale = Number(props.artScale ?? state.artScale ?? 1);
      const top = Number(props.top ?? state.top ?? .648);
      const rowStep = Number(props.rowStep ?? state.rowStep ?? .15);
      const tracking = Number(props.tracking ?? state.tracking ?? -.012);
      board.style.setProperty("--art-scale", String(artScale));
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "KinderSeaLabel, sans-serif");

      const plate = document.createElement("img");
      plate.className = "kinder-plate";
      plate.dataset.layoutItem = "source-lavender-stock";
      plate.src = "../../../support-references/materials/T30332_04-clean-lavender-plate.png";
      plate.alt = "";
      plate.draggable = false;
      board.append(plate);

      const illustration = document.createElement("img");
      illustration.className = "kinder-art";
      illustration.dataset.layoutItem = "source-pixel-seascape";
      illustration.src = "../../../support-references/materials/T30332_04_pixel-sea-art.png";
      illustration.alt = "";
      illustration.draggable = false;
      board.append(illustration);

      const stars = document.createElement("img");
      stars.className = "kinder-stars";
      stars.dataset.layoutItem = "source-corner-stars";
      stars.src = "../../../support-references/materials/T30332_04_corner-stars.png";
      stars.alt = "";
      stars.draggable = false;
      board.append(stars);

      const topLabel = document.createElement("span");
      topLabel.className = "kinder-label kinder-label-top";
      topLabel.dataset.layoutItem = "top-postcard-caption";
      topLabel.textContent = "Field Notes";
      board.append(topLabel);

      const sideLabel = document.createElement("span");
      sideLabel.className = "kinder-label kinder-label-side";
      sideLabel.dataset.layoutItem = "vertical-postcard-caption";
      sideLabel.textContent = "Postcard";
      board.append(sideLabel);

      const lines = [];
      headlines.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "kinder-row";
        row.style.left = `${(index === 0 ? .145 : .095) * 100}%`;
        row.style.width = `${(index === 0 ? .71 : .81) * 100}%`;
        row.style.top = `${(top + index * rowStep) * 100}%`;
        row.dataset.layoutItem = `headline-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "kinder-line";
        line.dataset.layoutItem = `headline-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        lines.push(line);
        row.append(line);
        board.append(row);
      });

      window.SupportLayout.fitLine(topLabel, {
        width: board.clientWidth * .30,
        height: board.clientHeight * .045,
        maxSize: board.clientHeight * .0275,
        minSize: board.clientHeight * .0175,
        tracking: .08,
        inkAware: true,
      });
      window.SupportLayout.fitLine(sideLabel, {
        width: board.clientHeight * .22,
        height: board.clientHeight * .03,
        maxSize: board.clientHeight * .025,
        minSize: board.clientHeight * .016,
        tracking: .1,
        inkAware: true,
      });
      window.SupportLayout.fitLinesTogether(lines, {
        width: board.clientWidth * .71 * .96,
        height: board.clientHeight * .13 * .90,
        maxSize: board.clientHeight * .140625 * scale,
        minSize: board.clientHeight * .0425,
        tracking,
        inkAware: true,
      });
    },
    contrastException: {
      minimum: 2.5,
      rationale: "Source white lettering on textured lavender intentionally follows the reference postcard treatment.",
    },
    getContrast() {
      return window.SupportLayout.contrast("#ffffff", "#726dcb");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.KinderSea32 = design;
})();
