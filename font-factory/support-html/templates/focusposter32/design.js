(function () {
  const sideNotes = [
    ["Keep", .056, .058, .050], ["Forward", .041, .080, .092],
    ["Moving", .056, .080, .140], ["Stay", .041, .047, .165],
    ["Focused", .051, .078, .274],
    ["Design", .956, .055, .061], ["Word", .941, .046, .090],
    ["Concept", .957, .086, .153], ["Art", .941, .035, .182],
    ["For", .952, .029, .276],
  ];
  const quoteColumns = [
    { key: "leftQuote", left: .035, width: .195, color: "red", fallback: "Staying\nAvoiding\nAbout\nThat\nYour" },
    { key: "innerQuote", left: .265, width: .275, color: "ink", fallback: "Focused\nDistractions,\nEmbracing\nComes From\nTruest" },
    { key: "isQuote", left: .558, width: .072, color: "red", fallback: "Is" },
    { key: "notQuote", left: .686, width: .112, color: "red", fallback: "Not\nBut\nThe" },
    { key: "outerQuote", left: .817, width: .164, color: "red", fallback: "About\nClarity\nPursuing\nIntentions." },
  ];

  function titleCase(value) {
    return String(value ?? "").trim().split(/(\s+)/u).map((part) => {
      if (!part || /^\s+$/u.test(part)) return part;
      const match = part.match(/^([^\p{L}\p{N}]*)([\p{L}\p{N}])([\s\S]*)$/u);
      if (!match) return part;
      return match[1] + match[2].toLocaleUpperCase("en") + match[3].toLocaleLowerCase("en");
    }).join("");
  }

  const design = {
    id: "focusposter32",
    title: "Focus Poster",
    defaults: {
      headline: "Focused",
      titleScale: 1,
      titleTop: .423,
      tracking: -.035,
      quoteScale: 1,
      quoteTop: .651,
      eyeScale: 1,
      leftQuote: quoteColumns[0].fallback,
      innerQuote: quoteColumns[1].fallback,
      isQuote: quoteColumns[2].fallback,
      notQuote: quoteColumns[3].fallback,
      outerQuote: quoteColumns[4].fallback,
    },
    controls: [
      { key: "headline", label: "Headline (One Word)", type: "text" },
      { key: "titleScale", label: "Headline Scale", min: .90, max: 1.08, step: .01 },
      { key: "titleTop", label: "Headline Position", min: .400, max: .445, step: .001 },
      { key: "tracking", label: "Headline Spacing", min: -.06, max: -.005, step: .001 },
      { key: "quoteScale", label: "Quote Scale", min: .85, max: 1.08, step: .01 },
      { key: "quoteTop", label: "Quote Position", min: .635, max: .68, step: .001 },
      { key: "eyeScale", label: "Eye Detail Scale", min: .96, max: 1.08, step: .01 },
      { key: "leftQuote", label: "Left Column", type: "textarea", rows: 5 },
      { key: "innerQuote", label: "Inner Column", type: "textarea", rows: 5 },
      { key: "isQuote", label: "Center Word", type: "textarea", rows: 2 },
      { key: "notQuote", label: "Next Column", type: "textarea", rows: 3 },
      { key: "outerQuote", label: "Right Column", type: "textarea", rows: 4 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const titleScale = Number(props.titleScale ?? state.titleScale ?? 1);
      const titleTop = Number(props.titleTop ?? state.titleTop ?? .423);
      const tracking = Number(props.tracking ?? state.tracking ?? -.035);
      const quoteScale = Number(props.quoteScale ?? state.quoteScale ?? 1);
      const quoteTop = Number(props.quoteTop ?? state.quoteTop ?? .651);
      const eyeScale = Number(props.eyeScale ?? state.eyeScale ?? 1);
      board.style.setProperty("--focus-eye-scale", String(eyeScale));
      board.style.setProperty("--focus-title-top", `${titleTop * 100}%`);
      board.style.setProperty("--focus-tracking", `${tracking}em`);

      const photo = document.createElement("img");
      photo.className = "focus-photo";
      photo.src = "../../../support-references/materials/T28576_06_soft-focus-portrait.png";
      photo.alt = "";
      photo.draggable = false;
      photo.dataset.layoutItem = "soft-focus-portrait";
      board.append(photo);

      const wash = document.createElement("div");
      wash.className = "focus-wash";
      wash.setAttribute("aria-hidden", "true");
      board.append(wash);

      const eyeRow = document.createElement("div");
      eyeRow.className = "focus-eye-row";
      eyeRow.dataset.layoutItem = "framed-eye-detail";
      const eye = document.createElement("img");
      eye.className = "focus-eye-art";
      eye.src = "../../../support-references/materials/T28576_06_eye-detail.png";
      eye.alt = "";
      eye.draggable = false;
      eyeRow.append(eye);
      board.append(eyeRow);

      const headlineRow = document.createElement("div");
      headlineRow.className = "focus-headline-row";
      headlineRow.style.top = `${titleTop * 100}%`;
      headlineRow.dataset.layoutItem = "headline-row";
      const headline = document.createElement("span");
      headline.className = "focus-headline";
      headline.textContent = titleCase(props.headline ?? state.headline ?? "Focused");
      headline.dataset.layoutItem = "headline";
      headline.dataset.displayItem = "true";
      headlineRow.append(headline);
      board.append(headlineRow);

      const headlineSize = window.SupportLayout.fitLine(headline, {
        width: board.clientWidth * .93 * .985,
        height: board.clientHeight * .215 * .9,
        maxSize: board.clientHeight * .225 * titleScale,
        minSize: board.clientHeight * .105,
        tracking,
        inkAware: true,
      });

      const columnSizes = [];
      const allColumnLabels = [];
      for (const [columnIndex, column] of quoteColumns.entries()) {
        const text = props[column.key] ?? props.columns?.[quoteColumns.indexOf(column)]
          ?? state[column.key] ?? column.fallback;
        const rows = String(text).split(/\r?\n/u).map(titleCase).filter(Boolean);
        const labels = [];
        rows.forEach((word, index) => {
          const row = document.createElement("div");
          row.className = "focus-column-row";
          row.style.left = `${column.left * 100}%`;
          const offsets = [0, .018, .055, .027, .01];
          row.style.top = `${(quoteTop + offsets[columnIndex] + index * .064) * 100}%`;
          row.style.width = `${column.width * 100}%`;
          row.style.height = "5.3%";
          row.dataset.layoutItem = `${column.key}-${index + 1}-row`;
          const label = document.createElement("span");
          label.className = `focus-quote focus-quote--${column.color}`;
          label.textContent = word;
          label.dataset.layoutItem = `${column.key}-${index + 1}`;
          row.append(label);
          board.append(row);
          labels.push(label);
          allColumnLabels.push(label);
        });
        if (labels.length) {
          const size = window.SupportLayout.fitLinesTogether(labels, {
            width: board.clientWidth * column.width * .97,
            height: board.clientHeight * .051 * .86,
            maxSize: board.clientHeight * .055 * quoteScale,
            minSize: board.clientHeight * .020,
            tracking: -.018,
            inkAware: true,
          });
          columnSizes.push(size);
        }
      }

      const sharedQuoteSize = Math.min(...columnSizes);
      for (const label of allColumnLabels) label.style.fontSize = `${sharedQuoteSize}px`;

      for (const [word, centerX, width, centerY] of sideNotes) {
        const row = document.createElement("div");
        row.className = "focus-side-word";
        row.style.left = `${(centerX - width / 2) * 100}%`;
        row.style.top = `${(centerY - .022 / 2) * 100}%`;
        row.style.width = `${width * 100}%`;
        row.style.height = "2.2%";
        row.dataset.layoutItem = `edge-note-${word.toLowerCase()}`;
        const label = document.createElement("span");
        label.className = "focus-side-label";
        label.textContent = titleCase(word);
        row.append(label);
        board.append(row);
      }

      design.headlineFontSize = `${headlineSize}px`;
      design.quoteFontSize = `${sharedQuoteSize}px`;
    },
    getContrast() {
      return window.SupportLayout.contrast("#f5000c", "#ffffff");
    },
    contrastException: {
      minimum: 3,
      rationale: "The oversized red headline and red quote columns preserve the source poster's ink over its lightened portrait.",
    },
    getWarnings() { return design.warnings || []; },
  };
  window.FocusPoster32 = design;
})();
