(function () {
  const root = "../../../support-references/";
  const templates = {
    palmello32: {
      title: "Palmello script wordmark", source: "T33329_00", style: "palmello", bg: null,
      fields: [{ key: "headline", label: "Main word", value: "Palmello", box: [.08,.30,.84,.42], size: 390, color: "#5c9b92", tracking: -.025 }],
      note: "A quiet deep-green field and a single soft teal script word."
    },
    quietattempt32: {
      title: "Quiet Attempt portrait poster", source: "T32243_00", style: "quietattempt", bg: "materials/user-batch-2026-10-20/T32243_00-clean-bg.png",
      fields: [
        { key: "headline", label: "Main phrase", value: "Quiet\nAttempt", box: [.17,.20,.66,.49], size: 360, color: "#ead2d0", tracking: -.035 },
        { key: "caption", label: "Small caption", value: "Soft Handwritten Script", box: [.19,.73,.62,.09], size: 58, color: "#ead2d0", tracking: .12, label: true }
      ], note: "Two pale script lines sit over the central dark portrait silhouette, with a small letter-spaced caption below."
    },
    hushglow32: {
      title: "Hush and Glow close-up poster", source: "T32243_06", style: "hushglow", bg: "materials/user-batch-2026-10-20/T32243_06-clean-bg.png",
      fields: [
        { key: "headline", label: "Main phrase", value: "Hush & Glow", box: [.045,.36,.91,.28], size: 300, color: "#f15a9d", tracking: -.045 },
        { key: "caption", label: "Supporting line", value: "For Glances, Not Statements", box: [.24,.68,.52,.12], size: 88, color: "#f28fbd", tracking: -.015 }
      ], note: "A wide pink script line crosses the dark close-up, with a smaller two-line caption underneath."
    },
    italianhorror32: {
      title: "Italian Horror broadside", source: "T15503_08", style: "italianhorror", bg: "materials/user-batch-2026-10-20/T15503_08-clean-bg.png",
      fields: [
        { key: "headline", label: "Main line", value: "Italian Horror", box: [.025,.36,.95,.28], size: 325, color: "#f5f1ef", tracking: -.035 },
        { key: "caption", label: "Subtitle", value: "Master Series", box: [.20,.64,.60,.16], size: 132, color: "#e3d4d3", tracking: .18, label: true }
      ], note: "A broad white brush title sits across a red-black horror still, with narrow spaced lettering below."
    },
    dreamwarriors32: {
      title: "Dream Warriors horror one-sheet", source: "T15503_09", style: "dreamwarriors", bg: "materials/user-batch-2026-10-20/T15503_09-clean-bg.png",
      fields: [
        { key: "headline", label: "Main phrase", value: "Dream\nWarriors", box: [.20,.16,.65,.58], size: 360, color: "#f5f1ef", tracking: -.055 },
        { key: "caption", label: "Lower caption", value: "A Midnight Feature", box: [.55,.79,.38,.08], size: 42, color: "#f4d3d2", tracking: .04, label: true }
      ], note: "The large two-line white brush phrase fills the center-right while a small red-lit figure stays visible at lower left."
    },
    nesting32: {
      title: "The Nesting horror one-sheet", source: "T15503_11", style: "nesting", bg: "materials/user-batch-2026-10-20/T15503_11-clean-bg.png",
      fields: [
        { key: "headline", label: "Main word", value: "Nesting", box: [.025,.20,.76,.45], size: 560, color: "#f7f3ef", tracking: -.045 },
        { key: "pretitle", label: "Top word", value: "The", box: [.30,.095,.22,.15], size: 170, color: "#f7f3ef", tracking: -.04 },
        { key: "caption", label: "Credit line", value: "A Chilling Story", box: [.18,.69,.52,.10], size: 50, color: "#d8c7c4", tracking: .12, label: true }
      ], note: "A large white brush title sits over a textured crimson scene, with a fine centered credit beneath."
    },
    erotica32: {
      title: "Erotica red title card", source: "T15503_12", style: "erotica", bg: "materials/user-batch-2026-10-20/T15503_12-clean-bg.png",
      fields: [{ key: "headline", label: "Main word", value: "Erotica", box: [.09,.30,.82,.42], size: 390, color: "#e23d4d", tracking: -.045 }],
      note: "One red brush word and its long underline sit on a near-black red-lit still."
    },
    conspiracytheory32: {
      title: "Conspiracy Theory poster", source: "T15503_13", style: "conspiracytheory", bg: "materials/user-batch-2026-10-20/T15503_13-clean-bg.png",
      fields: [{ key: "headline", label: "Main phrase", value: "Conspiracy\nTheory", box: [.16,.16,.70,.61], size: 350, color: "#f3efec", tracking: -.045 }],
      note: "A stacked white brush phrase overlays the red-black paper collage, leaving the scratched edge texture exposed."
    },
    overglow32: {
      title: "Overglow neon script card", source: "T16576_00", style: "overglow", bg: "materials/user-batch-2026-10-20/T16576_00-clean-bg.png",
      fields: [
        { key: "headline", label: "Main word", value: "Overglow", box: [.10,.34,.80,.31], size: 340, color: "#ed55ef", tracking: -.045 },
        { key: "caption", label: "Top caption", value: "Midnight Radio · 1985", box: [.30,.17,.40,.08], size: 42, color: "#f4e9fb", tracking: .18, label: true },
        { key: "footer", label: "Bottom caption", value: "A Retro Script Typeface", box: [.31,.72,.38,.08], size: 38, color: "#f4e9fb", tracking: .10, label: true }
      ], note: "A bright pink center word sits on a blue-violet star field with small, restrained top and bottom captions."
    },
    pinkvice32: {
      title: "Pink Vice retro car poster", source: "T16576_01", style: "pinkvice", bg: "materials/user-batch-2026-10-20/T16576_01-clean-bg.png",
      fields: [
        { key: "headline", label: "Main phrase", value: "Pink Vice", box: [.075,.25,.85,.31], size: 335, color: "#4168e8", tracking: -.065 },
        { key: "caption", label: "Small caption", value: "Retro Script", box: [.38,.82,.24,.06], size: 35, color: "#4f5d92", tracking: .09, label: true }
      ], note: "The blue script title with a pink offset shadow crosses the upper half above a low, centered pink sports car."
    },
    attitude32: {
      title: "Attitude teal fashion poster", source: "T16576_04", style: "attitude", bg: "materials/user-batch-2026-10-20/T16576_04-clean-bg.png",
      fields: [
        { key: "headline", label: "Main word", value: "Attitude", box: [.075,.39,.85,.27], size: 330, color: "#f2e2dc", tracking: -.06 },
        { key: "caption", label: "Top caption", value: "Retro Script Study", box: [.05,.07,.32,.07], size: 36, color: "#e5b8bb", tracking: .08, label: true },
        { key: "footer", label: "Bottom caption", value: "Teal Room · 1985", box: [.68,.87,.27,.06], size: 32, color: "#d9c5c1", tracking: .08, label: true }
      ], note: "A pale, shadowed script word crosses the teal fashion photograph while the model remains a secondary subject."
    },
    indieground32: {
      title: "Indieground foundry title card", source: "T16576_09", style: "indieground", bg: null,
      fields: [{ key: "headline", label: "Main phrase", value: "Indieground\nFont Foundry", box: [.12,.25,.76,.50], size: 300, color: "#4267d9", tracking: -.055 }],
      note: "A blue two-line script wordmark sits centered on a saturated pink field with a light offset shadow."
    },
    caramelsundae32: {
      title: "Caramel Sundae candy poster", source: "T36099_00", style: "caramelsundae", bg: "materials/user-batch-2026-10-20/T36099_00-clean-bg.png",
      fields: [
        { key: "headline", label: "Main phrase", value: "Caramel\nSundae", box: [.17,.28,.66,.40], size: 350, color: "#75401f", tracking: -.025 },
        { key: "caption", label: "Banner line", value: "Bold And Script Font Duo", box: [.24,.71,.52,.10], size: 64, color: "#fff1df", tracking: .035, label: true }
      ], note: "Two stacked words fill the torn-cream center panel above a coral ribbon on the striped candy background."
    },
    sweettreat32: {
      title: "Sweet Treat ice-cream poster", source: "T36099_07", style: "sweettreat", bg: "materials/user-batch-2026-10-20/T36099_07-clean-bg.png",
      fields: [
        { key: "line1", label: "Top word", value: "Sweet", box: [.40,.15,.53,.18], size: 215, color: "#75401f", tracking: -.02 },
        { key: "line2", label: "Middle word", value: "Treat", box: [.40,.36,.53,.18], size: 215, color: "#ed777e", tracking: -.02 },
        { key: "line3", label: "Bottom word", value: "Dreams", box: [.40,.57,.53,.18], size: 215, color: "#75401f", tracking: -.02 },
        { key: "caption", label: "Footer phrase", value: "Scoops · Smiles · Sundaes", box: [.44,.79,.48,.08], size: 56, color: "#e6787a", tracking: .02, label: true }
      ], note: "Three bold lines sit to the right of a smiling ice-cream cone illustration, framed by waffle corners."
    }
  };

  function makeField(board, field, state, config) {
    const value = String(state.props?.[field.key] ?? state[field.key] ?? field.value);
    const isLabel = field.key === "caption" || field.key === "footer";
    const element = document.createElement("div");
    element.className = `ur-field${isLabel ? " ur-label" : ""}`;
    element.dataset.layoutItem = `${config.style}-${field.key}`;
    if (!isLabel) element.dataset.displayItem = "true";
    element.textContent = value;
    const square = board.dataset.ratio === "1x1" && config.bg;
    // Square plates preserve the full 3:2 source in the middle two thirds;
    // place copy over that same source region after extending its background.
    const box = square
      ? [field.box[0], 1 / 6 + field.box[1] * 2 / 3, field.box[2], field.box[3] * 2 / 3]
      : field.box;
    element.style.left = `${box[0] * 100}%`;
    element.style.top = `${box[1] * 100}%`;
    element.style.width = `${box[2] * 100}%`;
    element.style.height = `${box[3] * 100}%`;
    element.style.color = field.color;
    element.style.letterSpacing = `${field.tracking || 0}em`;
    element.style.fontFamily = isLabel ? "Arial, sans-serif" : "SupportDisplay, Arial, sans-serif";
    element.dataset.originalFontSize = String(field.size);
    board.append(element);
    const scale = Number(state.scale ?? 1);
    // The measured box uses a 10% horizontal and 24% vertical safety inset so
    // unusually wide or tall glyphs shrink before they approach artwork edges.
    window.SupportLayout.fitLine(element, {
      width: board.clientWidth * box[2] * .90,
      height: board.clientHeight * box[3] * .76,
      maxSize: field.size * scale,
      minSize: isLabel ? 10 : 8,
      tracking: field.tracking || 0,
    });
    element.style.letterSpacing = `${field.tracking || 0}em`;
  }

  window.UserReferenceBatch = {
    ids: Object.keys(templates),
    create(id) {
      const config = templates[id];
      if (!config) throw new Error(`Unknown reference template: ${id}`);
      const design = {
        id,
        title: config.title,
        defaults: Object.fromEntries(config.fields.map((field) => [field.key, field.value]).concat([["scale",1]])),
        controls: config.fields.map((field) => ({ key: field.key, label: field.label, type: field.value.includes("\n") ? "textarea" : "text", value: field.value, rows: 2 })).concat([
          { key: "scale", label: "Display size", min: .55, max: 1.18, step: .01, value: 1 },
        ]),
        contrastException: { minimum: 1.4, rationale: "The source reference uses decorative lettering over its original textured or colored artwork; the text plate retains the reference palette and image." },
        render(board, state) {
          board.replaceChildren();
          board.className = `user-reference-board user-reference-${config.style}`;
          board.style.backgroundColor = config.bg ? "#111" : (id === "palmello32" ? "#173b24" : "#e743cb");
          if (config.bg) {
            const img = document.createElement("img");
            img.className = "ur-background";
            img.alt = "";
            const imagePath = board.dataset.ratio === "1x1"
              ? config.bg.replace("-clean-bg.png", "-clean-bg-square.png")
              : config.bg;
            img.src = `${root}${imagePath}`;
            img.dataset.layoutItem = `${config.style}-background`;
            board.append(img);
          }
          for (const field of config.fields) makeField(board, field, state, config);
          design.fitWarnings = [...board.querySelectorAll("[data-fit-failure]")].map((element) =>
            `${element.dataset.layoutItem} copy is too large for its reserved area; shorten it or use a narrower font.`);
          const accent = document.createElement("div");
          accent.className = "ur-accent";
          accent.setAttribute("aria-hidden", "true");
          board.append(accent);
        },
        getContrast() { return 2.0; },
        getWarnings() { return design.fitWarnings || []; },
      };
      return design;
    },
    getConfig(id) { return templates[id]; },
  };
})();
