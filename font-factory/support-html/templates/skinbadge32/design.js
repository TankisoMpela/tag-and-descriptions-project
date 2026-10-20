(function () {
  const design = {
    id: "skinbadge32",
    title: "Skin badge",
    defaults: { wordOne: "Skin", wordTwo: "Tribe", repeatScale: 1, headlineScale: 1, tracking: -0.015 },
    controls: [
      { key: "wordOne", label: "Top seal word", type: "text", value: "Skin" },
      { key: "wordTwo", label: "Bottom seal word", type: "text", value: "Tribe" },
      { key: "headlineScale", label: "Front seal scale", min: 0.78, max: 1.08, step: 0.01 },
      { key: "repeatScale", label: "Repeat pattern scale", min: 0.78, max: 1.14, step: 0.01 },
      { key: "tracking", label: "Display spacing", min: -0.04, max: 0.02, step: 0.005 },
    ],
    contrastException: {
      minimum: 1.8,
      rationale: "Cream lettering keeps the source skincare seal’s intentionally soft contrast on lavender.",
    },
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");

      const back = document.createElement("div");
      back.className = "skin-pattern";
      back.dataset.layoutItem = "skin-repeat-seal";
      const rows = document.createElement("div");
      rows.className = "skin-pattern-rows";
      const repeated = props.repeatWord || "Skin Tribe";
      for (let i = 0; i < 5; i += 1) {
        const row = document.createElement("div");
        row.className = "skin-pattern-row";
        row.textContent = repeated;
        rows.append(row);
      }
      back.append(rows);
      board.append(back);

      const badge = document.createElement("div");
      badge.className = "skin-badge";
      badge.dataset.layoutItem = "skin-front-seal";
      badge.innerHTML = `<svg class="skin-rim" viewBox="0 0 600 600" preserveAspectRatio="none" aria-hidden="true">
        <defs>
          <path id="skin-rim-top" d="M 52 300 A 248 248 0 0 1 548 300" />
          <path id="skin-rim-bottom" d="M 52 300 A 248 248 0 0 0 548 300" />
        </defs>
        <text class="skin-rim-text" text-anchor="middle"><textPath href="#skin-rim-top" startOffset="50%">Skin Care  •  Self Love  •  Skin Care</textPath></text>
        <text class="skin-rim-text" text-anchor="middle"><textPath href="#skin-rim-bottom" startOffset="50%">Self Love     Skin Care  •  Self Love</textPath></text>
      </svg>`;
      const wordOne = document.createElement("div");
      wordOne.className = "skin-word skin-word-top";
      wordOne.dataset.layoutItem = "skin-headline-top";
      wordOne.dataset.displayItem = "true";
      wordOne.textContent = props.wordOne ?? state.wordOne ?? "Skin";
      const wordTwo = document.createElement("div");
      wordTwo.className = "skin-word skin-word-bottom";
      wordTwo.dataset.layoutItem = "skin-headline-bottom";
      wordTwo.dataset.displayItem = "true";
      wordTwo.textContent = props.wordTwo ?? state.wordTwo ?? "Tribe";
      const stars = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      stars.classList.add("skin-stars");
      stars.setAttribute("viewBox", "0 0 600 600");
      stars.setAttribute("aria-hidden", "true");
      stars.innerHTML = '<path transform="translate(83 192) rotate(-20)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/><path transform="translate(202 75) rotate(-8)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/><path transform="translate(421 90) rotate(18)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/><path transform="translate(523 274) rotate(10)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/><path transform="translate(486 430) rotate(-14)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/><path transform="translate(313 528)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/><path transform="translate(113 461) rotate(12)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/><path transform="translate(68 312)" d="M0-8 2-2 8 0 2 2 0 8-2 2-8 0-2-2Z"/>';
      const underline = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      underline.setAttribute("viewBox", "0 0 400 60");
      underline.setAttribute("aria-hidden", "true");
      underline.classList.add("skin-underline");
      underline.innerHTML = '<path d="M10 33 C88 3 205 42 386 17 C397 15 400 21 385 25 C258 47 140 24 25 46 C13 48 7 42 10 33Z" />';
      badge.append(wordOne, wordTwo, stars, underline);
      board.append(badge);

      window.SupportLayout.fitStack([wordOne, wordTwo], {
        name: "skin-badge-headline",
        board,
        coordinateWidth: badge.clientWidth,
        coordinateHeight: badge.clientHeight,
        left: .13,
        top: .16,
        width: .74,
        height: .47,
        gap: .075,
        maxSize: board.clientHeight * .155 * Number(props.headlineScale ?? state.headlineScale ?? 1),
        minSize: board.clientHeight * .075,
        tracking: Number(props.tracking ?? state.tracking ?? -.015),
      });
      for (const row of rows.children) {
        window.SupportLayout.fitLine(row, {
          width: board.clientWidth * .54,
          height: board.clientHeight * .15,
          maxSize: 205 * state.repeatScale,
          minSize: 44,
          tracking: -.035,
        });
        row.style.letterSpacing = "-.035em";
      }
    },
    getContrast() { return window.SupportLayout.contrast("#fffdf7", "#b89bf9"); },
    getWarnings() { return design.warnings || []; },
  };
  window.SkinBadge32 = design;
})();
