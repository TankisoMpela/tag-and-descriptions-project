(function () {
  const assetRoot = "../../assets/blackletter-reference";

  function createText(board, definition, spec, state) {
    const box = document.createElement("div");
    box.className = `br-item br-text-box br-text-box--${spec.kind || "display"}`;
    const rotated = spec.rotate === 90 || spec.rotate === -90;
    const boxW = rotated ? spec.h * board.clientHeight : spec.w;
    const boxH = rotated ? spec.w * board.clientWidth : spec.h;
    const boxX = rotated
      ? (spec.x + spec.w / 2) * board.clientWidth - boxW / 2
      : spec.x * 100;
    const boxY = rotated
      ? (spec.y + spec.h / 2) * board.clientHeight - boxH / 2
      : spec.y * 100;
    box.style.left = rotated ? `${boxX}px` : `${boxX}%`;
    box.style.top = rotated ? `${boxY}px` : `${boxY}%`;
    box.style.width = rotated ? `${boxW}px` : `${boxW * 100}%`;
    box.style.height = rotated ? `${boxH}px` : `${boxH * 100}%`;
    if (rotated) box.style.transform = `rotate(${spec.rotate}deg)`;
    box.style.setProperty("--item-ink", spec.color || "var(--br-ink)");
    box.style.setProperty("--item-size", `${spec.max || 92}px`);
    box.style.setProperty("--item-tracking", `${spec.tracking ?? -0.025}em`);
    if (spec.align) box.style.justifyContent = spec.align;
    if (spec.textAlign) box.style.textAlign = spec.textAlign;
    if (spec.italic) box.classList.add("is-italic");
    if (spec.vertical) box.classList.add("is-vertical");

    const text = document.createElement("span");
    text.className = "br-copy";
    text.textContent = spec.text ?? state[spec.key] ?? definition.defaults[spec.key] ?? "";
    if (spec.textAlign) text.style.textAlign = spec.textAlign;
    if (spec.multiline) text.classList.add("is-multiline");
    if (spec.key) text.dataset.layoutItem = spec.key;
    if (spec.display !== false && spec.kind !== "label") {
      text.dataset.displayItem = "true";
    }
    box.append(text);
    board.append(box);
    window.SupportLayout.fitLine(text, {
      width: (rotated ? boxW : board.clientWidth * boxW) * (spec.fitWidth || 0.94),
      height: (rotated ? boxH : board.clientHeight * boxH) * (spec.fitHeight || 0.76),
      maxSize: spec.max || 92,
      minSize: spec.min || (spec.kind === "label" ? 12 : 42),
      tracking: spec.tracking ?? -0.025,
    });
  }

  function addElement(board, definition, spec, state) {
    if (spec.type === "rays") {
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.classList.add("br-item", "br-ray-field");
      svg.setAttribute("viewBox", "0 0 1000 400");
      svg.setAttribute("preserveAspectRatio", "none");
      svg.style.left = `${spec.x * 100}%`;
      svg.style.top = `${spec.y * 100}%`;
      svg.style.width = `${spec.w * 100}%`;
      svg.style.height = `${spec.h * 100}%`;
      svg.style.zIndex = String(spec.z ?? 8);
      const count = spec.count || 9;
      for (let index = 0; index < count; index += 1) {
        const y = 22 + index * (356 / Math.max(1, count - 1));
        const length = 58 + ((index * 37) % 77);
        for (const rightSide of [false, true]) {
          const ray = document.createElementNS(svg.namespaceURI, "line");
          ray.setAttribute("x1", rightSide ? String(1000 - length) : "0");
          ray.setAttribute("y1", String(y));
          ray.setAttribute("x2", rightSide ? "1000" : String(length));
          ray.setAttribute("y2", String(y + (rightSide ? 14 : -14)));
          ray.setAttribute("stroke", spec.color || "var(--br-accent)");
          ray.setAttribute("stroke-width", String(spec.strokeWidth || 2));
          ray.setAttribute("stroke-linecap", "round");
          svg.append(ray);
        }
      }
      board.append(svg);
      return svg;
    }
    if (spec.type === "swashes") {
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.classList.add("br-item", "br-swashes");
      svg.setAttribute("viewBox", spec.viewBox || "0 0 1200 800");
      svg.setAttribute("preserveAspectRatio", "none");
      svg.style.left = `${spec.x * 100}%`;
      svg.style.top = `${spec.y * 100}%`;
      svg.style.width = `${spec.w * 100}%`;
      svg.style.height = `${spec.h * 100}%`;
      svg.style.zIndex = String(spec.z ?? 10);
      for (const entry of spec.paths || []) {
        const path = document.createElementNS(svg.namespaceURI, "path");
        path.setAttribute("d", entry.d);
        path.setAttribute("fill", entry.fill || "none");
        path.setAttribute("stroke", entry.color || spec.color || "var(--br-accent)");
        path.setAttribute("stroke-width", String(entry.strokeWidth || spec.strokeWidth || 6));
        path.setAttribute("stroke-linecap", "round");
        path.setAttribute("stroke-linejoin", "round");
        if (entry.opacity !== undefined) path.setAttribute("opacity", String(entry.opacity));
        svg.append(path);
      }
      board.append(svg);
      return svg;
    }
    if (spec.type === "arcText") {
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.classList.add("br-item", "br-arc-text");
      svg.setAttribute("viewBox", "0 0 1000 190");
      svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
      svg.style.left = `${spec.x * 100}%`;
      svg.style.top = `${spec.y * 100}%`;
      svg.style.width = `${spec.w * 100}%`;
      svg.style.height = `${spec.h * 100}%`;
      svg.style.color = spec.color || "var(--br-ink)";
      svg.style.zIndex = String(spec.z ?? 12);
      const defs = document.createElementNS(svg.namespaceURI, "defs");
      const path = document.createElementNS(svg.namespaceURI, "path");
      path.id = `${definition.id}-arc-path`;
      path.setAttribute("d", "M 70 176 C 260 0, 740 0, 930 176");
      defs.append(path);
      const label = document.createElementNS(svg.namespaceURI, "text");
      label.classList.add("br-arc-copy");
      label.dataset.layoutItem = spec.key || "arc-label";
      label.dataset.displayItem = "true";
      label.setAttribute("text-anchor", "middle");
      label.setAttribute("font-size", String(spec.fontSize || 70));
      label.setAttribute("letter-spacing", String(spec.letterSpacing || 9));
      if (spec.textLength) {
        label.setAttribute("textLength", String(spec.textLength));
        label.setAttribute("lengthAdjust", "spacing");
      }
      label.setAttribute("fill", "currentColor");
      const textPath = document.createElementNS(svg.namespaceURI, "textPath");
      textPath.setAttribute("href", `#${path.id}`);
      textPath.setAttribute("startOffset", "50%");
      textPath.textContent = state[spec.key] ?? definition.defaults[spec.key] ?? spec.text ?? "";
      label.append(textPath);
      svg.append(defs, label);
      board.append(svg);
      return svg;
    }
    if (spec.type === "text") return createText(board, definition, spec, state);
    const item = document.createElement(spec.type === "image" ? "img" : "div");
    item.className = `br-item br-${spec.type}${spec.className ? ` ${spec.className}` : ""}`;
    item.style.left = `${spec.x * 100}%`;
    item.style.top = `${spec.y * 100}%`;
    item.style.width = `${spec.w * 100}%`;
    item.style.height = `${spec.h * 100}%`;
    if (spec.opacity !== undefined) item.style.opacity = spec.opacity;
    if (spec.rotate || spec.flipX) {
      item.style.transform = `${spec.rotate ? `rotate(${spec.rotate}deg) ` : ""}${spec.flipX ? "scaleX(-1)" : ""}`.trim();
    }
    if (spec.z !== undefined) item.style.zIndex = String(spec.z);
    if (spec.radius) item.style.borderRadius = spec.radius;
    if (spec.color) {
      item.style.setProperty("--shape-ink", spec.color);
      item.style.color = spec.color;
    }
    if (spec.type === "image") {
      item.src = `${assetRoot}/${spec.asset}.png`;
      item.alt = "";
      item.draggable = false;
      item.style.objectFit = spec.fit || "contain";
      if (spec.objectPosition) item.style.objectPosition = spec.objectPosition;
      if (spec.blend) item.style.mixBlendMode = spec.blend;
      if (spec.filter) item.style.filter = spec.filter;
    }
    if (spec.type === "badge") {
      item.classList.add("br-badge");
      const span = document.createElement("span");
      span.textContent = spec.text ?? state[spec.key] ?? definition.defaults[spec.key] ?? "";
      if (spec.display) span.classList.add("br-badge--display");
      item.append(span);
      if (spec.key) item.dataset.layoutItem = spec.key;
      if (spec.display) item.dataset.displayItem = "true";
      window.SupportLayout.fitLine(span, {
        width: board.clientWidth * spec.w * 0.84,
        height: board.clientHeight * spec.h * 0.60,
        maxSize: spec.max || 35,
        minSize: spec.min || 14,
        tracking: spec.tracking ?? 0,
      });
    }
    if (spec.type === "initial") {
      item.classList.add("br-initial");
      const initialSize = board.dataset.ratio === "1x1" && spec.squareSize
        ? spec.squareSize : spec.size;
      if (initialSize) item.style.fontSize = `${initialSize}px`;
      item.dataset.layoutItem = spec.key || "monogram";
      item.dataset.displayItem = "true";
      item.textContent = Array.from(String(state[spec.key || "headline"] ??
        definition.defaults[spec.key || "headline"] ?? "B"))[0] || "B";
    }
    if (spec.type === "panel") {
      item.classList.add("br-panel", `br-panel--${spec.tone || "cream"}`);
      item.style.borderRadius = spec.radius || "0";
      if (spec.border !== false) item.style.border = `1px solid ${spec.borderColor || "color-mix(in srgb, var(--br-ink) 50%, transparent)"}`;
    }
    if (spec.type === "frame" && spec.borderColor) item.style.borderColor = spec.borderColor;
    if (spec.type === "frame" && spec.borderWidth) item.style.borderWidth = spec.borderWidth;
    if (spec.type === "shade") {
      item.classList.add("br-shade");
      item.style.setProperty("--shade-opacity", String(spec.opacity ?? .4));
    }
    if (spec.type === "tilegrid") {
      item.classList.add("br-tilegrid");
      item.style.setProperty("--grid-cols", String(spec.cols || 3));
      item.style.setProperty("--grid-rows", String(spec.rows || 2));
      (spec.tiles || []).forEach((tile, index) => {
        const cell = document.createElement("div");
        cell.className = `br-tile br-tile--${tile.tone || (index % 2 ? "paper" : "ink")}`;
        const copy = document.createElement("span");
        const value = state[tile.key] ?? definition.defaults[tile.key] ?? "";
        copy.textContent = tile.repeat ? `${value}\n${value}` : value;
        copy.className = tile.kind === "initial" ? "br-tile-initial" :
          `br-tile-word${tile.repeat ? " is-repeated" : ""}`;
        if (index === 0) {
          copy.dataset.layoutItem = tile.key || "primary-tile";
          copy.dataset.displayItem = "true";
        }
        cell.append(copy);
        item.append(cell);
        window.SupportLayout.fitLine(copy, {
          width: board.clientWidth * spec.w / (spec.cols || 3) * .88,
          height: board.clientHeight * spec.h / (spec.rows || 2) * .68,
          maxSize: tile.kind === "initial" ? 145 : tile.repeat ? 108 : 86,
          minSize: tile.kind === "initial" ? 76 : tile.repeat ? 54 : 44,
          tracking: -.02,
        });
      });
    }
    if (spec.type === "glyphrows") {
      item.classList.add("br-glyphrows");
      const totalLines = (spec.rows || []).reduce((sum, row) => {
        if (row.kind === "label") return sum + 1;
        const value = String(state[row.key] ?? definition.defaults[row.key] ?? "");
        return sum + (row.lines ? value.split("\n").length : 1);
      }, 0);
      (spec.rows || []).forEach((row) => {
        const value = String(state[row.key] ?? definition.defaults[row.key] ?? "");
        if (row.kind === "label") {
          const label = document.createElement("span");
          label.className = "br-glyph-label";
          label.textContent = value;
          if (row.key) label.dataset.layoutItem = row.key;
          item.append(label);
          return;
        }
        const group = document.createElement("div");
        group.className = "br-glyph-group";
        item.append(group);
        const lines = row.lines ? value.split("\n") : [value];
        lines.forEach((copy, index) => {
          const line = document.createElement("span");
          line.className = "br-glyph-line";
          line.textContent = copy;
          line.dataset.layoutItem = lines.length > 1 ? `${row.key}-${index + 1}` : row.key;
          line.dataset.displayItem = "true";
          group.append(line);
          window.SupportLayout.fitLine(line, {
            width: board.clientWidth * spec.w * .94,
            height: board.clientHeight * spec.h / totalLines * (row.fitHeight || .74),
            maxSize: row.max || 42,
            minSize: row.min || 38,
            tracking: row.tracking ?? 0,
          });
        });
      });
    }
    if (spec.type === "dial") {
      item.classList.add("br-dial");
      const ring = document.createElement("i");
      ring.className = "br-dial-ring";
      item.append(ring);
      for (let i = 0; i < 24; i += 1) {
        const tick = document.createElement("i");
        tick.className = `br-dial-tick${i % 6 === 0 ? " is-major" : ""}`;
        tick.style.setProperty("--tick-angle", `${i * 15}deg`);
        item.append(tick);
      }
      const label = document.createElement("span");
      label.className = "br-dial-label";
      label.textContent = spec.label || "01";
      item.append(label);
    }
    if (spec.type === "medallion") {
      item.classList.add("br-medallion");
      item.textContent = spec.label || "✦";
      if (spec.size) item.style.fontSize = `${spec.size}px`;
    }
    board.append(item);
    return item;
  }

  function create(definition) {
    const design = {
      id: definition.id,
      title: definition.title,
      defaults: definition.defaults,
      literalKeys: definition.literalKeys || [],
      controls: definition.controls || [
        { key: "headline", label: "Main Display Copy", type: "text" },
        { key: "line2", label: "Second Display Line", type: "text" },
        { key: "descriptor", label: "Supporting Copy", type: "text" },
        { key: "overline", label: "Top Label", type: "text" },
        { key: "footer", label: "Footer Copy", type: "text" },
        { key: "scale", label: "Display Scale", min: 0.82, max: 1.12, step: 0.01 },
        { key: "tracking", label: "Display Spacing", min: -0.09, max: 0.015, step: 0.001 },
      ],
      render(board, state) {
        const props = state.props || state;
        board.replaceChildren();
        board.className = `blackletter-reference-board skin-${definition.skin || "ink"} layout-${definition.layout || "poster"}`;
        board.style.setProperty("--br-paper", definition.paper || "#171716");
        board.style.setProperty("--br-ink", definition.ink || "#f3ead4");
        board.style.setProperty("--br-accent", definition.accent || "#c9691d");
        board.style.setProperty("--br-muted", definition.muted || "#8e8574");
        board.style.setProperty("--br-grain", String(definition.grain ?? 0.14));

        const values = { ...definition.defaults, ...state, ...props };
        const scale = Number(values.scale ?? 1);
        const tracking = Number(values.tracking ?? -0.025);
        const elements = (definition.elements || []).map((item) => ({ ...item }));
        for (const item of elements) {
          if (item.type === "text" && item.kind !== "label") {
            item.max = (item.max || 92) * scale;
            item.tracking = tracking;
          }
          addElement(board, definition, item, values);
        }
      },
      getContrast() {
        return window.SupportLayout.contrast(definition.ink || "#f3ead4", definition.contrastPaper || definition.paper || "#171716");
      },
      getWarnings() { return []; },
    };
    return design;
  }

  window.BlackletterReferenceFactory = { create };
})();
