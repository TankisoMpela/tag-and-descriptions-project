(function () {
  const defaults = {
    headline: "Herbals",
    productName: "Arabica Whole Beans Coffee",
    batch: "1969",
    badge: "New",
    process: "Process : Natural\nNet Weight : 12 OZ",
    roast: "Medium Roast",
    date: "Roast Date\n27 June 2024",
    scale: 1,
    tracking: -.018,
    detailScale: 1,
    green: "#19b722",
    cream: "#faf0d5",
    ink: "#2a211f",
    yellow: "#f4d329",
    orange: "#f55324",
  };
  const botanical = '<svg viewBox="0 0 800 180" aria-hidden="true" focusable="false">' +
    '<g><path d="M395 125 C333 119 282 95 232 79 C163 56 99 60 30 80"/>' +
    '<path d="M405 125 C467 119 518 95 568 79 C637 56 701 60 770 80"/>' +
    '<path d="M223 77 C190 37 164 34 148 42 C154 65 183 82 223 77Z"/>' +
    '<path d="M278 96 C270 49 246 40 226 45 C226 72 245 94 278 96Z"/>' +
    '<path d="M333 114 C334 69 313 54 294 57 C289 83 306 108 333 114Z"/>' +
    '<path d="M577 77 C610 37 636 34 652 42 C646 65 617 82 577 77Z"/>' +
    '<path d="M522 96 C530 49 554 40 574 45 C574 72 555 94 522 96Z"/>' +
    '<path d="M467 114 C466 69 487 54 506 57 C511 83 494 108 467 114Z"/>' +
    '<path d="M163 63 C146 54 132 53 119 56 M637 63 C654 54 668 53 681 56"/>' +
    '<path d="M190 125 C198 109 209 109 215 122 C222 109 233 109 241 125 M559 125 C567 109 578 109 584 122 C591 109 602 109 610 125"/>' +
    '<ellipse cx="215" cy="131" rx="5" ry="4"/><ellipse cx="585" cy="131" rx="5" ry="4"/>' +
    '</g><g><path d="M369 137 C382 121 394 121 400 135 C406 121 418 121 431 137"/>' +
    '<ellipse cx="400" cy="145" rx="6" ry="4"/></g></svg>';

  function burstSvg() {
    const radii = [58, 31, 60, 33, 56, 29, 59, 32, 57, 33, 60, 30,
      58, 31, 60, 29, 56, 33, 59, 30, 58, 32, 60, 29];
    const points = radii.map((radius, index) => {
      const angle = -Math.PI / 2 + index * Math.PI / 12;
      const x = 60 + Math.cos(angle) * radius;
      const y = 60 + Math.sin(angle) * radius;
      return `${x.toFixed(2)},${y.toFixed(2)}`;
    }).join(" ");
    return `<svg viewBox="0 0 120 120" preserveAspectRatio="none" aria-hidden="true" focusable="false"><path d="M${points.replaceAll(" ", " L")} Z"/></svg>`;
  }

  const design = {
    id: "herbalproduct32",
    title: "Herbal Product",
    labelFace: "HerbalLabel",
    defaults,
    contrastException: {
      minimum: 3.0,
      rationale: "The source's large cream NEW label prints over a bright orange twelve-ray burst.",
    },
    controls: [
      { key: "headline", label: "Main product name", type: "text", value: defaults.headline },
      { key: "productName", label: "Coffee description", type: "text", value: defaults.productName },
      { key: "batch", label: "Batch mark", type: "text", value: defaults.batch },
      { key: "badge", label: "Stock burst", type: "text", value: defaults.badge },
      { key: "process", label: "Process and weight · one line per row", type: "textarea", rows: 2, value: defaults.process },
      { key: "roast", label: "Roast level", type: "text", value: defaults.roast },
      { key: "date", label: "Roast date · one line per row", type: "textarea", rows: 2, value: defaults.date },
      { key: "scale", label: "Display scale", min: .86, max: 1.12, step: .01 },
      { key: "tracking", label: "Display tracking", min: -.09, max: .035, step: .005 },
      { key: "detailScale", label: "Detail scale", min: .8, max: 1.2, step: .01 },
      { key: "green", label: "Carton green", type: "color", value: defaults.green },
      { key: "cream", label: "Label cream", type: "color", value: defaults.cream },
      { key: "ink", label: "Label ink", type: "color", value: defaults.ink },
      { key: "yellow", label: "Frame yellow", type: "color", value: defaults.yellow },
      { key: "orange", label: "Stock orange", type: "color", value: defaults.orange },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const square = board.dataset.ratio === "1x1";
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "HerbalLabel");
      for (const name of ["green", "cream", "ink", "yellow", "orange"]) {
        const value = props[name] ?? state[name];
        board.style.setProperty(`--herbal-${name}`,
          square && name === "green" && value === defaults.green ? "#315f3a" : value);
      }

      const layer = (className, name, parent = board) => {
        const element = document.createElement("div");
        element.className = className;
        element.dataset.layoutItem = name;
        parent.append(element);
        return element;
      };
      const fit = (element, { width, height, max, min, tracking, display = false, scale = 1 }) => {
        if (display) element.dataset.displayItem = "true";
        const size = window.SupportLayout.fitLine(element, {
          width: board.clientWidth * width,
          height: board.clientHeight * height,
          maxSize: board.clientHeight * max * scale,
          minSize: board.clientHeight * min,
          tracking,
          inkAware: true,
        });
        element.style.fontSize = `${size}px`;
        element.style.letterSpacing = `${tracking}em`;
        return element;
      };

      layer("carton-frame", "herbal-outer-frame");
      layer("carton-paper", "herbal-cream-label");
      const plant = layer("plant-mark", "herbal-botanical-sprigs");
      plant.innerHTML = botanical;

      const burst = layer("stock-burst", "herbal-twelve-ray-burst");
      burst.innerHTML = burstSvg();
      const badge = layer("stock-copy", "herbal-stock-label");
      badge.textContent = props.badge ?? state.badge ?? defaults.badge;
      const tracking = Number(props.tracking ?? state.tracking);
      fit(badge, { width: .145, height: .065, max: .112, min: .055,
        tracking: .012, display: true, scale: Number(props.scale ?? state.scale) });

      const batch = layer("batch-mark", "herbal-batch-oval");
      const batchText = document.createElement("span");
      batchText.dataset.layoutItem = "herbal-batch-word";
      batchText.textContent = props.batch ?? state.batch ?? defaults.batch;
      batch.append(batchText);
      fit(batchText, { width: .17, height: .11, max: .1, min: .05,
        tracking: -.025, display: true, scale: Number(props.scale ?? state.scale) });

      const title = layer("product-title", "herbal-product-headline");
      title.textContent = props.headline ?? state.headline ?? defaults.headline;
      fit(title, { width: square ? .84 : .77, height: square ? .16 : .19,
        max: square ? .18 : .215, min: .09,
        tracking, display: true, scale: Number(props.scale ?? state.scale) });

      const sub = layer("product-name", "herbal-product-description");
      const subText = document.createElement("span");
      subText.textContent = props.productName ?? state.productName ?? defaults.productName;
      sub.append(subText);
      fit(subText, { width: square ? .64 : .575, height: .082, max: .066, min: .033,
        tracking: Math.min(tracking, -.018), display: true,
        scale: Number(props.scale ?? state.scale) });

      const detailScale = Number(props.detailScale ?? state.detailScale);
      const addSmallLines = (className, key, name, lines, width, align) => {
        const block = layer(`detail-block ${className}`, name);
        block.style.textAlign = align;
        const copy = String(props[key] ?? state[key] ?? defaults[key]).split("\n");
        lines.forEach((_, index) => {
          const line = document.createElement("span");
          line.className = "detail-line";
          line.dataset.layoutItem = `${name}-${index + 1}`;
          line.textContent = copy[index] ?? "";
          block.append(line);
          fit(line, { width, height: .035, max: .025, min: .016,
            tracking: .005, scale: detailScale });
        });
        return block;
      };
      addSmallLines("product-process", "process", "herbal-process-weight",
        defaults.process.split("\n"), square ? .36 : .22, "left");

      const roast = layer("detail-block product-roast", "herbal-roast-level");
      roast.textContent = props.roast ?? state.roast ?? defaults.roast;
      fit(roast, { width: square ? .55 : .28, height: square ? .07 : .075,
        max: square ? .06 : .07, min: .035,
        tracking: -.025, display: true,
        scale: Number(props.scale ?? state.scale) });

      addSmallLines("product-date", "date", "herbal-roast-date",
        defaults.date.split("\n"), square ? .34 : .165, "right");
    },
    getContrast() {
      const ink = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--herbal-ink").trim();
      const cream = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--herbal-cream").trim();
      const orange = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--herbal-orange").trim();
      return Math.min(window.SupportLayout.contrast(ink, cream),
        window.SupportLayout.contrast(cream, orange));
    },
    getWarnings() { return design.warnings || []; },
  };
  window.HerbalProduct32 = design;
})();
