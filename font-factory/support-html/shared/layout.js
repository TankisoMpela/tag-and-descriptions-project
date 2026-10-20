(function () {
  const measureElement = document.createElement("span");
  const measuredProperties = [
    "fontFamily", "fontStyle", "fontWeight", "fontStretch", "fontVariant",
    "fontKerning", "fontFeatureSettings", "fontVariationSettings",
    "fontOpticalSizing", "fontSizeAdjust", "lineHeight", "wordSpacing",
    "textTransform", "textRendering", "writingMode",
  ];
  Object.assign(measureElement.style, {
    position: "fixed",
    left: "-100000px",
    top: "0",
    display: "inline-block",
    width: "max-content",
    height: "max-content",
    maxWidth: "none",
    whiteSpace: "pre",
    visibility: "hidden",
    contain: "layout style",
    transform: "none",
    pointerEvents: "none",
  });

  function measure(element, text, size, tracking) {
    const computed = getComputedStyle(element);
    for (const property of measuredProperties) {
      measureElement.style[property] = computed[property];
    }
    const declaredLineHeight = computed.lineHeight;
    const declaredFontSize = parseFloat(computed.fontSize) || size;
    const lineHeightRatio = declaredLineHeight === "normal"
      ? NaN : parseFloat(declaredLineHeight) / declaredFontSize;
    measureElement.style.lineHeight = Number.isFinite(lineHeightRatio) && lineHeightRatio > 0
      ? `${lineHeightRatio}em` : "normal";
    measureElement.style.fontSize = `${size}px`;
    measureElement.style.letterSpacing = `${tracking}em`;
    element.style.whiteSpace = "pre";
    measureElement.textContent = text;
    document.body.append(measureElement);
    const bounds = measureElement.getBoundingClientRect();
    measureElement.remove();
    return { width: bounds.width, height: bounds.height };
  }

  function setFitResult(element, fits, width, height, size) {
    element.dataset.fitSafeWidth = String(width);
    element.dataset.fitSafeHeight = String(height);
    element.dataset.fitFontSize = String(size);
    if (fits) delete element.dataset.fitFailure;
    else element.dataset.fitFailure = "minimum-size-exceeds-safe-area";
  }

  function fitLine(element, options) {
    const {
      width,
      height,
      maxSize,
      minSize = 18,
      tracking = -0.02,
      inkAware = false,
    } = options;
    element.style.letterSpacing = `${tracking}em`;
    const copy = element.textContent || "";
    const fitsAt = (size) => {
      const bounds = measure(element, copy, size, tracking);
      return bounds.width <= width + .25 && bounds.height <= height + .25;
    };
    const minimumFits = fitsAt(minSize);
    let low = minSize;
    let high = maxSize;
    let best = minimumFits ? minSize : 0;
    if (minimumFits) {
      for (let i = 0; i < 20; i += 1) {
        const size = (low + high) / 2;
        if (fitsAt(size)) {
          best = size;
          low = size;
        } else {
          high = size;
        }
      }
    }
    const chosen = best || minSize;
    element.style.fontSize = `${chosen}px`;
    setFitResult(element, minimumFits, width, height, chosen);
    return chosen;
  }

  function fitLinesTogether(elements, options) {
    const {
      width,
      height,
      maxSize,
      minSize = 18,
      tracking = -0.02,
      inkAware = false,
    } = options;
    const lines = [...elements];
    if (!lines.length) return minSize;
    const copies = lines.map((element) => element.textContent || "");
    const fitsAt = (size) => {
      for (let index = 0; index < lines.length; index += 1) {
        const bounds = measure(lines[index], copies[index], size, tracking);
        if (bounds.width > width + .25 || bounds.height > height + .25) return false;
      }
      return true;
    };
    for (const element of lines) element.style.letterSpacing = `${tracking}em`;
    let low = minSize;
    let high = maxSize;
    const minimumFits = fitsAt(minSize);
    let best = minimumFits ? minSize : 0;
    if (minimumFits) {
      for (let i = 0; i < 20; i += 1) {
        const size = (low + high) / 2;
        if (fitsAt(size)) {
          best = size;
          low = size;
        } else {
          high = size;
        }
      }
    }
    const chosen = best || minSize;
    for (const element of lines) {
      element.style.fontSize = `${chosen}px`;
      setFitResult(element, minimumFits, width, height, chosen);
    }
    return chosen;
  }

  // Lay out readable text rows as separate, non-overlapping boxes, then fit
  // their shared type size to the narrowest row. Use this for ordinary stacks;
  // art that intentionally crosses an image or another layer stays template-led.
  function fitStack(elements, options) {
    const {
      board,
      containers = elements,
      coordinateWidth = board.clientWidth,
      coordinateHeight = board.clientHeight,
      left = 0,
      top = 0,
      width = 1,
      height = 1,
      gap = 0.015,
      maxSize,
      minSize = 18,
      tracking = -0.02,
    } = options;
    const lines = [...elements];
    const boxes = [...containers];
    if (!lines.length || lines.length !== boxes.length) return minSize;
    const gapPx = board.clientHeight * Math.max(0, gap);
    const rowHeight = (board.clientHeight * height - gapPx * (lines.length - 1)) / lines.length;
    const rowWidth = coordinateWidth * width;
    lines.forEach((line, index) => {
      const box = boxes[index];
      box.style.left = `${left * 100}%`;
      box.style.top = `${(top + (rowHeight + gapPx) * index / coordinateHeight) * 100}%`;
      box.style.width = `${width * 100}%`;
      box.style.height = `${rowHeight}px`;
      box.style.boxSizing = "border-box";
      box.style.display = "flex";
      box.style.alignItems = "center";
      box.style.overflow = "visible";
      if (options.align === "right") {
        box.style.justifyContent = "flex-end";
        box.style.textAlign = "right";
      } else if (options.align === "center") {
        box.style.justifyContent = "center";
        box.style.textAlign = "center";
      }
      box.dataset.supportStackIndex = String(index);
      line.dataset.supportStackGroup = options.name || "text-stack";
      line.dataset.supportStackIndex = String(index);
    });
    return fitLinesTogether(lines, {
      width: rowWidth * 0.97,
      height: rowHeight * 0.94,
      maxSize,
      minSize,
      tracking,
    });
  }

  function luminance(hex) {
    const value = hex.replace("#", "");
    const channels = [0, 2, 4].map((offset) => {
      const channel = parseInt(value.slice(offset, offset + 2), 16) / 255;
      return channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4;
    });
    return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
  }

  function contrast(foreground, background) {
    const a = luminance(foreground);
    const b = luminance(background);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  }

  function boundsReport(board, design) {
    const box = board.getBoundingClientRect();
    const outOfBounds = [];
    const slots = [...board.querySelectorAll("[data-layout-item]")].map((element) => {
      const bounds = element.getBoundingClientRect();
      const relative = {
        x: bounds.left - box.left,
        y: bounds.top - box.top,
        width: bounds.width,
        height: bounds.height,
      };
      if (relative.x < -1 || relative.y < -1 ||
          relative.x + relative.width > box.width + 1 ||
          relative.y + relative.height > box.height + 1) {
        outOfBounds.push({ name: element.dataset.layoutItem, ...relative });
      }
      return {
        name: element.dataset.layoutItem,
        text: element.textContent.trim(),
        fontSize: getComputedStyle(element).fontSize,
        ...relative,
      };
    });
    const displays = slots.filter((slot) => board.querySelector(
      `[data-layout-item="${CSS.escape(slot.name)}"]`,
    )?.hasAttribute("data-display-item"));
    const headlineFontSize = displays.length
      ? `${Math.max(...displays.map((slot) => parseFloat(slot.fontSize)))}px`
      : "0px";
    const displayFontSizes = displays.map((slot) => parseFloat(slot.fontSize));
    const fitFailures = [...board.querySelectorAll("[data-fit-failure]")].map((element) => ({
      name: element.dataset.layoutItem || element.parentElement?.dataset.layoutItem || "text",
      text: element.textContent.trim(),
      reason: element.dataset.fitFailure,
      fontSize: getComputedStyle(element).fontSize,
      safeWidth: Number(element.dataset.fitSafeWidth),
      safeHeight: Number(element.dataset.fitSafeHeight),
    }));
    const stackGroups = new Map();
    for (const element of board.querySelectorAll("[data-support-stack-group]")) {
      const group = element.dataset.supportStackGroup;
      const list = stackGroups.get(group) || [];
      list.push({
        name: element.dataset.layoutItem || group,
        index: Number(element.dataset.supportStackIndex || 0),
        bounds: element.getBoundingClientRect(),
      });
      stackGroups.set(group, list);
    }
    const stackOverlaps = [];
    for (const [group, rows] of stackGroups) {
      rows.sort((a, b) => a.index - b.index);
      for (let i = 0; i < rows.length; i += 1) {
        for (let j = i + 1; j < rows.length; j += 1) {
          const a = rows[i].bounds;
          const b = rows[j].bounds;
          if (Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1 &&
              Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1) {
            stackOverlaps.push({ group, first: rows[i].name, second: rows[j].name });
          }
        }
      }
    }
    return {
      template: design.id,
      headlineFontSize,
      smallestDisplayFontSize: displayFontSizes.length
        ? `${Math.min(...displayFontSizes)}px` : "0px",
      contrast: design.getContrast(),
      contrastException: design.contrastException || undefined,
      outOfBounds,
      fitFailures,
      stackOverlaps,
      slots,
      contentWarnings: design.getWarnings?.() || [],
    };
  }

  window.SupportLayout = { fitLine, fitLinesTogether, fitStack, contrast, boundsReport };
})();
