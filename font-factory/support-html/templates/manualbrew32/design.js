(function () {
  const defaults = {
    lineOne: "Manual",
    lineTwo: "Brew",
    credit: "Our SunKits © Rivari Studio 2024",
    background: "#2c2626",
    pink: "#f580a1",
    yellow: "#f4d12c",
    green: "#97cd30",
    blue: "#40bedf",
    orange: "#f05c2f",
    scale: 1,
    letterHeight: 1.2,
    tracking: 0.015,
    lineGap: 1,
  };
  const design = {
    id: "manualbrew32",
    title: "Manual Brew",
    labelFace: "ManualBrewLabel",
    defaults,
    contrastException: {
      minimum: 3.0,
      rationale: "The source uses large, brightly colored specimen letters against charcoal; the darkest source accent is orange.",
    },
    controls: [
      { key: "lineOne", label: "Top word", type: "text", value: defaults.lineOne },
      { key: "lineTwo", label: "Lower word", type: "text", value: defaults.lineTwo },
      { key: "credit", label: "Studio credit", type: "text", value: defaults.credit },
      { key: "scale", label: "Wordmark scale", min: 0.82, max: 1.12, step: 0.01 },
      { key: "letterHeight", label: "Letter height", min: 0.9, max: 1.3, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.04, max: 0.11, step: 0.005 },
      { key: "lineGap", label: "Line separation", min: 0.82, max: 1.22, step: 0.01 },
      { key: "background", label: "Charcoal", type: "color", value: defaults.background },
      { key: "pink", label: "Pink", type: "color", value: defaults.pink },
      { key: "yellow", label: "Yellow", type: "color", value: defaults.yellow },
      { key: "green", label: "Green", type: "color", value: defaults.green },
      { key: "blue", label: "Blue", type: "color", value: defaults.blue },
      { key: "orange", label: "Orange", type: "color", value: defaults.orange },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "ManualBrewLabel");
      board.style.setProperty("--brew-background", props.background ?? state.background);
      board.style.setProperty("--brew-tracking", (props.tracking ?? state.tracking) + "em");

      const palette = [
        props.pink ?? state.pink,
        props.yellow ?? state.yellow,
        props.green ?? state.green,
        props.blue ?? state.blue,
        props.orange ?? state.orange,
      ];
      design.currentBackground = props.background ?? state.background;
      design.currentPalette = palette;
      const fitColoredLine = (element, { width, height, maxSize, minSize }) => {
        element.style.whiteSpace = "nowrap";
        element.style.display = "inline-block";
        element.style.width = "max-content";
        let low = minSize;
        let high = maxSize;
        let best = minSize;
        for (let attempt = 0; attempt < 18; attempt += 1) {
          const size = (low + high) / 2;
          element.style.fontSize = `${size}px`;
          const bounds = element.getBoundingClientRect();
          if (bounds.width <= width && bounds.height <= height) {
            best = size;
            low = size;
          } else {
            high = size;
          }
        }
        element.style.fontSize = `${best}px`;
        return best;
      };
      const addWord = (key, fallback, name, className, paletteIndexes, top, width, height, maxSize) => {
        const text = String(props[key] ?? state[key] ?? fallback).trim();
        const word = document.createElement("div");
        word.className = "brew-word " + className;
        word.dataset.layoutItem = name;
        word.dataset.displayItem = "true";
        word.dataset.text = text;
        word.style.top = top + "%";
        word.replaceChildren(...[...text].map((character, index) => {
          const glyph = document.createElement("span");
          glyph.textContent = character;
          glyph.style.color = palette[paletteIndexes[index % paletteIndexes.length] % palette.length];
          return glyph;
        }));
        board.append(word);
        const size = fitColoredLine(word, {
          width: board.clientWidth * width,
          height: board.clientHeight * height,
          maxSize: board.clientHeight * maxSize * Number(props.scale ?? state.scale),
          minSize: board.clientHeight * .09,
        });
        word.style.letterSpacing = (props.tracking ?? state.tracking) + "em";
        word.style.fontSize = size + "px";
        return word;
      };
      const separation = Number(props.lineGap ?? state.lineGap);
      const letterHeight = Number(props.letterHeight ?? state.letterHeight);
      const top = addWord("lineOne", defaults.lineOne, "manualbrew-top-word", "brew-manual",
        [0, 1, 2, 3, 4, 1], 22, .82, .34, .31);
      const bottom = addWord("lineTwo", defaults.lineTwo, "manualbrew-bottom-word", "brew-brew",
        [4, 3, 1, 0], 53.5 + (separation - 1) * 11, .58, .34, .30);
      const credit = document.createElement("div");
      credit.className = "brew-credit";
      credit.dataset.layoutItem = "manualbrew-studio-credit";
      credit.textContent = props.credit ?? state.credit ?? defaults.credit;
      board.append(credit);
      top.style.transform = `translateX(-50%) scaleY(${letterHeight})`;
      bottom.style.transform = `translateX(-50%) scaleY(${letterHeight})`;
      top.style.transformOrigin = "center center";
      bottom.style.transformOrigin = "center center";
    },
    getContrast() {
      const bg = design.currentBackground || defaults.background;
      return Math.min(...(design.currentPalette || [defaults.pink, defaults.yellow, defaults.green,
        defaults.blue, defaults.orange]).map(color => window.SupportLayout.contrast(color, bg)));
    },
    getWarnings() { return design.warnings || []; },
  };
  window.ManualBrew32 = design;
})();
