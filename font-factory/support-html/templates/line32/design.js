(function () {
  function titleCase(value) {
    return String(value ?? "").trim().split(/(\s+)/u).map((part) => {
      if (!part || /^\s+$/u.test(part)) return part;
      const match = part.match(/^([^\p{L}\p{N}]*)([\p{L}\p{N}])([\s\S]*)$/u);
      if (!match) return part;
      return match[1] + match[2].toLocaleUpperCase("en") + match[3].toLocaleLowerCase("en");
    }).join("");
  }

  function packLines(value) {
    const words = titleCase(value).split(/\s+/u).filter(Boolean);
    if (words.length <= 1) return [words[0] || "Letters"];
    const total = words.reduce((sum, word) => sum + word.length, 0) + words.length - 1;
    const target = total / 2;
    const lines = [];
    let current = [];
    let run = 0;
    for (let i = 0; i < words.length; i += 1) {
      const word = words[i];
      current.push(word);
      run += word.length + (current.length > 1 ? 1 : 0);
      const remaining = words.length - i - 1;
      const needs = 1 - lines.length;
      if (needs > 0 && remaining >= needs && (run >= target || remaining === needs)) {
        lines.push(current.join(" "));
        current = [];
        run = 0;
      }
    }
    if (current.length) lines.push(current.join(" "));
    return lines;
  }

  const design = {
    id: "line32",
    title: "Letterpress Broadside",
    defaults: {
      headline: "Letters That Matter",
      overline: "New Release",
      edge: "101 Glyphs",
      footer: "Display Specimen",
      scale: 1,
      top: .20,
      secondTop: .49,
      tracking: -.025,
      ghostScale: 1,
      echoStrength: .30,
      grain: 0,
      deviceOpacity: .22,
      ink: "#202214",
      accent: "#80600e",
      muted: "#696953",
      paperOne: "#f1eee0",
      paperTwo: "#e0dbc6",
      inkRgb: "32 34 20",
      accentRgb: "128 96 14",
      mutedRgb: "105 105 83",
      dark: false,
      pool: .021,
      device: "none",
      echo: true,
      warnings: [],
    },
    controls: [
      { key: "headline", label: "Headline", type: "text" },
      { key: "overline", label: "Overline", type: "text" },
      { key: "scale", label: "Headline Scale", min: .85, max: 1.10, step: .01 },
      { key: "top", label: "First Line Position", min: .16, max: .28, step: .001 },
      { key: "secondTop", label: "Second Line Position", min: .45, max: .59, step: .001 },
      { key: "tracking", label: "Headline Spacing", min: -.065, max: .015, step: .001 },
      { key: "ghostScale", label: "Ghost Initial Scale", min: .7, max: 1.3, step: .01 },
      { key: "echoStrength", label: "Outline Echo", min: 0, max: .45, step: .01 },
      { key: "grain", label: "Paper Grain", min: 0, max: .25, step: .01 },
      { key: "deviceOpacity", label: "Theme Device", min: 0, max: .45, step: .01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const headlineCopy = titleCase(props.headline ?? state.headline ?? "Letters That Matter");
      const lines = Array.isArray(props.lines) && props.lines.length
        ? props.lines.map(titleCase)
        : packLines(headlineCopy);
      const overlineCopy = titleCase(props.overline ?? state.overline ?? "New Release");
      const edgeCopy = titleCase(props.edge ?? state.edge ?? "101 Glyphs");
      const footerCopy = titleCase(props.footer ?? state.footer ?? "Display Specimen");
      const scale = Number(props.scale ?? state.scale ?? 1);
      const top = Number(props.top ?? state.top ?? .285);
      const secondTop = Number(props.secondTop ?? state.secondTop ?? .505);
      const tracking = Number(props.tracking ?? state.tracking ?? -.025);
      const ghostScale = Number(props.ghostScale ?? state.ghostScale ?? 1);
      const echoStrength = Number(props.echoStrength ?? state.echoStrength ?? .30);
      const grain = Number(props.grain ?? state.grain ?? .12);
      const deviceOpacity = Number(props.deviceOpacity ?? state.deviceOpacity ?? .22);
      const device = String(props.device ?? state.device ?? "none");
      const echoEnabled = Boolean(props.echo ?? state.echo ?? true) && echoStrength > 0;
      const ink = props.ink ?? state.ink ?? "#202214";
      const accent = props.accent ?? state.accent ?? "#80600e";
      const muted = props.muted ?? state.muted ?? "#696953";
      const paperOne = props.paperOne ?? state.paperOne ?? "#f1eee0";
      const paperTwo = props.paperTwo ?? state.paperTwo ?? "#e0dbc6";
      board.style.setProperty("--wide-ink", ink);
      board.style.setProperty("--wide-accent", accent);
      board.style.setProperty("--wide-muted", muted);
      board.style.setProperty("--wide-paper-one", paperOne);
      board.style.setProperty("--wide-paper-two", paperTwo);
      board.style.setProperty("--wide-ink-rgb", props.inkRgb ?? state.inkRgb ?? "32 34 20");
      board.style.setProperty("--wide-accent-rgb", props.accentRgb ?? state.accentRgb ?? "128 96 14");
      board.style.setProperty("--wide-muted-rgb", props.mutedRgb ?? state.mutedRgb ?? "105 105 83");
      board.style.setProperty("--wide-pool", String(props.pool ?? state.pool ?? .021));
      board.style.setProperty("--wide-grain", String(grain));
      board.style.setProperty("--wide-device-opacity", String(deviceOpacity));
      board.style.setProperty("--wide-tracking", `${tracking}em`);
      board.style.setProperty("--wide-ghost-scale", String(ghostScale));
      board.style.setProperty("--wide-echo-strength", String(echoStrength));
      board.style.setProperty("--wide-top", `${top * 100}%`);
      board.style.setProperty("--wide-second-top", `${secondTop * 100}%`);
      board.style.setProperty("--wide-scale", String(scale));
      design.currentAccent = accent;
      design.currentGround = paperOne;
      board.style.setProperty("--wide-label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "Line32Label, sans-serif");

      if (device !== "none") {
        const deviceLayer = document.createElement("div");
        deviceLayer.className = `wide-device wide-device--${device}`;
        deviceLayer.dataset.layoutItem = "theme-device";
        board.append(deviceLayer);
      }

      const grainLayer = document.createElement("div");
      grainLayer.className = "wide-grain";
      grainLayer.dataset.layoutItem = "paper-tooth";
      board.append(grainLayer);

      const ghostClip = document.createElement("div");
      ghostClip.className = "wide-ghost-clip";
      ghostClip.dataset.layoutItem = "clipped-ghost-initial";
      if (headlineCopy) {
        const lastLetter = [...headlineCopy].reverse().find((char) => /\p{L}/u.test(char));
        if (lastLetter) {
          const ghost = document.createElement("span");
          ghost.className = "wide-ghost-letter";
          ghost.textContent = lastLetter.toLocaleUpperCase("en");
          ghost.style.transform = `translate(-50%, -50%) scale(${ghostScale})`;
          ghostClip.append(ghost);
        }
      }
      board.append(ghostClip);

      const overline = document.createElement("div");
      overline.className = "wide-header";
      overline.dataset.layoutItem = "overline-row";
      const overlineText = document.createElement("span");
      overlineText.className = "wide-overline";
      overlineText.textContent = overlineCopy;
      overlineText.dataset.layoutItem = "overline";
      overline.append(overlineText);
      board.append(overline);
      const headerRule = document.createElement("div");
      headerRule.className = "wide-header-rule";
      board.append(headerRule);
      const tick = document.createElement("div");
      tick.className = "wide-accent-tick";
      board.append(tick);

      const placedLines = lines.slice(0, 2);
      const linePositions = placedLines.length > 1
        ? [top, secondTop]
        : [Math.min(top + .10, .39)];
      const headlineRows = [];
      const headlineTexts = [];
      const headlineEchoes = [];
      placedLines.forEach((line, index) => {
        const row = document.createElement("div");
        row.className = "wide-line-row";
        row.dataset.layoutItem = `headline-row-${index + 1}`;
        const text = document.createElement("span");
        text.className = `wide-headline ${index === 1 ? "wide-headline--accent" : "wide-headline--ink"}`;
        text.textContent = line;
        text.style.letterSpacing = `${tracking}em`;
        text.dataset.layoutItem = `headline-line-${index + 1}`;
        text.dataset.displayItem = "true";
        row.append(text);
        let echo = null;
        if (index === 0 && echoEnabled && placedLines.length > 1) {
          echo = document.createElement("span");
          echo.className = "wide-echo";
          echo.textContent = line;
          echo.style.letterSpacing = `${tracking}em`;
          echo.style.opacity = String(echoStrength);
          echo.dataset.layoutItem = "wireframe-echo";
          row.append(echo);
        }
        board.append(row);
        headlineRows.push(row);
        headlineTexts.push(text);
        headlineEchoes.push(echo);
      });
      const rowHeight = .275;
      const stackGap = placedLines.length > 1
        ? Math.max(.01, linePositions[1] - linePositions[0] - rowHeight) : 0;
      const stackHeight = rowHeight * placedLines.length + stackGap * (placedLines.length - 1);
      const headlineSize = window.SupportLayout.fitStack(headlineTexts, {
        name: "line32-headline",
        containers: headlineRows,
        board,
        left: .055,
        top: linePositions[0],
        width: .89,
        height: stackHeight,
        gap: stackGap,
        maxSize: board.clientHeight * .34 * scale,
        minSize: board.clientHeight * .06,
        tracking,
      });
      headlineEchoes.forEach((echo, index) => {
        if (echo) echo.style.fontSize = `${headlineSize}px`;
      });

      const footer = document.createElement("div");
      footer.className = "wide-footer-row";
      footer.dataset.layoutItem = "footer-row";
      const footerTick = document.createElement("div");
      footerTick.className = "wide-footer-tick";
      footer.append(footerTick);
      const footerText = document.createElement("span");
      footerText.className = "wide-footer-label";
      footerText.textContent = footerCopy;
      footerText.dataset.layoutItem = "footer-label";
      footer.append(footerText);
      board.append(footer);

      const edgeRow = document.createElement("div");
      edgeRow.className = "wide-edge-row";
      edgeRow.dataset.layoutItem = "edge-copy-row";
      const edgeText = document.createElement("span");
      edgeText.className = "wide-edge-label";
      edgeText.textContent = edgeCopy;
      edgeText.dataset.layoutItem = "edge-copy";
      edgeRow.append(edgeText);
      board.append(edgeRow);
      window.SupportLayout.fitLine(overlineText, {
        width: board.clientWidth * .75,
        height: board.clientHeight * .030,
        maxSize: board.clientHeight * .0255,
        minSize: 10,
        tracking: .22,
        inkAware: true,
      });
      window.SupportLayout.fitLine(footerText, {
        width: board.clientWidth * .64,
        height: board.clientHeight * .042,
        maxSize: board.clientHeight * .0335,
        minSize: 10,
        tracking: .16,
        inkAware: true,
      });
      window.SupportLayout.fitLine(edgeText, {
        width: board.clientWidth * .12,
        height: board.clientHeight * .020,
        maxSize: board.clientHeight * .0235,
        minSize: 8,
        tracking: .30,
        inkAware: true,
      });
      design.headlineFontSize = `${headlineSize}px`;
    },
    getContrast() {
      return window.SupportLayout.contrast(this.currentAccent || "#80600e", this.currentGround || "#f1eee0");
    },
    contrastException: {
      minimum: 3,
      rationale: "The quiet echo keeps its theme ink over the softly textured field.",
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Line32 = design;
})();
