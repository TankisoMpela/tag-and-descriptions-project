(function () {
  const headlines = ["Every", "Sunset Brings", "The Promise Of", "A New Day"];
  // The source puts progressively tighter lines into its lower half; the
  // Skia box positions had pushed rows three and four into the paper edge.
  const rowTops = [.305, .438, .588, .725];
  const rowHeights = [.132, .155, .155, .15];
  const design = {
    id: "sunsetpromise32",
    title: "Sunset promise",
    defaults: { scale: 1, artScale: 1, top: .305, lineSpacing: 0, tracking: -.012, outline: .006 },
    controls: [
      { key: "scale", label: "Headline scale", min: .88, max: 1.08, step: .01 },
      { key: "artScale", label: "Sunset artwork scale", min: .94, max: 1.06, step: .005 },
      { key: "top", label: "Headline position", min: .29, max: .32, step: .001 },
      { key: "lineSpacing", label: "Line spacing", min: -.008, max: .008, step: .001 },
      { key: "tracking", label: "Letter spacing", min: -.03, max: 0, step: .001 },
      { key: "outline", label: "Outline weight", min: .004, max: .01, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scale = Number(props.scale ?? state.scale ?? 1);
      const artScale = Number(props.artScale ?? state.artScale ?? 1);
      const top = Number(props.top ?? state.top ?? .305);
      const lineSpacing = Number(props.lineSpacing ?? state.lineSpacing ?? 0);
      const tracking = Number(props.tracking ?? state.tracking ?? -.012);
      const outline = Number(props.outline ?? state.outline ?? .006);
      board.style.setProperty("--sunset-art-scale", String(artScale));
      board.style.setProperty("--outline-width", `${outline}em`);
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "SunsetPromiseLabel, sans-serif");

      const plate = document.createElement("img");
      plate.className = "sunset-plate";
      plate.dataset.layoutItem = "source-lavender-floral-stock";
      plate.src = "../../../support-references/materials/T30332_07-clean-sunset-background.png";
      plate.alt = "";
      plate.draggable = false;
      board.append(plate);

      const art = document.createElement("img");
      art.className = "sunset-art";
      art.dataset.layoutItem = "source-pixel-sunset";
      art.src = "../../../support-references/materials/T30332_07_pixel-sunset-art.png";
      art.alt = "";
      art.draggable = false;
      board.append(art);

      const headerLeft = document.createElement("span");
      headerLeft.className = "sunset-label sunset-label-left";
      headerLeft.dataset.layoutItem = "left-poster-caption";
      headerLeft.textContent = "Field Notes";
      board.append(headerLeft);

      const headerRight = document.createElement("span");
      headerRight.className = "sunset-label sunset-label-right";
      headerRight.dataset.layoutItem = "right-poster-caption";
      headerRight.textContent = "Dusk / 07";
      board.append(headerRight);

      const lines = [];
      headlines.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "sunset-row";
        row.style.top = `${(top + (rowTops[index] - .305) + index * lineSpacing) * 100}%`;
        row.style.height = `${rowHeights[index] * 100}%`;
        row.dataset.layoutItem = `sunset-headline-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "sunset-line";
        line.dataset.layoutItem = `sunset-headline-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        lines.push(line);
        row.append(line);
        board.append(row);
      });

      window.SupportLayout.fitLine(headerLeft, {
        width: board.clientWidth * .16,
        height: board.clientHeight * .058,
        maxSize: board.clientHeight * .018,
        minSize: board.clientHeight * .009,
        tracking: .08,
        inkAware: true,
      });
      window.SupportLayout.fitLine(headerRight, {
        width: board.clientWidth * .12,
        height: board.clientHeight * .058,
        maxSize: board.clientHeight * .017,
        minSize: board.clientHeight * .009,
        tracking: .07,
        inkAware: true,
      });
      window.SupportLayout.fitLinesTogether(lines, {
        width: board.clientWidth * .80 * .96,
        height: board.clientHeight * .132 * .90,
        maxSize: board.clientHeight * .17 * scale,
        minSize: board.clientHeight * .035,
        tracking,
        inkAware: true,
      });
    },
    contrastException: {
      minimum: 2.5,
      rationale: "The source overlays white outlined display lettering on its lavender textured stock.",
    },
    getContrast() {
      return window.SupportLayout.contrast("#ffffff", "#766ed0");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.SunsetPromise32 = design;
})();
