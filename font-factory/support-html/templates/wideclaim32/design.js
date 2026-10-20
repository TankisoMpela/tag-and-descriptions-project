(function () {
  function titleCase(value) {
    return String(value ?? "").trim().split(/(\s+)/u).map((part) => {
      if (!part || /^\s+$/u.test(part)) return part;
      const match = part.match(/^([^\p{L}\p{N}]*)([\p{L}\p{N}])([\s\S]*)$/u);
      if (!match) return part;
      return match[1] + match[2].toLocaleUpperCase("en") + match[3].toLocaleLowerCase("en");
    }).join("");
  }

  const design = {
    id: "wideclaim32",
    title: "Wide Claim",
    defaults: {
      lineOne: "A Typeface Is",
      lineTwo: "A Visual Voice",
      wordOne: "Wide",
      wordTwo: "Serif",
      scale: 1,
      topTracking: -.04,
      displayTracking: -.05,
      wordOneTop: .355,
      wordTwoTop: .685,
    },
    controls: [
      { key: "lineOne", label: "Upper Line", type: "text" },
      { key: "lineTwo", label: "Second Line", type: "text" },
      { key: "wordOne", label: "First Display Word", type: "text" },
      { key: "wordTwo", label: "Second Display Word", type: "text" },
      { key: "scale", label: "Display Scale", min: .90, max: 1.08, step: .01 },
      { key: "topTracking", label: "Statement Spacing", min: -.06, max: -.005, step: .001 },
      { key: "displayTracking", label: "Display Word Spacing", min: -.08, max: -.015, step: .001 },
      { key: "wordOneTop", label: "First Word Position", min: .34, max: .39, step: .001 },
      { key: "wordTwoTop", label: "Second Word Position", min: .655, max: .715, step: .001 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const topTracking = Number(props.topTracking ?? state.topTracking ?? -.04);
      const displayTracking = Number(props.displayTracking ?? state.displayTracking ?? -.05);
      const scale = Number(props.scale ?? state.scale ?? 1);
      const wordOneTop = Number(props.wordOneTop ?? state.wordOneTop ?? .355);
      const wordTwoTop = Number(props.wordTwoTop ?? state.wordTwoTop ?? .685);
      board.style.setProperty("--wide-top-tracking", `${topTracking}em`);
      board.style.setProperty("--wide-display-tracking", `${displayTracking}em`);
      board.style.setProperty("--wide-word-one-top", `${wordOneTop * 100}%`);
      board.style.setProperty("--wide-word-two-top", `${wordTwoTop * 100}%`);

      function addLine(name, value, className, box, fontHeight, accentIs = false) {
        const row = document.createElement("div");
        row.className = `wide-line ${className}`;
        row.style.left = `${box.left * 100}%`;
        row.style.top = `${box.top * 100}%`;
        row.style.width = `${box.width * 100}%`;
        row.style.height = `${box.height * 100}%`;
        row.dataset.layoutItem = `${name}-row`;
        const text = document.createElement("span");
        text.className = "wide-line-text";
        text.dataset.layoutItem = name;
        text.dataset.displayItem = "true";
        text.style.letterSpacing = `${topTracking}em`;
        const words = titleCase(value).split(/(\s+)/u);
        for (const word of words) {
          if (!word || /^\s+$/u.test(word)) {
            text.append(document.createTextNode(word));
            continue;
          }
          const part = document.createElement("span");
          part.textContent = word;
          if (accentIs && word.replace(/[^\p{L}]/gu, "").toLocaleLowerCase("en") === "is") {
            part.className = "wide-line-word--accent";
          } else {
            part.className = "wide-line-word--ink";
          }
          text.append(part);
        }
        row.append(text);
        board.append(row);
        window.SupportLayout.fitLine(text, {
          width: board.clientWidth * box.width * .98,
          height: board.clientHeight * box.height * .88,
          maxSize: board.clientHeight * fontHeight * scale,
          minSize: board.clientHeight * .045,
          tracking: topTracking,
          inkAware: true,
        });
      }

      function addDisplayWord(name, value, className, box, alternating = false) {
        const row = document.createElement("div");
        row.className = `wide-display-row ${className}`;
        row.style.left = `${box.left * 100}%`;
        row.style.top = `${box.top * 100}%`;
        row.style.width = `${box.width * 100}%`;
        row.style.height = `${box.height * 100}%`;
        row.dataset.layoutItem = `${name}-row`;
        const text = document.createElement("span");
        text.className = "wide-display-text";
        text.dataset.layoutItem = name;
        text.dataset.displayItem = "true";
        text.style.letterSpacing = `${displayTracking}em`;
        const copy = [...titleCase(value).replace(/\s+/gu, "")];
        copy.forEach((character, index) => {
          const letter = document.createElement("span");
          letter.className = alternating
            ? (index % 2 ? "wide-display-letter--ink" : "wide-display-letter--red")
            : "wide-display-letter--red";
          letter.textContent = character;
          text.append(letter);
        });
        row.append(text);
        board.append(row);
        window.SupportLayout.fitLine(text, {
          width: board.clientWidth * box.width * .98,
          height: board.clientHeight * box.height * .88,
          maxSize: board.clientHeight * .48 * scale,
          minSize: board.clientHeight * .12,
          tracking: displayTracking,
          inkAware: true,
        });
      }

      addLine("opening-statement", props.lineOne ?? state.lineOne ?? "A Typeface Is",
        "wide-row-one", { left: .034, top: .036, width: .932, height: .172 }, .155, true);
      addLine("second-statement", props.lineTwo ?? state.lineTwo ?? "A Visual Voice",
        "wide-row-two", { left: .034, top: .217, width: .932, height: .138 }, .13);
      addDisplayWord("display-word-one", props.wordOne ?? state.wordOne ?? "Wide",
        "wide-word-one-row", { left: .035, top: wordOneTop, width: .93, height: .31 });
      addDisplayWord("display-word-two", props.wordTwo ?? state.wordTwo ?? "Serif",
        "wide-word-two-row", { left: .038, top: wordTwoTop, width: .924, height: .29 }, true);
    },
    getContrast() {
      return window.SupportLayout.contrast("#f5000c", "#ffffff");
    },
    contrastException: {
      minimum: 3,
      rationale: "The red specimen letters preserve the source poster's oversized red-on-white type treatment.",
    },
    getWarnings() { return design.warnings || []; },
  };
  window.WideClaim32 = design;
})();
