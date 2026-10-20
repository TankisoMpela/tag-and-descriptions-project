(function () {
  const leftWords = ["Covent", "Garden"];
  const bottomWords = ["Covent", "Garden"];
  const middleWords = ["Covent", "Garden"];
  const rightHeading = ["Covent", "Garden"];
  const rightCopy = ["Timeless", "Charm,", "Rooted In", "Grace."];

  function svgElement(tag) {
    return document.createElementNS("http://www.w3.org/2000/svg", tag);
  }

  function starPoints(points, outer, inner) {
    const coords = [];
    for (let i = 0; i < points * 2; i += 1) {
      const radius = i % 2 ? inner : outer;
      const angle = -Math.PI / 2 + i * Math.PI / points;
      coords.push(`${50 + Math.cos(angle) * radius},${50 + Math.sin(angle) * radius}`);
    }
    return coords.join(" ");
  }

  const design = {
    id: "phonegarden32",
    title: "Phone garden",
    defaults: { scale: 1, centerScale: 1, tracking: -.012, rightSpacing: .073 },
    controls: [
      { key: "scale", label: "Display type scale", min: .9, max: 1.08, step: .01 },
      { key: "centerScale", label: "Center lockup scale", min: .9, max: 1.08, step: .01 },
      { key: "tracking", label: "Display tracking", min: -.025, max: .005, step: .001 },
      { key: "rightSpacing", label: "Garden message spacing", min: .069, max: .077, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scene = document.createElement("div");
      scene.className = "phone-scene";
      board.append(scene);
      board = scene;
      const scale = Number(props.scale ?? state.scale ?? 1);
      const centerScale = Number(props.centerScale ?? state.centerScale ?? 1);
      const tracking = Number(props.tracking ?? state.tracking ?? -.035);
      const rightSpacing = Number(props.rightSpacing ?? state.rightSpacing ?? .073);
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "PhoneGardenLabel, sans-serif");

      const plate = document.createElement("img");
      plate.className = "phone-plate";
      plate.dataset.layoutItem = "source-three-phone-plate";
      plate.src = "../../../support-references/materials/T30332_08-clean-phone-plate-no-lettering.png";
      plate.alt = "";
      plate.draggable = false;
      board.append(plate);

      const flowerPatch = document.createElement("div");
      flowerPatch.className = "phone-flower-patch";
      flowerPatch.dataset.layoutItem = "cleaned-left-screen-area";
      board.append(flowerPatch);

      const peony = document.createElement("img");
      peony.className = "phone-peony";
      peony.dataset.layoutItem = "source-left-peony";
      peony.src = "../../../support-references/materials/T30332_08_left-peony-v2.png";
      peony.alt = "";
      peony.draggable = false;
      board.append(peony);

      const centerPatch = document.createElement("div");
      centerPatch.className = "phone-star-patch";
      centerPatch.dataset.layoutItem = "center-screen-star-cleanup";
      centerPatch.style.left = "56.5%";
      centerPatch.style.top = "19%";
      centerPatch.style.width = `${board.clientHeight * .15}px`;
      centerPatch.style.height = `${board.clientHeight * .15}px`;
      board.append(centerPatch);

      const leftPatch = document.createElement("div");
      leftPatch.className = "phone-star-patch";
      leftPatch.dataset.layoutItem = "left-screen-star-cleanup";
      leftPatch.style.left = "16.5%";
      leftPatch.style.top = "22.2%";
      leftPatch.style.width = `${board.clientHeight * .076}px`;
      leftPatch.style.height = `${board.clientHeight * .076}px`;
      board.append(leftPatch);

      const smallDot = document.createElement("span");
      smallDot.className = "phone-dot";
      smallDot.dataset.layoutItem = "left-screen-outline-dot";
      smallDot.style.left = `${board.clientWidth * (194 / 1184) - board.clientHeight * .0042}px`;
      smallDot.style.top = `${board.clientHeight * (598 / 792) - board.clientHeight * .0042}px`;
      smallDot.style.width = `${board.clientHeight * .0084}px`;
      smallDot.style.height = `${board.clientHeight * .0084}px`;
      board.append(smallDot);

      const labelElements = [];
      for (const [text, x, item] of [
        ["Field Notes", .336, "left-neutral-side-caption"],
        ["Flora / 08", .665, "right-neutral-side-caption"],
      ]) {
        const label = document.createElement("span");
        label.className = "phone-label phone-label-vertical";
        label.style.setProperty("--label-x", `${x * 100}%`);
        label.dataset.layoutItem = item;
        label.textContent = text;
        board.append(label);
        labelElements.push(label);
      }

      const leftLineElements = [];
      leftWords.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "phone-row";
        row.style.left = "6%";
        row.style.width = "22.5%";
        row.style.top = `${([.29, .43][index]) * 100}%`;
        row.style.height = "10%";
        row.dataset.layoutItem = `left-lockup-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "phone-type";
        line.style.letterSpacing = `${tracking}em`;
        line.dataset.layoutItem = `left-lockup-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        leftLineElements.push(line);
        row.append(line);
        board.append(row);
      });

      const leftBottomElements = [];
      bottomWords.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "phone-row";
        row.style.left = "5.5%";
        row.style.width = "23%";
        row.style.top = `${([.77, .85][index]) * 100}%`;
        row.style.height = "5.5%";
        row.dataset.layoutItem = `left-footer-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "phone-type";
        line.style.letterSpacing = `${tracking}em`;
        line.dataset.layoutItem = `left-footer-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        leftBottomElements.push(line);
        row.append(line);
        board.append(row);
      });

      const middleElements = [];
      middleWords.forEach((text, index) => {
        const line = document.createElement("span");
        line.className = "phone-type phone-vertical-type";
        line.style.setProperty("--center-x", `${([.415, .585][index]) * 100}%`);
        line.style.letterSpacing = `${tracking}em`;
        line.dataset.layoutItem = `center-lockup-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        middleElements.push(line);
        board.append(line);
      });

      const rightHeadingElements = [];
      rightHeading.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "phone-row phone-right-title";
        row.style.left = "71.5%";
        row.style.width = "25.5%";
        row.style.top = `${([.15, .225][index]) * 100}%`;
        row.style.height = "5.2%";
        row.dataset.layoutItem = `right-heading-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "phone-type phone-right-title";
        line.dataset.layoutItem = `right-heading-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        rightHeadingElements.push(line);
        row.append(line);
        board.append(row);
      });

      const rightCopyElements = [];
      rightCopy.forEach((text, index) => {
        const row = document.createElement("div");
        row.className = "phone-row phone-right-copy";
        row.style.left = "71.5%";
        row.style.width = "25.5%";
        row.style.top = `${(.6 + index * rightSpacing) * 100}%`;
        row.style.height = "6.6%";
        row.dataset.layoutItem = `right-message-row-${index + 1}`;

        const line = document.createElement("span");
        line.className = "phone-type phone-right-copy";
        line.dataset.layoutItem = `right-message-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        rightCopyElements.push(line);
        row.append(line);
        board.append(row);
      });

      function addStar(label, x, y, radius, points, inner, fill, stroke, strokeWidth) {
        const size = radius * 2 * board.clientHeight;
        const svg = svgElement("svg");
        svg.setAttribute("viewBox", "0 0 100 100");
        svg.setAttribute("aria-hidden", "true");
        svg.classList.add("phone-star");
        svg.dataset.layoutItem = label;
        svg.style.width = `${size}px`;
        svg.style.height = `${size}px`;
        svg.style.left = `${board.clientWidth * x - size / 2}px`;
        svg.style.top = `${board.clientHeight * y - size / 2}px`;
        const polygon = svgElement("polygon");
        polygon.setAttribute("points", starPoints(points, 47, 47 * inner));
        polygon.setAttribute("fill", fill);
        polygon.setAttribute("stroke", stroke);
        polygon.setAttribute("stroke-width", String(strokeWidth));
        polygon.setAttribute("stroke-linejoin", "round");
        svg.append(polygon);
        board.append(svg);
      }

      window.SupportLayout.fitLine(labelElements[0], {
        width: board.clientHeight * .20,
        height: board.clientHeight * .03,
        maxSize: board.clientHeight * .02,
        minSize: board.clientHeight * .009,
        tracking: .07,
        inkAware: true,
      });
      window.SupportLayout.fitLine(labelElements[1], {
        width: board.clientHeight * .18,
        height: board.clientHeight * .03,
        maxSize: board.clientHeight * .019,
        minSize: board.clientHeight * .009,
        tracking: .06,
        inkAware: true,
      });
      window.SupportLayout.fitLinesTogether(leftLineElements, {
        width: board.clientWidth * .225 * .96,
        height: board.clientHeight * .09 * .86,
        maxSize: board.clientHeight * .094 * scale,
        minSize: board.clientHeight * .028,
        tracking,
        inkAware: true,
      });
      window.SupportLayout.fitLinesTogether(leftBottomElements, {
        width: board.clientWidth * .23 * .96,
        height: board.clientHeight * .055 * .88,
        maxSize: board.clientHeight * .057 * scale,
        minSize: board.clientHeight * .022,
        tracking,
        inkAware: true,
      });
      window.SupportLayout.fitLinesTogether(middleElements, {
        width: board.clientHeight * .66 * .94,
        height: board.clientHeight * .15 * .88,
        maxSize: board.clientHeight * .13 * centerScale,
        minSize: board.clientHeight * .035,
        tracking,
        inkAware: true,
      });
      window.SupportLayout.fitLinesTogether(rightHeadingElements, {
        width: board.clientWidth * .255 * .94,
        height: board.clientHeight * .052 * .9,
        maxSize: board.clientHeight * .048 * scale,
        minSize: board.clientHeight * .022,
        tracking: -.04,
        inkAware: true,
      });
      window.SupportLayout.fitLinesTogether(rightCopyElements, {
        width: board.clientWidth * .255 * .94,
        height: board.clientHeight * .066 * .88,
        maxSize: board.clientHeight * .052 * scale,
        minSize: board.clientHeight * .022,
        tracking: -.025,
        inkAware: true,
      });

      addStar("left-lockup-star", .165, .222, .025, 5, .47,
        "none", "#eb63a4", 2.6);
      addStar("center-lockup-star", .565, .19, .062, 8, .42,
        "#fff297", "#1c3345", 1.2);
    },
    getContrast() {
      return window.SupportLayout.contrast("#0a0b0f", "#fdf5e5");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.PhoneGarden32 = design;
})();
