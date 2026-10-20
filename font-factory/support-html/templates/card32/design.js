(function () {
  function titleCase(value) {
    return String(value ?? "").trim().split(/(\s+)/u).map((part) => {
      if (!part || /^\s+$/u.test(part)) return part;
      const match = part.match(/^([^\p{L}\p{N}]*)([\p{L}\p{N}])([\s\S]*)$/u);
      if (!match) return part;
      return match[1] + match[2].toLocaleUpperCase("en") + match[3].toLocaleLowerCase("en");
    }).join("");
  }

  function packLines(value, count) {
    const words = titleCase(value).split(/\s+/u).filter(Boolean);
    if (words.length <= 1) return [words[0] || "Always"];
    const rows = Math.min(count, words.length);
    const total = words.reduce((sum, word) => sum + word.length, 0) + rows - 1;
    const target = total / rows;
    const lines = [];
    let current = [];
    let run = 0;
    for (let index = 0; index < words.length; index += 1) {
      current.push(words[index]);
      run += words[index].length + (current.length > 1 ? 1 : 0);
      const remaining = words.length - index - 1;
      const needed = rows - lines.length - 1;
      if (needed > 0 && remaining >= needed && (run >= target || remaining === needed)) {
        lines.push(current.join(" "));
        current = [];
        run = 0;
      }
    }
    if (current.length) lines.push(current.join(" "));
    return lines;
  }

  function rgbSpace(value) {
    const hex = String(value).replace("#", "");
    return [0, 2, 4].map((offset) => parseInt(hex.slice(offset, offset + 2), 16)).join(" ");
  }

  const design = {
    id: "card32",
    title: "Printed Paper Stack",
    defaults: {
      word: "By Heart",
      phrase: "Cut For The Long Run",
      caption: "In Hand",
      foot: "Banners And Tickets",
      footer: "Display Specimen",
      edge: "101 Glyphs",
      scale: 1,
      wordScale: 1,
      ground: "#0c2e22",
      groundTwo: "#18523a",
      paper: "#effbec",
      paperBack: "#d7e2d4",
      ink: "#c2f1c7",
      accent: "#7ee08c",
      muted: "#6e736d",
      inkRgb: "194 241 199",
      accentRgb: "126 224 140",
      mutedRgb: "110 115 109",
      paperBackRgb: "215 226 212",
      inkOnPaper: "#6e736d",
      accentOnPaper: "#477e4f",
      device: "grid",
      deviceOpacity: .50,
      warnings: [],
    },
    controls: [
      { key: "word", label: "Specimen Word", type: "text" },
      { key: "phrase", label: "Card Phrase", type: "text" },
      { key: "caption", label: "Card Caption", type: "text" },
      { key: "foot", label: "Card Footer", type: "text" },
      { key: "scale", label: "Card Scale", min: .88, max: 1.12, step: .01 },
      { key: "wordScale", label: "Specimen Word Scale", min: .82, max: 1.12, step: .01 },
      { key: "ground", label: "Bench Color", type: "color" },
      { key: "accent", label: "Accent Color", type: "color" },
      { key: "deviceOpacity", label: "Background Device", min: 0, max: .7, step: .01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const get = (key, fallback) => props[key] ?? state[key] ?? fallback;
      const ground = get("ground", "#742a0a");
      const ink = get("ink", "#fff0cb");
      board.style.setProperty("--card-ground-one", ground);
      board.style.setProperty("--card-ground-two", get("groundTwo", "#ac4610"));
      board.style.setProperty("--card-paper", get("paper", "#fff2de"));
      board.style.setProperty("--card-paper-back", get("paperBack", "#f0e7d5"));
      board.style.setProperty("--card-ink", ink);
      board.style.setProperty("--card-accent", get("accent", "#795029"));
      board.style.setProperty("--card-muted", get("muted", "#665b51"));
      board.style.setProperty("--card-ink-rgb", rgbSpace(ink));
      board.style.setProperty("--card-accent-rgb", rgbSpace(get("accent", "#7ee08c")));
      board.style.setProperty("--card-muted-rgb", rgbSpace(get("muted", "#6e736d")));
      board.style.setProperty("--card-paper-back-rgb", rgbSpace(get("paperBack", "#d7e2d4")));
      board.style.setProperty("--card-device-opacity", String(get("deviceOpacity", .50)));
      board.style.setProperty("--card-label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "CardLabel, sans-serif");
      design.currentInk = ink;
      design.currentGround = ground;

      const addLayer = (className, itemName, parent = board) => {
        const element = document.createElement("div");
        element.className = className;
        element.dataset.layoutItem = itemName;
        parent.append(element);
        return element;
      };
      const addText = (parent, className, text, itemName, display = false) => {
        const element = document.createElement("span");
        element.className = className;
        element.textContent = text;
        element.dataset.layoutItem = itemName;
        if (display) element.dataset.displayItem = "true";
        parent.append(element);
        return element;
      };

      const device = String(get("device", "grid"));
      addLayer(`card-bench-device card-bench-device--${device}`, "bench-device");
      const header = addText(board, "card-header", titleCase(get("caption", "In Hand")), "bench-caption");
      addLayer("card-header-rule", "header-rule");

      const wordLines = packLines(get("word", "By Heart"),
        Math.min(2, get("word", "By Heart").trim().split(/\s+/u).length));
      const wordColumn = addLayer("card-word-column", "specimen-word-column");
      const wordElements = wordLines.map((line, index) =>
        addText(wordColumn, "card-word-line", line, `specimen-word-${index + 1}`, true));

      const under = addLayer("card-under", "under-sheet");
      const front = addLayer("card-front", "lettered-card");
      addLayer("card-tape card-tape--left", "left-tape", front);
      addLayer("card-tape card-tape--right", "right-tape", front);
      addLayer("card-inset", "inner-frame", front);
      ["tl", "tr", "bl", "br"].forEach((corner) =>
        addLayer(`card-corner card-corner--${corner}`, `card-corner-${corner}`, front));

      const caption = addText(front, "card-caption", titleCase(get("caption", "In Hand")), "card-caption-text");
      const phrase = get("phrase", "Cut For The Long Run");
      const phraseWords = phrase.trim().split(/\s+/u).filter(Boolean);
      const phraseLines = packLines(phrase, Math.min(3, Math.max(2, phraseWords.length)));
      const phraseBlock = addLayer("card-phrase", "card-phrase-block", front);
      const phraseElements = phraseLines.map((line, index) => {
        const row = addText(phraseBlock, "card-phrase-line", line,
          `card-phrase-${index + 1}`, true);
        row.style.color = get(index % 2 === 0 ? "inkOnPaper" : "accentOnPaper",
          index % 2 === 0 ? "#6e736d" : "#477e4f");
        return row;
      });
      addLayer("card-divider", "card-divider", front);
      const foot = addText(front, "card-foot", titleCase(get("foot", "Banners And Tickets")), "card-foot-text");
      const footer = addLayer("card-footer", "specimen-footer");
      addLayer("card-footer-tick", "footer-tick", footer);
      addText(footer, "", titleCase(get("footer", "Display Specimen")), "footer-label");
      const edge = addText(board, "card-edge", titleCase(get("edge", "101 Glyphs")), "edge-label");

      const scale = Number(get("scale", 1));
      const wordScale = Number(get("wordScale", 1));
      front.style.transform = `translate(-50%, -50%) rotate(-2.2deg) scale(${scale})`;
      under.style.transform = `translate(-50%, -50%) rotate(2.8deg) scale(${scale})`;
      const wordSizes = wordElements.map((element) =>
        window.SupportLayout.fitLine(element, {
          width: board.clientWidth * .315,
          height: board.clientHeight * .32,
          maxSize: board.clientHeight * .32 * wordScale,
          minSize: board.clientHeight * .055,
          tracking: -.035,
          inkAware: true,
        }));
      const phraseSize = window.SupportLayout.fitLinesTogether(phraseElements, {
        width: phraseBlock.clientWidth * .94,
        height: phraseBlock.clientHeight / Math.max(1, phraseElements.length) * .82,
        maxSize: board.clientHeight * .15,
        minSize: board.clientHeight * .05,
        tracking: -.02,
        inkAware: true,
      });
      phraseElements.forEach((element) => { element.style.fontSize = `${phraseSize}px`; });
      window.SupportLayout.fitLine(header, {
        width: board.clientWidth * .45,
        height: board.clientHeight * .03,
        maxSize: board.clientHeight * .0255,
        minSize: 9,
        tracking: .20,
        inkAware: true,
      });
      window.SupportLayout.fitLine(caption, {
        width: board.clientWidth * .35,
        height: board.clientHeight * .035,
        maxSize: board.clientHeight * .0275,
        minSize: 9,
        tracking: .24,
        inkAware: true,
      });
      window.SupportLayout.fitLine(foot, {
        width: board.clientWidth * .35,
        height: board.clientHeight * .04,
        maxSize: board.clientHeight * .028,
        minSize: 9,
        tracking: .17,
        inkAware: true,
      });
      const footerLabel = footer.querySelector("[data-layout-item='footer-label']");
      window.SupportLayout.fitLine(footerLabel, {
        width: board.clientWidth * .38,
        height: board.clientHeight * .04,
        maxSize: board.clientHeight * .0335,
        minSize: 9,
        tracking: .16,
        inkAware: true,
      });
      window.SupportLayout.fitLine(edge, {
        width: board.clientWidth * .12,
        height: board.clientHeight * .02,
        maxSize: board.clientHeight * .0235,
        minSize: 8,
        tracking: .30,
        inkAware: true,
      });
      design.headlineFontSize = `${Math.max(...wordSizes, phraseSize)}px`;
    },
    getContrast() {
      return window.SupportLayout.contrast(this.currentInk || "#fff0cb",
        this.currentGround || "#742a0a");
    },
    contrastException: {
      minimum: 3,
      rationale: "The cream specimen word stays clear over the tinted paper bench.",
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Card32 = design;
})();
