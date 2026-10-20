(function () {
  const design = {
    id: "soldier32",
    title: "Archival plate",
    defaults: {
      year: "1935",
      thisLine: "This",
      warLine: "War Is",
      uselessLine: "Useless",
      digits: "1234567890",
      symbols: "!?$¢€£&",
      yearScale: 1,
      headlineScale: 1,
      stripScale: 1,
      tracking: -0.025,
    },
    controls: [
      { key: "year", label: "Year", type: "text" },
      { key: "thisLine", label: "Headline · line 1", type: "text" },
      { key: "warLine", label: "Headline · line 2", type: "text" },
      { key: "uselessLine", label: "Headline · line 3", type: "text" },
      { key: "digits", label: "Numerals", type: "text" },
      { key: "symbols", label: "Symbols", type: "text" },
      { key: "yearScale", label: "Year scale", min: 0.78, max: 1.14, step: 0.01 },
      { key: "headlineScale", label: "Headline scale", min: 0.78, max: 1.12, step: 0.01 },
      { key: "stripScale", label: "Glyph strip scale", min: 0.78, max: 1.16, step: 0.01 },
      { key: "tracking", label: "Display tracking", min: -0.08, max: 0.015, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, 'Noto Serif Display', Georgia, serif");

      const photo = document.createElement("img");
      photo.className = "soldier-photo";
      photo.dataset.layoutItem = "archival-photo";
      photo.src = "../../../support-references/materials/T13692_soldier-cutout.png";
      photo.alt = "";
      board.append(photo);

      const frame = document.createElement("div");
      frame.className = "soldier-frame";
      frame.dataset.layoutItem = "frame-and-rules";
      frame.setAttribute("aria-hidden", "true");
      board.append(frame);

      const makeLine = (name, text, box, options = {}) => {
        const element = document.createElement("div");
        element.className = `specimen ${options.className || ""}`;
        element.dataset.layoutItem = name;
        if (options.display !== false) element.dataset.displayItem = "true";
        element.textContent = text;
        board.append(element);
        window.SupportLayout.fitLine(element, {
          width: board.clientWidth * box.width,
          height: board.clientHeight * box.height,
          maxSize: board.clientHeight * box.max * (options.scale || 1),
          minSize: board.clientHeight * box.min,
          tracking: options.tracking ?? state.tracking,
        });
        element.style.letterSpacing = `${options.tracking ?? state.tracking}em`;
        return element;
      };

      const year = makeLine("year", props.year ?? state.year ?? "1935", {
        width: .37, height: .145, max: .245, min: .09,
      }, { className: "year", scale: state.yearScale, tracking: -.035 });
      year.style.transform = "scaleX(1.08)";

      const lines = [
        props.thisLine ?? state.thisLine,
        props.warLine ?? state.warLine,
        props.uselessLine ?? state.uselessLine,
      ];
      lines.forEach((text, index) => {
        const line = makeLine(`headline-${index + 1}`, text, {
          width: .41, height: .087, max: .105, min: .055,
        }, {
          className: `headline headline-${index + 1}`,
          scale: state.headlineScale,
          tracking: -.035,
        });
      });

      const headlineRows = [...board.querySelectorAll(".headline")];
      window.SupportLayout.fitStack(headlineRows, {
        name: "soldier-headline",
        board,
        left: .53,
        top: .265,
        width: .41,
        height: .285,
        gap: .015,
        align: "center",
        maxSize: board.clientHeight * .105 * Number(props.headlineScale ?? state.headlineScale ?? 1),
        minSize: board.clientHeight * .055,
        tracking: Number(props.tracking ?? state.tracking ?? -.035),
      });

      const stripDigits = makeLine("digit-strip", props.digits ?? state.digits ?? "1234567890", {
        width: .36, height: .05, max: .072, min: .04,
      }, { className: "glyph-strip digits", scale: state.stripScale, tracking: -.02 });
      stripDigits.style.fontStyle = "italic";
      stripDigits.style.fontWeight = "600";
      stripDigits.style.transform = "translateX(-50%)";

      const symbolCopy = String(props.symbols ?? state.symbols ?? "!?$¢€£&");
      const stripSymbols = makeLine("symbol-strip", symbolCopy, {
        width: .43, height: .05, max: .06, min: .04,
      }, { className: "glyph-strip symbols", scale: state.stripScale, tracking: .20 });
      stripSymbols.replaceChildren(...[...symbolCopy].map((character) => {
        const glyph = document.createElement("span");
        glyph.textContent = character;
        return glyph;
      }));
      stripSymbols.style.gap = ".11em";
      stripSymbols.style.fontStyle = "italic";
      stripSymbols.style.fontWeight = "600";
      stripSymbols.style.transform = "translateX(-50%)";
    },
    getContrast() { return window.SupportLayout.contrast("#f5f3ed", "#070809"); },
    getWarnings() { return design.warnings || []; },
  };
  window.Soldier32 = design;
})();
