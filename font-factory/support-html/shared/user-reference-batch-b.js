(function () {
  const root = "../../../support-references/";
  const batch = "materials/user-batch-2026-10-20-b/";
  const templates = {
    saucystack32: {
      title: "Saucy Stack fast-food poster", source: "T34327_05", style: "saucystack", bg: `${batch}T34327_05-clean-bg.png`,
      fields: [
        { key: "headline", label: "Top line", value: "LET'S HAVE", box: [.15,.08,.70,.12], squareBox: [.10,.035,.80,.09], squareSize: 180, size: 145, color: "#23792b", weight: 800 },
        { key: "line2", label: "Banner line", value: "SAUCY STACK", box: [.16,.23,.68,.17], squareBox: [.12,.12,.76,.12], squareSize: 215, size: 180, color: "#f9dc28", weight: 800 },
        { key: "line3", label: "Bottom line", value: "AFTER THIS!", box: [.15,.42,.70,.12], squareBox: [.10,.25,.80,.085], squareSize: 185, size: 150, color: "#23792b", weight: 800 },
      ], note: "Three bold lines sit above the snack photo, with the middle phrase on a red banner."
    },
    anteliascard32: {
      title: "Antelias tilted studio card", source: "T33743_05", style: "anteliascard", bg: `${batch}T33743_05-clean-bg.png`,
      fields: [
        { key: "caption", label: "Studio label", value: "BUSINESS TYPOGRAPHY", box: [.22,.18,.34,.07], size: 22, color: "#282624", tracking: .12, label: true },
        { key: "headline", label: "Studio name", value: "Antelias", box: [.10,.31,.80,.32], squareBox: [.10,.30,.80,.29], size: 350, color: "#151312", tracking: -.04 },
        { key: "footer", label: "Contact line", value: "BRANDING · VISUAL WITH PURPOSE", box: [.17,.67,.66,.08], size: 27, color: "#292725", tracking: .09, label: true },
      ], note: "A dark script name fills a lightly tilted white studio card with small, letter-spaced business details."
    },
    peacebreath32: {
      title: "Keep your mind open to peace poster", source: "T15926_01", style: "peacebreath", bg: `${batch}T15926_01-clean-bg.png`, literalKeys: ["headline", "caption"],
      fields: [
        { key: "headline", label: "Main message", value: "Keep your mind\nopen to PEACE\nMake space to\nslow down and\nBREATHE", box: [.11,.12,.78,.76], squareBox: [.08,.12,.84,.76], size: 240, squareSize: 240, color: "#ffd05a", tracking: -.025 },
        { key: "caption", label: "Small heading", value: "PEACEFUL ISLAND FONT DUO", box: [.27,.06,.46,.05], squareBox: [.27,.035,.46,.045], size: 23, color: "#ffd16a", tracking: .14, label: true },
      ], note: "A stacked golden message sits inside a dark rounded screen over a quiet sea-and-sky photograph."
    },
    nyccoffee32: {
      title: "New York coffee shops feature", source: "T15926_02", style: "nyccoffee", bg: `${batch}T15926_02-clean-bg.png`,
      fields: [
        { key: "headline", label: "Feature headline", value: "New York's\nTop Ten\nCoffee Shops", box: [.18,.16,.64,.62], size: 210, color: "#fffaf4", tracking: -.025, weight: 700 },
        { key: "caption", label: "Small heading", value: "PAPERCLIP BRAND FONT DUO", box: [.28,.07,.44,.05], size: 21, color: "#f5eee7", tracking: .12, label: true },
      ], note: "A compact white feature headline overlays a warm café photograph inside a video-frame treatment."
    },
    afterhours32: {
      title: "After Hours spring collection", source: "T15926_03", style: "afterhours", bg: `${batch}T15926_03-clean-bg.png`,
      fields: [
        { key: "headline", label: "Collection name", value: "after hours", box: [.18,.30,.64,.22], squareBox: [.09,.07,.82,.20], squareSize: 275, size: 230, color: "#ffbd4d", tracking: -.045 },
        { key: "caption", label: "Collection line", value: "CASUAL SPRING COLLECTION", box: [.25,.53,.50,.08], squareBox: [.15,.73,.70,.07], squareSize: 36, size: 33, color: "#ffe0a0", tracking: .09, label: true },
        { key: "footer", label: "Season marker", value: "SS · 2022", box: [.38,.69,.24,.07], squareBox: [.34,.85,.32,.07], squareSize: 42, size: 38, color: "#ffc85e", tracking: .08, label: true },
      ], note: "Golden script and compact collection details sit across the grass-and-golf portrait scene."
    },
    outofoffice32: {
      title: "Out of Office vacation poster", source: "T15926_06", style: "outofoffice", bg: `${batch}T15926_06-clean-bg.png`,
      fields: [
        { key: "caption", label: "Top line", value: "GREETINGS FROM", box: [.29,.08,.42,.07], squareBox: [.22,.07,.56,.075], squareSize: 31, size: 27, color: "#fff3df", tracking: .14, label: true },
        { key: "headline", label: "Main phrase", value: "OUT OF\nOFFICE", box: [.17,.20,.66,.42], squareBox: [.10,.18,.80,.45], squareSize: 335, size: 290, color: "#f7a433", weight: 800, tracking: -.035 },
        { key: "footer", label: "Bottom line", value: "WE'RE ON VACATION", box: [.27,.65,.46,.07], squareBox: [.22,.67,.56,.075], squareSize: 35, size: 31, color: "#ffd08a", tracking: .11, label: true },
      ], note: "A warm orange two-line title stands above a canyon photograph with restrained vacation captions."
    },
    skincareroutine32: {
      title: "Night skincare routine video card", source: "T15926_07", style: "skincareroutine", bg: `${batch}T15926_07-clean-bg.png`, literalKeys: ["headline"],
      fields: [
        { key: "headline", label: "Routine title", value: "night & skincare\nROUTINE", box: [.06,.34,.88,.36], squareBox: [.055,.39,.89,.39], squareSize: 360, size: 340, color: "#fffaf5", tracking: -.035 },
        { key: "caption", label: "Creator label", value: "CLARA LIFE", box: [.77,.09,.16,.07], squareBox: [.75,.08,.20,.07], squareSize: 31, size: 27, color: "#ffbd54", tracking: .04, label: true },
      ], note: "A white two-line routine title sits low over a skincare portrait, leaving the face clear."
    },
    youlookgood32: {
      title: "You look good today ocean card", source: "T15926_08", style: "youlookgood", bg: `${batch}T15926_08-clean-bg.png`, literalKeys: ["headline"],
      fields: [
        { key: "headline", label: "Main phrase", value: "you look\ngood today", box: [.19,.24,.62,.46], squareBox: [.08,.22,.84,.47], squareSize: 350, size: 270, color: "#ffc44f", tracking: -.035 },
        { key: "caption", label: "Small heading", value: "PEACEFUL BRAND FONT DUO", box: [.27,.08,.46,.06], squareBox: [.22,.07,.56,.065], squareSize: 26, size: 23, color: "#f8f4e9", tracking: .13, label: true },
      ], note: "Two golden script lines float over a soft ocean surface inside a rounded video-frame treatment."
    },
    spiritadventure32: {
      title: "The Spirit of Adventure photo quote", source: "T9403_01", style: "spiritadventure", bg: `${batch}T9403_01-clean-bg.png`, literalKeys: ["headline"],
      fields: [
        { key: "headline", label: "Quote", value: "the Spirit\nof\nAdventure", box: [.12,.10,.76,.78], squareBox: [.08,.05,.84,.89], squareSize: 330, size: 300, color: "#fffdf8", tracking: -.045 },
      ], note: "A tall white script phrase follows the vertical sweep of a blue glacier landscape."
    },
    dreamfollow32: {
      title: "Follow your dreams mountain quote", source: "T9403_02", style: "dreamfollow", bg: `${batch}T9403_02-clean-bg.png`, literalKeys: ["headline"],
      fields: [
        { key: "headline", label: "Quote", value: "follow your dreams\nno matter what!", box: [.04,.55,.92,.40], squareBox: [.04,.55,.92,.40], squareSize: 300, size: 280, color: "#fffdf8", tracking: -.04 },
      ], note: "A low white script quote sits below a seated figure looking toward a night mountain sky."
    },
    angelinastyle32: {
      title: "Angelina Jolie style and fashion photo", source: "T9403_03", style: "angelinastyle", bg: `${batch}T9403_03-clean-bg.png`, squareBg: `${batch}T9403_03-clean-bg.png`,
      fields: [
        { key: "headline", label: "Feature title", value: "Angelina Jolie", box: [.05,.60,.62,.19], squareBox: [.035,.055,.54,.20], squareSize: 205, size: 185, color: "#f9f6f0", tracking: -.035 },
        { key: "caption", label: "Subtitle", value: "STYLE AND FASHION", box: [.09,.79,.48,.07], squareBox: [.05,.265,.48,.065], squareSize: 33, size: 30, color: "#eee8dc", tracking: .12, label: true },
      ], note: "A pale script name and small uppercase subtitle occupy the open lower-left beside the fashion portrait."
    },
    comesnatural32: {
      title: "Do what comes natural beach quote", source: "T9403_04", style: "comesnatural", bg: `${batch}T9403_04-clean-bg.png`,
      fields: [
        { key: "headline", label: "Quote", value: "Do\nWhat\nComes\nNatural", box: [.06,.08,.50,.84], size: 320, color: "#151515", tracking: -.045 },
      ], note: "A narrow black script stack fills the open left side while the shoreline figure stays visible at right."
    },
    calmafterstorm32: {
      title: "Calm after the storm floral quote", source: "T9403_05", style: "calmafterstorm", bg: `${batch}T9403_05-clean-bg.png`,
      fields: [
        { key: "headline", label: "Quote", value: "calm after\nthe storm\nkind of\nSunday", box: [.22,.12,.56,.76], size: 210, color: "#fffdf9", tracking: -.035 },
      ], note: "A centered white script stack sits over a soft, muted botanical photograph."
    },
    beachclub32: {
      title: "Beach Club editorial title card", source: "T18889_00", style: "beachclub", bg: "originals/user-batch-2026-10-20-b/T18889_00.jpg",
      fields: [
        { key: "caption", label: "Overline", value: "INTRODUCING", box: [.14,.20,.49,.08], squareBox: [.16,.29,.62,.07], squareSize: 35, size: 29, color: "#f7f4dc", tracking: .24, label: true },
        { key: "headline", label: "Main phrase", value: "Beach\nClub", box: [.07,.29,.59,.42], squareBox: [.10,.37,.66,.34], squareSize: 365, size: 295, color: "#fff02f", tracking: -.055 },
      ], note: "The source title is replaced within a turquoise panel over the editorial beach photograph; the original photo remains beside the remake."
    },
    splitampersand32: {
      title: "Kulkokale and Sagu Exora split specimen", source: "T16351_04", style: "splitampersand", bg: null,
      fields: [
        { key: "headline", label: "Main phrase", value: "Letters\nMatter", box: [.04,.14,.42,.72], size: 220, color: "#101010", tracking: -.035, weight: 700 },
        { key: "glyph", label: "Ampersand", value: "&", box: [.53,.10,.42,.78], size: 520, color: "#fff", tracking: -.04 },
      ], note: "A bold pangram occupies the white left half and a single oversized ampersand fills the black right half."
    },
    setrum32: {
      title: "Setrum futuristic corridor poster", source: "T16351_08", style: "setrum", bg: `${batch}T16351_08-clean-bg.png`, squareBg: `${batch}T16351_08-clean-bg-square-adapted.png`,
      fields: [
        { key: "headline", label: "Product name", value: "SETRUM", box: [.18,.07,.64,.23], squareBox: [.08,.08,.84,.22], squareSize: 320, size: 275, color: "#fff", weight: 800, tracking: -.04 },
        { key: "date", label: "Date", value: "18.05.23", box: [.18,.69,.64,.23], squareBox: [.10,.82,.80,.12], squareSize: 225, size: 205, color: "#e42e45", tracking: .09 },
      ], note: "A white geometric title and red outlined date frame a narrow blue-lit corridor photograph."
    },
    nectarambience32: {
      title: "Nector Ambience sci-fi poster", source: "T18612_01", style: "nectarambience", bg: `${batch}T18612_01-clean-bg.png`,
      fields: [
        { key: "headline", label: "Main phrase", value: "Nector Ambience", box: [.03,.12,.94,.21], squareBox: [.07,.025,.86,.12], squareSize: 230, size: 350, color: "#72e9c1", tracking: -.045, weight: 300 },
      ], note: "A single horizontal mint title uses the upper space above a neon ring on a dark magenta science-fiction panel."
    },
    fluorescentduo32: {
      title: "Fluorescent Adolescent and Normal Behaviour split poster", source: "T19863_07", style: "fluorescentduo", bg: `${batch}T19863_07-clean-bg.png`,
      fields: [
        { key: "headline", label: "Left poster title", value: "Fluorescent\nAdolescent", box: [.07,.12,.40,.40], size: 180, color: "#fff12d", weight: 800, tracking: -.025 },
        { key: "rightTitle", label: "Right poster title", value: "NRML\nBHVR", box: [.53,.12,.40,.40], size: 210, color: "#fff12d", tracking: -.035 },
      ], note: "Two saturated portrait cards sit side by side with separate yellow titles at their tops."
    },
    sacharon32: {
      title: "Sacharon pop-art title card", source: "T19863_00", style: "sacharon", bg: `${batch}T19863_00-clean-bg.png`,
      fields: [
        { key: "headline", label: "Main title", value: "SACHARON", box: [.08,.48,.84,.30], squareBox: [.08,.42,.84,.31], size: 340, color: "#ffdd27", weight: 900, tracking: -.04 },
      ], note: "A heavy yellow display title sits across the lower portion of a vivid portrait and neon-green shapes."
    },
    lastnightsweden32: {
      title: "Last Night in Sweden poster", source: "T7553_01", style: "lastnightsweden", bg: `${batch}T7553_01-clean-bg.png`,
      fields: [
        { key: "headline", label: "Main phrase", value: "LAST NIGHT\nIN SWEDEN", box: [.12,.20,.76,.54], size: 300, color: "#ffca32", tracking: -.04 },
      ], note: "A rough yellow two-line brush title sits on a deep-blue field beside a vertical yellow stripe."
    },
    crywolf32: {
      title: "Cry Wolf forest title card", source: "T7553_00", style: "crywolf", bg: `${batch}T7553_00-clean-bg.png`,
      fields: [
        { key: "headline", label: "Main phrase", value: "CRY\nWOLF", box: [.12,.18,.76,.60], squareBox: [.12,.18,.76,.60], size: 380, color: "#f4f1ec", tracking: -.04, weight: 800 },
      ], note: "A compact white brush phrase sits over the dark vertical forest texture."
    },
  };

  function makeField(board, field, state, config) {
    const value = String(state.props?.[field.key] ?? state[field.key] ?? field.value);
    const isLabel = field.key === "caption" || field.key === "footer";
    const element = document.createElement("div");
    element.className = `urb-field${isLabel ? " urb-label" : ""}`;
    element.dataset.layoutItem = `${config.style}-${field.key}`;
    if (!isLabel) element.dataset.displayItem = "true";
    element.textContent = value;
    const square = board.dataset.ratio === "1x1" && config.bg;
    const box = square
      ? (field.squareBox || [field.box[0], 1 / 6 + field.box[1] * 2 / 3, field.box[2], field.box[3] * 2 / 3])
      : field.box;
    element.style.left = `${box[0] * 100}%`;
    element.style.top = `${box[1] * 100}%`;
    element.style.width = `${box[2] * 100}%`;
    element.style.height = `${box[3] * 100}%`;
    element.style.color = field.color;
    element.style.fontWeight = String(field.weight || (isLabel ? 600 : 400));
    element.style.letterSpacing = `${field.tracking || 0}em`;
    element.style.fontFamily = isLabel ? "Arial, sans-serif" : "SupportDisplay, Arial, sans-serif";
    element.dataset.originalFontSize = String(field.size);
    board.append(element);
    const scale = Number(state.scale ?? 1);
    window.SupportLayout.fitLine(element, {
      width: board.clientWidth * box[2] * (isLabel ? .90 : .94),
      height: board.clientHeight * box[3] * (isLabel ? .76 : .90),
      maxSize: (square && field.squareSize ? field.squareSize : field.size) * scale,
      minSize: isLabel ? 10 : 8,
      tracking: field.tracking || 0,
    });
    element.style.letterSpacing = `${field.tracking || 0}em`;
  }

  window.UserReferenceBatchB = {
    ids: Object.keys(templates),
    create(id) {
      const config = templates[id];
      if (!config) throw new Error(`Unknown reference template: ${id}`);
      const design = {
        id,
        title: config.title,
        literalKeys: config.literalKeys || [],
        defaults: Object.fromEntries(config.fields.map((field) => [field.key, field.value]).concat([["scale",1]])),
        controls: config.fields.map((field) => ({ key: field.key, label: field.label, type: field.value.includes("\n") ? "textarea" : "text", value: field.value, rows: 3 })).concat([
          { key: "scale", label: "Display size", min: .55, max: 1.18, step: .01, value: 1 },
        ]),
        contrastException: { minimum: 1.4, rationale: "The source composition uses decorative lettering over its original imagery or colored field; the reference plate retains its palette and picture." },
        render(board, state) {
          board.replaceChildren();
          board.className = `user-reference-board-b user-reference-${config.style}`;
          board.style.backgroundColor = config.backgroundColor || "#101014";
          if (config.bg) {
            const img = document.createElement("img");
            img.className = "urb-background";
            img.alt = "";
            const imagePath = board.dataset.ratio === "1x1" && config.squareBg
              ? config.squareBg
              : board.dataset.ratio === "1x1" && config.bg.startsWith(batch)
                ? config.bg.replace("-clean-bg.png", "-clean-bg-square.png")
                : config.bg;
            img.src = `${root}${imagePath}`;
            img.dataset.layoutItem = `${config.style}-background`;
            board.append(img);
          }
          for (const field of config.fields) makeField(board, field, state, config);
          const accent = document.createElement("div");
          accent.className = "urb-accent";
          accent.setAttribute("aria-hidden", "true");
          board.append(accent);
          if (config.style === "beachclub") {
            const badgeMask = document.createElement("div");
            badgeMask.className = "urb-source-mask";
            badgeMask.setAttribute("aria-hidden", "true");
            board.append(badgeMask);
          }
          design.fitWarnings = [...board.querySelectorAll("[data-fit-failure]")].map((element) =>
            `${element.dataset.layoutItem} copy is too large for its reserved area; shorten it or use a narrower font.`);
        },
        getContrast() { return 2.0; },
        getWarnings() { return design.fitWarnings || []; },
      };
      return design;
    },
    getConfig(id) { return templates[id]; },
  };
})();
