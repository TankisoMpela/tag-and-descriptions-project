(function () {
  const headlines = ["Wander Where", "Your Soul Feels Wild."];
  const design = {
    id: "cliffpostcard32",
    title: "Coastal postcard",
    defaults: { scale: 1, top: .195, gap: .14, tracking: -.02 },
    controls: [
      { key: "scale", label: "Headline scale", min: .86, max: 1.12, step: .01 },
      { key: "top", label: "Headline position", min: .18, max: .21, step: .001 },
      { key: "gap", label: "Line spacing", min: .13, max: .15, step: .001 },
      { key: "tracking", label: "Letter spacing", min: -.04, max: 0, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scale = Number(props.scale ?? state.scale ?? 1);
      const top = Number(props.top ?? state.top ?? .195);
      const gap = Number(props.gap ?? state.gap ?? .14);
      const tracking = Number(props.tracking ?? state.tracking ?? -.02);
      board.style.setProperty("--postcard-scale", String(scale));
      board.style.setProperty("--postcard-top", String(top));
      board.style.setProperty("--postcard-gap", String(gap));
      board.style.setProperty("--postcard-tracking", String(tracking));
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "CliffPostcardLabel, sans-serif");

      const plate = document.createElement("img");
      plate.className = "postcard-plate";
      plate.dataset.layoutItem = "source-torn-paper-and-coastal-photo";
      plate.src = "../../../support-references/materials/T30332_02-clean-postcard-background.png";
      plate.alt = "";
      plate.draggable = false;
      board.append(plate);

      const lineElements = [];
      const positions = [
        { left: .13, width: .74 },
        { left: .075, width: .85 },
      ];
      headlines.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "postcard-row";
        row.style.left = `${positions[index].left * 100}%`;
        row.style.width = `${positions[index].width * 100}%`;
        row.style.top = `${(top + index * gap) * 100}%`;
        row.dataset.layoutItem = `postcard-headline-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "postcard-line";
        line.dataset.layoutItem = `postcard-headline-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        lineElements.push(line);
        row.append(line);
        board.append(row);
      });

      const leftCaption = document.createElement("span");
      leftCaption.className = "postcard-caption postcard-caption-left";
      leftCaption.dataset.layoutItem = "left-postcard-caption";
      leftCaption.textContent = "Open Air / Study 02";
      board.append(leftCaption);

      const rightCaption = document.createElement("span");
      rightCaption.className = "postcard-caption postcard-caption-right";
      rightCaption.dataset.layoutItem = "right-postcard-caption";
      rightCaption.textContent = "Land / Sea / Sky";
      board.append(rightCaption);

      window.SupportLayout.fitLinesTogether(lineElements, {
        width: board.clientWidth * .74 * .96,
        height: board.clientHeight * .13 * .92,
        maxSize: board.clientHeight * .235 * scale,
        minSize: board.clientHeight * .068,
        tracking,
        inkAware: true,
      });
      window.SupportLayout.fitLine(leftCaption, {
        width: board.clientWidth * .36,
        height: board.clientHeight * .06,
        maxSize: board.clientHeight * .03,
        minSize: board.clientHeight * .012,
        tracking: .10,
        inkAware: true,
      });
      window.SupportLayout.fitLine(rightCaption, {
        width: board.clientWidth * .35,
        height: board.clientHeight * .06,
        maxSize: board.clientHeight * .03,
        minSize: board.clientHeight * .012,
        tracking: .10,
        inkAware: true,
      });
    },
    getContrast() {
      return window.SupportLayout.contrast("#0c0f12", "#cbdce3");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.CliffPostcard32 = design;
})();
