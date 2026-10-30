(function () {
  const root = "../../../support-references/";
  const materials = "materials/user-batch-2026-10-26-c/";
  const templates = {
    welcomemorning32: {
      title: "Welcome Morning storefront card",
      source: "T31141_04",
      style: "welcomemorning",
      photo: `${materials}T31141_04-storefront-strip.png`,
      squarePhoto: `${materials}T31141_04-storefront-strip-square.png`,
      lineOne: "WELCOME",
      lineTwo: "MORNING",
      note: "Two large left-aligned display lines and a small eight-point star sit over a vivid pink field, with a narrow storefront photograph below.",
    },
    esens32: {
      title: "ESENS beauty portrait",
      source: "T31141_05",
      style: "esens",
      photo: `${materials}T31141_05-clean-bg.png`,
      squarePhoto: `${materials}T31141_05-clean-bg-square.png`,
      headline: "ESENS",
      caption: "LOTION BEAUTY SKINCARE",
      note: "A single centered pink display word sits over a muted over-shoulder portrait; a small tracked skincare caption is centered beneath it.",
    },
    asbon32: {
      title: "ASBON tropical frame",
      source: "T31141_02",
      style: "asbon",
      photo: `${materials}T31141_02-photo-strip.png`,
      squarePhoto: `${materials}T31141_02-photo-square.png`,
      headline: "ASBON",
      note: "A high-contrast black display word sits above a wide tropical lagoon photograph, all inside a vivid pink inset with a dark outer frame.",
    },
    italicregular32: {
      title: "Family style comparison specimen",
      source: "T30392_12",
      style: "italicregular",
      paper: `${materials}T30392_12-clean-bg.png`,
      leftLabel: "Family Member Sample",
      rightLabel: "vs Current Style Sample",
      leftGlyph: "A",
      rightGlyph: "a",
      note: "Two oversized live letterforms compare an actual sibling font style with the current face on warm, lightly grained paper.",
    },
    smokeletters32: {
      title: "Smoky bracketed letter specimen",
      source: "T30392_16",
      style: "smokeletters",
      paper: `${materials}T30392_16-smoke-bg.png`,
      squarePaper: `${materials}T30392_16-smoke-bg-square.png`,
      topLeft: "LETTERFORM STUDY",
      topRight: "DISPLAY TYPE SPECIMEN",
      bottomLeft: "EXPRESSIVE CHARACTERS",
      bottomRight: "MONOCHROME TYPE STUDY",
      leftBrace: "{",
      leftGlyph: "f",
      rightGlyph: "h",
      rightBrace: "}",
      note: "Two oversized italic lowercase letters sit between tall curly braces over smoky monochrome paper, with tiny labels in the corners.",
    },
    blackerwear32: {
      title: "Blacker Wear fashion editorial",
      source: "T26301_02",
      style: "blackerwear",
      photo: `${materials}T26301_02-clean-bg.png`,
      squarePhoto: `${materials}T26301_02-clean-bg-square.png`,
      leftTitle: "Blacker",
      leftTagline: "Wear",
      rightTitle: "Trendy",
      rightItalic: "Fashion",
      bodyCopy: "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
      note: "A monochrome seated fashion portrait with two white display lines on the left and a two-line editorial headline plus body copy on a pale gray panel.",
    },
    silentnight32: {
      title: "Silent Night starfield specimen",
      source: "T0420_02",
      style: "silentnight",
      leftWord: "Silent",
      rightWord: "Night",
      note: "A single centered Silent Night line sits on black, framed by scattered white and soft gray four-point stars.",
    },
    playgrid32: {
      title: "Play Grid modular number specimen",
      source: "T29045_05",
      style: "playgrid",
      topLeft: "hora nocte",
      topRight: "neyro mono",
      label: "Pickle",
      year: "2037",
      gridTitle: "PLAY",
      topNumber: "82",
      leftNumber: "69",
      rightNumber: "45",
      bottomNumber: "82",
      note: "A dark year poster sits beside a compact 3-by-3 specimen grid, with a large live display title, four directional arrows, and a central geometric mark.",
    },
    fridayrunning32: {
      title: "Friday Running Club specimen",
      source: "T29045_06",
      style: "fridayrunning",
      topLeftLabel: "HORA NOCTE",
      topRightLabel: "NEYRO MONO",
      topTitle: "FRIDAY",
      headline: "RUNNING",
      leftNumber: "20",
      club: "CLUB",
      rightNumber: "25",
      footerLeft: "6 STYLES",
      footerRight: "© 2025",
      note: "A black athletic type poster with two small cyan corner labels, a white title flanked by geometric marks, a large cyan RUNNING line, and a white club/date lockup.",
    },
    medievalcreatures32: {
      title: "Medieval Creatures type specimen",
      source: "T33443_05",
      style: "medievalcreatures",
      topLine: "medieval creatures",
      yearLine: "{1348}",
      bottomLine: "manuscript and bestiaries",
      note: "A three-line medieval specimen in red on black: a small upper caption, oversized bracketed numerals, and a smaller lower caption.",
    },
    littlemadquote32: {
      title: "Little Mad quote specimen",
      source: "T33443_07",
      style: "littlemadquote",
      topLeft: "Hora Nocte",
      topRight: "HN Relvick",
      lineOne: "We All Go",
      lineTwo: "A Little Mad",
      lineThree: "Sometimes",
      attribution: "Psycho (1960)",
      footerLeft: "20 Styles",
      footerRight: "All Right Reserved © 2026",
      note: "A three-line crimson quote in an oversized italic serif, with the small Psycho attribution, white corner metadata, and a deep violet-to-black vignette.",
    },
    soulrevenge32: {
      title: "Soul's Revenge posters",
      source: "T33443_11",
      style: "soulrevenge",
      original: "originals/user-batch-2026-10-26-c/T33443_11.jpg",
      photoHouse: `${materials}T33443_11-photo-house.png`,
      photoTree: `${materials}T33443_11-photo-tree.png`,
      photoGarden: `${materials}T33443_11-photo-garden.png`,
      cinemaCredit: "23 CINEMAS PRESENT",
      titleOne: "Soul’s",
      titleTwo: "Revenge",
      director: "A Film By Daniel V. Harrington",
      castOne: "Victor\nWHITMORE",
      castTwo: "Eleanor\nGRAVES",
      castThree: "Isabella\nCROWE",
      castFour: "Lucas\nBLACKWOOD",
      dragonTitle: "THE DRAGON KNIGHT",
      yearOne: "1",
      yearTwo: "9",
      yearThree: "8",
      yearFour: "7",
      dragonTagline: "A LEGEND AWAKENS",
      note: "Two black film posters sit side by side on a violet field: an illustrated Soul’s Revenge cast poster and the red circled 1987 Dragon Knight title card.",
    },
    allworkplay32: {
      title: "All Work And No Play",
      source: "T18053_05",
      style: "allworkplay",
      photo: `${materials}T18053_05-clean-bg.png`,
      lineOne: "All work and no play",
      lineTwo: "makes Jack a dull boy,",
      lineThree: "All play and no work",
      lineFour: "makes Jack a mere toy.",
      note: "Four large italic lime lines carry the All work and no play quote over a dark frozen blue texture.",
    },
    owlstory32: {
      title: "The Owl Who Couldn’t Sleep",
      source: "T18880_08",
      style: "owlstory",
      photo: `${materials}T18880_08-clean-bg.png`,
      squarePhoto: `${materials}T18880_08-clean-bg-square.png`,
      titleLineOne: "The",
      titleLineTwo: "Owl",
      captionOne: "WHO",
      captionTwo: "COULDN’T",
      captionThree: "SLEEP",
      note: "A hand-engraved owl in indigo and black sits on warm textured paper beside the live title The Owl and its three-line subhead.",
    },
    hazysky32: {
      title: "Hazy Sky Session IPA",
      source: "T18880_11",
      style: "hazysky",
      photo: `${materials}T18880_11-clean-bg.png`,
      squarePhoto: `${materials}T18880_11-clean-bg-square.png`,
      headlineOne: "hazy",
      headlineTwo: "sky",
      caption: "SESSION IPA",
      note: "Large live black serif lettering with fine gold edging sits across a textured pink, cream, and seafoam wave background above the Session IPA caption.",
    },
    itsokay32: {
      title: "It’s Okay display poster",
      source: "T18880_15",
      style: "itsokay",
      photo: `${materials}T18880_15-clean-bg.png`,
      squarePhoto: `${materials}T18880_15-clean-bg-square.png`,
      headlineOne: "it's",
      headlineTwo: "Okay!",
      studioOne: "Fenotype",
      studioTwo: "Studios",
      footer: "POSTRE - TASTY DISPLAY TYPE",
      note: "Two oversized cream title rows sit across a stippled violet rose on black, with editable studio lettering at left and a tracked footer.",
    },
    nightonearth32: {
      title: "Night on Earth display specimen",
      source: "T18021_05",
      style: "nightonearth",
      headlineOne: "Night on",
      headlineTwo: "earth.",
      note: "Two oversized electric-indigo serif rows fill the near-black field, matching the source's left-aligned Night on earth. specimen.",
    },
    goodthingstothose32: {
      title: "Good Things quote and checkbox specimen",
      source: "T17804_02",
      style: "goodthingstothose",
      brandLetter: "F",
      lineOne: "Good things",
      lineTwo: "come to those",
      lineThree: "who",
      period: ".",
      optionOne: "Lurk",
      optionTwo: "Mull",
      optionThree: "Sniggle",
      optionFour: "Garble",
      optionFive: "Scuttle",
      checkedOption: 2,
      note: "Three bold cream quote rows, a small upper-right F, a drawn underline and period, and five editable checkbox labels on vivid electric blue-purple.",
    },
    rudybrownie32: {
      title: "Rudy Brownie sunset display specimen",
      source: "T17997_03",
      style: "rudybrownie",
      photo: `${materials}T17997_03-clean-sunset.png`,
      squarePhoto: `${materials}T17997_03-clean-sunset-square.png`,
      lineOne: "Rudy",
      lineTwo: "Brownie",
      note: "Two large cream display lines are rebuilt as editable HTML/CSS over text-free palm-tree sunset photography, with a separate square crop.",
    },
    sociato32: {
      title: "Sociato editorial specimen",
      source: "T16618_06",
      style: "sociato",
      photo: `${materials}T16618_06-clean-photo.png`,
      initial: "R",
      highlight: "Quirky.",
      bodyCopy: "Perfect for modern trends, it’s a typeface full of character. The typeface was inspired by a declaration published during the French Revolution that extolled the development of a new religion, the cult of the Supreme Being. It’s a stunning piece of work, with a wild, baroque layout and hand drawn typography. It’s a veritable goldmine of typographic ideas.",
      note: "A live white initial fills a vivid portrait panel beside an oversized editorial paragraph; the gold lead-in and copy remain editable text.",
    },
  };

  function makeStar(board) {
    const star = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    star.classList.add("urc-star");
    star.setAttribute("viewBox", "0 0 100 100");
    star.setAttribute("aria-hidden", "true");
    star.dataset.layoutItem = "welcomemorning32-star";
    const points = Array.from({ length: 16 }, (_, index) => {
      const angle = (Math.PI * 2 * index / 16) - Math.PI / 2;
      const radius = index % 2 === 0 ? 49 : 18;
      return `${50 + Math.cos(angle) * radius},${50 + Math.sin(angle) * radius}`;
    }).join(" ");
    const shape = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
    shape.setAttribute("points", points);
    star.append(shape);
    board.append(star);
  }

  function makePhotoStrip(board, config) {
    const square = board.dataset.ratio === "1x1";
    const box = square
      ? [.0407, .6579, .9187, .1818]
      : [.0556, .6170, .8888, .2760];
    const photo = document.createElement("img");
    photo.className = "urc-photo-strip";
    photo.alt = "";
    photo.src = `${root}${square ? config.squarePhoto : config.photo}`;
    photo.dataset.layoutItem = `${config.style}-storefront-photo`;
    Object.assign(photo.style, {
      left: `${box[0] * 100}%`,
      top: `${box[1] * 100}%`,
      width: `${box[2] * 100}%`,
      height: `${box[3] * 100}%`,
    });
    board.append(photo);
  }

  function makePortrait(board, config) {
    const square = board.dataset.ratio === "1x1";
    const photo = document.createElement("img");
    photo.className = "urc-portrait";
    photo.alt = "";
    photo.src = `${root}${square ? config.squarePhoto : config.photo}`;
    photo.dataset.layoutItem = `${config.style}-portrait-photo`;
    board.append(photo);
  }

  function makeAsbonCard(board) {
    const square = board.dataset.ratio === "1x1";
    const box = square ? [.08, .06, .84, .88] : [.0972, .103, .8056, .793];
    const card = document.createElement("div");
    card.className = "urc-asbon-card";
    card.dataset.layoutItem = "asbon32-pink-card";
    Object.assign(card.style, {
      left: `${box[0] * 100}%`,
      top: `${box[1] * 100}%`,
      width: `${box[2] * 100}%`,
      height: `${box[3] * 100}%`,
    });
    board.append(card);
  }

  function makeAsbonPhoto(board, config) {
    const square = board.dataset.ratio === "1x1";
    const box = square ? [.13, .45, .74, .424] : [.1422, .45, .7156, .342];
    const photo = document.createElement("img");
    photo.className = "urc-asbon-photo";
    photo.alt = "";
    photo.src = `${root}${square ? config.squarePhoto : config.photo}`;
    photo.dataset.layoutItem = "asbon32-lagoon-photo";
    Object.assign(photo.style, {
      left: `${box[0] * 100}%`,
      top: `${box[1] * 100}%`,
      width: `${box[2] * 100}%`,
      height: `${box[3] * 100}%`,
    });
    board.append(photo);
  }

  function makePaper(board, config) {
    const paper = document.createElement("img");
    paper.className = "urc-paper";
    paper.alt = "";
    paper.src = `${root}${config.paper}`;
    paper.dataset.layoutItem = `${config.style}-paper-texture`;
    board.append(paper);
  }

  function makeSmokePaper(board, config) {
    const square = board.dataset.ratio === "1x1";
    const paper = document.createElement("img");
    paper.className = "urc-smoke-paper";
    paper.alt = "";
    paper.src = `${root}${square ? config.squarePaper : config.paper}`;
    paper.dataset.layoutItem = "smokeletters32-smoky-background";
    board.append(paper);
  }

  function makeBlackerWearPlate(board, config) {
    const square = board.dataset.ratio === "1x1";
    const photo = document.createElement("img");
    photo.className = "urc-fashion-plate";
    photo.alt = "";
    photo.src = `${root}${square ? config.squarePhoto : config.photo}`;
    photo.dataset.layoutItem = "blackerwear32-fashion-background";
    board.append(photo);
  }

  function makeSilentNightStars(board) {
    const stars = [
      [.024, .046, .036, "#f2f1ef"], [.055, .103, .036, "#f2f1ef"],
      [.155, .178, .022, "#f2f1ef"], [.104, .261, .022, "#f2f1ef"],
      [.497, .136, .036, "#f2f1ef"], [.306, .265, .036, "#f2f1ef"],
      [.548, .300, .022, "#f2f1ef"], [.458, .555, .018, "#999999"],
      [.868, .187, .017, "#d8d8d8"], [.946, .187, .040, "#f2f1ef"],
      [.700, .405, .035, "#888888"], [.885, .703, .037, "#999999"],
      [.176, .841, .037, "#a8a8a8"], [.235, .833, .019, "#e4e4e4"],
      [.653, .838, .039, "#b5b5b5"], [.713, .819, .020, "#dedede"],
    ];
    const pathData = "M50 0 C56 38 62 44 100 50 C62 56 56 62 50 100 C44 62 38 56 0 50 C38 44 44 38 50 0Z";
    stars.forEach(([x, y, size, color], index) => {
      const star = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      star.classList.add("urc-night-star");
      star.setAttribute("viewBox", "0 0 100 100");
      star.setAttribute("aria-hidden", "true");
      star.dataset.layoutItem = `silentnight32-star-${index + 1}`;
      Object.assign(star.style, {
        left: `${x * 100}%`,
        top: `${y * 100}%`,
        width: `${size * 100}%`,
        height: `${size * 100}%`,
        color,
      });
      const shape = document.createElementNS("http://www.w3.org/2000/svg", "path");
      shape.setAttribute("d", pathData);
      star.append(shape);
      board.append(star);
    });
  }

  function makePlayGridArrow(cell, direction) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("aria-hidden", "true");
    svg.classList.add("pg-arrow");
    svg.dataset.layoutItem = `playgrid32-arrow-${direction}`;
    const arrow = document.createElementNS("http://www.w3.org/2000/svg", "path");
    arrow.setAttribute("d", "M22 22 L76 76 M25 50 L22 22 L50 25");
    arrow.setAttribute("fill", "none");
    arrow.setAttribute("stroke", "currentColor");
    arrow.setAttribute("stroke-width", "11");
    arrow.setAttribute("stroke-linecap", "square");
    arrow.setAttribute("stroke-linejoin", "miter");
    svg.append(arrow);
    const rotation = { nw: 0, ne: 90, se: 180, sw: 270 }[direction];
    svg.style.transform = `rotate(${rotation}deg)`;
    cell.append(svg);
  }

  function makePlayGridMark(cell) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("aria-hidden", "true");
    svg.classList.add("pg-mark");
    svg.dataset.layoutItem = "playgrid32-center-mark";
    const mark = document.createElementNS("http://www.w3.org/2000/svg", "path");
    mark.setAttribute("d", "M18 5 H38 L50 29 L62 5 H82 L70 39 L95 29 V47 L68 50 L95 53 V71 L70 61 L82 95 H62 L50 71 L38 95 H18 L30 61 L5 71 V53 L32 50 L5 47 V29 L30 39 Z");
    mark.setAttribute("fill", "currentColor");
    svg.append(mark);
    cell.append(svg);
  }

  function makePlayGridPanels(board) {
    const square = board.dataset.ratio === "1x1";
    const panels = [
      { className: "pg-poster", item: "playgrid32-poster", left: .081, top: square ? .245 : .125, width: .379, height: square ? .510 : .750 },
      { className: "pg-grid-panel", item: "playgrid32-grid-panel", left: .510, top: square ? .245 : .125, width: .379, height: square ? .510 : .750 },
    ];
    const [poster, specimen] = panels.map((spec) => {
      const panel = document.createElement("section");
      panel.className = spec.className;
      panel.dataset.layoutItem = spec.item;
      Object.assign(panel.style, {
        left: `${spec.left * 100}%`, top: `${spec.top * 100}%`,
        width: `${spec.width * 100}%`, height: `${spec.height * 100}%`,
      });
      board.append(panel);
      return panel;
    });
    return { poster, specimen, square };
  }

  function makePlayGridText(parent, key, value, box, options = {}) {
    const element = document.createElement("div");
    element.className = `pg-type ${options.className || ""}`.trim();
    element.dataset.layoutItem = `${options.templateId || "playgrid32"}-${key}`;
    element.dataset.displayItem = options.display === false ? "false" : "true";
    const glyphs = document.createElement("span");
    glyphs.className = "pg-glyphs";
    glyphs.textContent = String(value ?? "");
    element.append(glyphs);
    Object.assign(element.style, {
      left: `${box[0] * 100}%`, top: `${box[1] * 100}%`,
      width: `${box[2] * 100}%`, height: `${box[3] * 100}%`,
      color: options.color || "#f3f3f0",
      fontFamily: options.fontFamily || (options.mono
        ? "'Courier New', Courier, monospace"
        : "SupportDisplay, 'Noto Sans', Arial, sans-serif"),
      fontWeight: "400",
      fontStyle: options.italic ? "italic" : "normal",
      letterSpacing: `${options.tracking ?? -.025}em`,
      fontSize: `${options.baseSize || 100}px`,
      textAlign: options.align || "left",
      justifyContent: options.justify || "flex-start",
    });
    if (options.display === false) element.removeAttribute("data-display-item");
    parent.append(element);
    const width = parent.clientWidth * box[2] * (options.widthFactor || .96);
    const height = parent.clientHeight * box[3] * (options.heightFactor || .82);
    const size = window.SupportLayout.fitLine(element, {
      width, height,
      maxSize: Math.max(16, parent.clientHeight * (options.maxSize || .18) * Number(options.scale ?? 1)),
      minSize: Math.max(1, Math.min(12, parent.clientHeight * .02)),
      tracking: options.tracking ?? -.025,
    });
    if (!options.mono && options.tighten !== false) {
      const range = document.createRange();
      range.selectNodeContents(glyphs);
      const naturalWidth = range.getBoundingClientRect().width;
      const targetWidth = parent.clientWidth * box[2] * (options.targetWidth || .82);
      glyphs.style.transform = `scaleX(${naturalWidth > 0
        ? Math.max(.65, Math.min(1.9, targetWidth / naturalWidth)) : 1})`;
    }
    return { element, size };
  }

  function addPlayGridComposition(board, config, state) {
    const { poster, specimen, square } = makePlayGridPanels(board);
    const scale = Number(state.displayScale ?? 1);
    makePlayGridText(poster, "topLeft", state.topLeft ?? config.topLeft, [.050, .022, .43, .055], {
      mono: true, display: false, color: "#87d9e8", tracking: .015, maxSize: .029, widthFactor: .98, heightFactor: .88,
    });
    makePlayGridText(poster, "topRight", state.topRight ?? config.topRight, [.50, .022, .45, .055], {
      mono: true, display: false, align: "right", justify: "flex-end", color: "#87d9e8", tracking: .015, maxSize: .029, widthFactor: .99, heightFactor: .88,
    });
    makePlayGridText(poster, "label", state.label ?? config.label, [.090, .607, .83, .105], {
      className: "pg-poster-label", maxSize: .132, targetWidth: .60, scale, tracking: -.045,
    });
    makePlayGridText(poster, "year", state.year ?? config.year, [.090, .720, .87, .270], {
      className: "pg-poster-year", maxSize: .285, targetWidth: .98, scale, tracking: -.045,
    });

    const headerBox = [.07, .023, .70, .190];
    makePlayGridText(specimen, "gridTitle", state.gridTitle ?? config.gridTitle, headerBox, {
      maxSize: .195, targetWidth: .90, scale, tracking: -.035, align: "center", justify: "center",
    });
    const playIcon = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    playIcon.setAttribute("viewBox", "0 0 100 100");
    playIcon.setAttribute("aria-hidden", "true");
    playIcon.classList.add("pg-play-icon");
    playIcon.dataset.layoutItem = "playgrid32-play-icon";
    const playShape = document.createElementNS("http://www.w3.org/2000/svg", "path");
    playShape.setAttribute("d", "M50 0 L66 29 L100 50 L66 71 L50 100 L34 71 L0 50 L34 29 Z M50 30 L59 42 L77 50 L59 58 L50 70 L41 58 L23 50 L41 42 Z");
    playShape.setAttribute("fill", "currentColor");
    playShape.setAttribute("fill-rule", "evenodd");
    playIcon.append(playShape);
    Object.assign(playIcon.style, {
      left: "82%", top: "7%", width: "9%", height: "11%",
      color: "#f3f3f0",
    });
    specimen.append(playIcon);
    const grid = document.createElement("div");
    grid.className = "pg-number-grid";
    grid.dataset.layoutItem = "playgrid32-number-grid";
    Object.assign(grid.style, {
      left: "0", top: "24.3%", width: "100%", height: "75.7%",
    });
    specimen.append(grid);
    const cells = [
      { key: "arrow-nw", color: "purple", arrow: "nw" },
      { key: "topNumber", color: "paper", value: state.topNumber ?? config.topNumber },
      { key: "arrow-ne", color: "purple", arrow: "ne" },
      { key: "leftNumber", color: "paper", value: state.leftNumber ?? config.leftNumber },
      { key: "center-mark", color: "purple", mark: true },
      { key: "rightNumber", color: "paper", value: state.rightNumber ?? config.rightNumber },
      { key: "arrow-sw", color: "purple", arrow: "sw" },
      { key: "bottomNumber", color: "paper", value: state.bottomNumber ?? config.bottomNumber },
      { key: "arrow-se", color: "purple", arrow: "se" },
    ];
    cells.forEach((cell, index) => {
      const node = document.createElement("div");
      node.className = `pg-cell pg-${cell.color}`;
      node.dataset.layoutItem = `playgrid32-cell-${cell.key}`;
      node.dataset.gridCell = cell.key;
      Object.assign(node.style, {
        left: `${(index % 3) * 33.333333}%`,
        top: `${Math.floor(index / 3) * 33.333333}%`,
        width: "33.333333%", height: "33.333333%",
      });
      grid.append(node);
      if (cell.arrow) {
        makePlayGridArrow(node, cell.arrow);
      } else if (cell.mark) {
        makePlayGridMark(node);
      } else {
        makePlayGridText(node, cell.key, cell.value, [.07, .06, .86, .88], {
            maxSize: .88, targetWidth: .90, tracking: -.06, align: "center", justify: "center",
            color: "#08090b", scale, widthFactor: .92, heightFactor: .82,
          });
      }
    });
    board.style.setProperty("--pg-scale", String(scale));
    board.dataset.ratio = square ? "1x1" : "3x2";
  }

  function makeFridayRunningMark(board, side) {
    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", "0 0 100 100");
    svg.setAttribute("aria-hidden", "true");
    svg.classList.add("fr-running-mark");
    svg.dataset.layoutItem = `fridayrunning32-mark-${side}`;
    const shape = document.createElementNS("http://www.w3.org/2000/svg", "path");
    shape.setAttribute("d", "M24 5 H43 L50 27 L57 5 H76 L66 39 L95 31 V50 L66 58 L76 95 H57 L50 73 L43 95 H24 L34 58 L5 50 V31 L34 39 Z");
    shape.setAttribute("fill", "currentColor");
    svg.append(shape);
    Object.assign(svg.style, {
      left: side === "left" ? "21.8%" : "73.8%",
      top: "22.4%", width: "5.8%", height: "8.6%",
      color: "#f2f2f0",
    });
    board.append(svg);
  }

  function addFridayRunningComposition(board, config, state) {
    const scale = Number(state.displayScale ?? 1);
    const text = (key, box, options) => makePlayGridText(
      board, key, state[key] ?? config[key], box,
      { ...options, scale, templateId: "fridayrunning32" },
    );
    text("topLeftLabel", [.040, .038, .30, .050], {
      mono: true, display: false, color: "#79d3e8", tracking: .045,
      maxSize: .030, widthFactor: .98, heightFactor: .86,
    });
    text("topRightLabel", [.660, .038, .30, .050], {
      mono: true, display: false, align: "right", justify: "flex-end",
      color: "#79d3e8", tracking: .045, maxSize: .030,
      widthFactor: .98, heightFactor: .86,
    });
    text("topTitle", [.285, .178, .43, .157], {
      maxSize: .164, targetWidth: .92, tracking: -.025, align: "center", justify: "center",
    });
    makeFridayRunningMark(board, "left");
    makeFridayRunningMark(board, "right");
    text("headline", [.075, .378, .85, .254], {
      maxSize: .267, targetWidth: .97, tracking: -.035, align: "center", justify: "center",
      color: "#5fc5ed",
    });
    text("leftNumber", [.270, .652, .090, .145], {
      maxSize: .132, targetWidth: .85, tracking: -.035, align: "center", justify: "center",
    });
    text("club", [.378, .645, .255, .163], {
      maxSize: .174, targetWidth: .96, tracking: -.035, align: "center", justify: "center",
    });
    text("rightNumber", [.670, .652, .090, .145], {
      maxSize: .132, targetWidth: .85, tracking: -.035, align: "center", justify: "center",
    });
    text("footerLeft", [.040, .920, .28, .054], {
      mono: true, display: false, color: "#79d3e8", tracking: .055,
      maxSize: .036, widthFactor: .98, heightFactor: .88,
    });
    text("footerRight", [.685, .920, .275, .054], {
      mono: true, display: false, align: "right", justify: "flex-end",
      color: "#79d3e8", tracking: .055, maxSize: .036,
      widthFactor: .98, heightFactor: .88,
    });
  }

  function addMedievalCreaturesComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const text = (key, box, options) => makePlayGridText(
      board, key, state[key] ?? config[key], box,
      { ...options, className: "mc-type", templateId: "medievalcreatures32", scale },
    );
    text("topLine", square ? [.10, .178, .80, .104] : [.215, .158, .57, .102], {
      maxSize: .112, targetWidth: .96, widthFactor: .98, heightFactor: .86,
      tracking: -.018, align: "center", justify: "center", color: "#d3000c",
    });
    text("yearLine", square ? [.035, .315, .93, .375] : [.035, .282, .93, .438], {
      maxSize: .60, targetWidth: .94, widthFactor: .98, heightFactor: .90,
      tracking: -.045, align: "center", justify: "center", color: "#d3000c",
    });
    text("bottomLine", square ? [.09, .738, .82, .108] : [.12, .748, .76, .105], {
      maxSize: .112, targetWidth: .96, widthFactor: .98, heightFactor: .86,
      tracking: -.018, align: "center", justify: "center", color: "#d3000c",
    });
  }

  function addLittleMadQuoteComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const text = (key, box, options) => makePlayGridText(
      board, key, state[key] ?? config[key], box,
      { ...options, className: "lmq-type", templateId: "littlemadquote32", scale },
    );
    const small = { maxSize: .023, targetWidth: .96, widthFactor: .98,
      heightFactor: .88, tracking: .015, color: "#e6e2ea",
      fontFamily: "Georgia, 'Times New Roman', serif", display: false,
      tighten: false };
    text("topLeft", square ? [.045, .045, .31, .045] : [.036, .043, .22, .045], {
      ...small, align: "left", justify: "flex-start",
    });
    text("topRight", square ? [.64, .045, .315, .045] : [.79, .043, .174, .045], {
      ...small, align: "right", justify: "flex-end",
    });
    const rows = square
      ? [
          ["lineOne", [.075, .185, .85, .175]],
          ["lineTwo", [.045, .375, .91, .175]],
          ["lineThree", [.075, .565, .85, .175]],
        ]
      : [
          ["lineOne", [.18, .135, .64, .215]],
          ["lineTwo", [.08, .363, .84, .215]],
          ["lineThree", [.11, .591, .78, .215]],
        ];
    rows.forEach(([key, box]) => text(key, box, {
      maxSize: .255, targetWidth: .96, widthFactor: .98, heightFactor: .89,
      tracking: -.035, align: "center", justify: "center", italic: true,
      color: "#d3000c",
    }));
    text("attribution", square ? [.29, .755, .42, .078] : [.34, .833, .32, .075], {
      maxSize: .070, targetWidth: .96, widthFactor: .98, heightFactor: .88,
      tracking: -.025, align: "center", justify: "center", italic: true,
      color: "#d3000c",
    });
    text("footerLeft", square ? [.045, .928, .26, .042] : [.036, .938, .22, .042], {
      ...small, align: "left", justify: "flex-start",
    });
    text("footerRight", square ? [.56, .928, .395, .042] : [.72, .938, .244, .042], {
      ...small, align: "right", justify: "flex-end",
    });
  }

  function addSoulRevengeComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const posters = square
      ? [
          { side: "film", left: .005, top: .155, width: .485, height: .642 },
          { side: "dragon", left: .510, top: .232, width: .485, height: .642 },
        ]
      : [
          { side: "film", left: .064, top: .039, width: .415, height: .823 },
          { side: "dragon", left: .519, top: .135, width: .414, height: .822 },
        ];
    const [film, dragon] = posters.map((spec) => {
      const panel = document.createElement("section");
      panel.className = `sr-poster sr-poster-${spec.side}`;
      panel.dataset.layoutItem = `soulrevenge32-${spec.side}-poster`;
      Object.assign(panel.style, {
        left: `${spec.left * 100}%`, top: `${spec.top * 100}%`,
        width: `${spec.width * 100}%`, height: `${spec.height * 100}%`,
      });
      board.append(panel);
      return panel;
    });
    const addPhoto = (poster, key, path, top) => {
      const photo = document.createElement("img");
      photo.className = "sr-photo";
      photo.alt = "";
      photo.src = `${root}${path}`;
      photo.dataset.layoutItem = `soulrevenge32-${key}`;
      Object.assign(photo.style, {
        left: "3.35%", top: `${top * 100}%`, width: "93.85%", height: "14.78%",
      });
      poster.append(photo);
    };
    addPhoto(film, "house-photo", config.photoHouse, .088);
    addPhoto(film, "tree-photo", config.photoTree, .257);
    addPhoto(film, "garden-photo", config.photoGarden, .427);

    const text = (parent, key, value, box, options = {}) => makePlayGridText(
      parent, key, state[key] ?? value, box,
      { ...options, className: "sr-type", templateId: "soulrevenge32", scale },
    );
    text(film, "cinemaCredit", config.cinemaCredit,
      [.08, .022, .84, .056], {
        maxSize: .031, targetWidth: .90, widthFactor: .98, heightFactor: .88,
        tracking: .01, align: "center", justify: "center", color: "#d3000c",
        fontFamily: "Georgia, 'Times New Roman', serif", display: false, tighten: false,
      });
    text(film, "titleOne", config.titleOne, [.055, .596, .89, .114], {
      maxSize: .145, targetWidth: .92, widthFactor: .96, heightFactor: .88,
      tracking: -.04, align: "center", justify: "center", color: "#d3000c",
    });
    text(film, "titleTwo", config.titleTwo, [.035, .713, .93, .127], {
      maxSize: .17, targetWidth: .96, widthFactor: .97, heightFactor: .88,
      tracking: -.045, align: "center", justify: "center", color: "#d3000c",
    });
    text(film, "director", config.director, [.10, .841, .80, .045], {
      maxSize: .032, targetWidth: .95, widthFactor: .98, heightFactor: .84,
      tracking: -.005, align: "center", justify: "center", color: "#f3f1ed",
      fontFamily: "Georgia, 'Times New Roman', serif", display: false, tighten: false,
    });
    ["castOne", "castTwo", "castThree", "castFour"].forEach((key, index) => {
      const col = [.025, .267, .508, .750][index];
      const width = .225;
      const [given, surname] = String(state[key] ?? config[key]).split(/\r?\n/u, 2);
      text(film, `${key}Given`, given, [col, .902, width, .031], {
        maxSize: .020, targetWidth: .95, widthFactor: .95, heightFactor: .90,
        tracking: 0, align: "center", justify: "center", color: "#f3f1ed",
        fontFamily: "Georgia, 'Times New Roman', serif", display: false, tighten: false,
      });
      text(film, `${key}Surname`, surname, [col, .932, width, .040], {
        maxSize: .036, targetWidth: .96, widthFactor: .94, heightFactor: .90,
        tracking: -.04, align: "center", justify: "center", color: "#d3000c",
      });
    });
    text(dragon, "dragonTitle", config.dragonTitle, [.055, .043, .89, .083], {
      maxSize: .074, targetWidth: .96, widthFactor: .96, heightFactor: .88,
      tracking: -.035, align: "center", justify: "center", color: "#f4f2ef",
    });
    const circleSize = { width: .50, height: .3775 };
    const circles = [
      ["yearOne", config.yearOne, .300, .34875],
      ["yearTwo", config.yearTwo, .700, .34875],
      ["yearThree", config.yearThree, .300, .65175],
      ["yearFour", config.yearFour, .700, .65175],
    ];
    circles.forEach(([key, value, centerX, centerY]) => {
      const left = centerX - circleSize.width / 2;
      const top = centerY - circleSize.height / 2;
      const ring = document.createElement("div");
      ring.className = "sr-circle";
      ring.dataset.layoutItem = `soulrevenge32-${key}-ring`;
      Object.assign(ring.style, {
        left: `${left * 100}%`, top: `${top * 100}%`,
        width: `${circleSize.width * 100}%`, height: `${circleSize.height * 100}%`,
        borderWidth: `${Math.max(2, dragon.clientWidth * .012)}px`,
      });
      dragon.append(ring);
      text(dragon, key, value,
        [left, top, circleSize.width, circleSize.height], {
          className: "sr-year",
          maxSize: .275, targetWidth: .78, widthFactor: .94, heightFactor: .87,
          tracking: -.04, align: "center", justify: "center", color: "#d3000c",
        });
    });
    text(dragon, "dragonTagline", config.dragonTagline,
      [.045, .903, .91, .075], {
        maxSize: .078, targetWidth: .96, widthFactor: .96, heightFactor: .88,
        tracking: -.035, align: "center", justify: "center", color: "#f4f2ef",
      });
  }

  function addAllWorkPlayComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const photo = document.createElement("img");
    photo.className = "awp-bg";
    photo.alt = "";
    photo.src = `${root}${config.photo}`;
    photo.dataset.layoutItem = "allworkplay32-ice-background";
    board.append(photo);
    const vignette = document.createElement("div");
    vignette.className = "awp-vignette";
    vignette.dataset.layoutItem = "allworkplay32-blue-vignette";
    board.append(vignette);
    const boxes = square
      ? [
          ["lineOne", [.006, .18, .988, .15], .88],
          ["lineTwo", [.006, .34, .988, .15], .97],
          ["lineThree", [.006, .55, .988, .15], .88],
          ["lineFour", [.006, .69, .988, .15], .99],
        ]
      : [
          ["lineOne", [0, .18, 1, .15], .88],
          ["lineTwo", [0, .34, 1, .15], .97],
          ["lineThree", [0, .55, 1, .15], .88],
          ["lineFour", [0, .69, 1, .15], .99],
        ];
    boxes.forEach(([key, box, targetWidth]) => makePlayGridText(
      board, key, state[key] ?? config[key], box, {
        className: "awp-type", templateId: "allworkplay32", scale,
        maxSize: .15, targetWidth,
        widthFactor: .995, heightFactor: .92,
        tracking: -.035, align: "left", justify: "flex-start",
        italic: true, color: "#cfff5c",
      },
    ));
  }

  function addSociatoComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const split = square ? .44 : .49;
    const photo = document.createElement("img");
    photo.className = "sociato-photo";
    photo.alt = "";
    photo.src = `${root}${config.photo}`;
    photo.dataset.layoutItem = "sociato32-portrait-photo";
    Object.assign(photo.style, { width: `${split * 100}%` });
    board.append(photo);

    makePlayGridText(board, "initial", state.initial ?? config.initial,
      square ? [.045, .14, .35, .72] : [.045, .14, .39, .72], {
        className: "sociato-initial", templateId: "sociato32",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
        scale: Number(state.displayScale ?? 1),
        maxSize: .80, widthFactor: .95, heightFactor: .90,
        tracking: -.012, align: "left", justify: "flex-start", tighten: false,
        color: "#ffffff",
      });

    const copyWindow = document.createElement("div");
    copyWindow.className = "sociato-copy-window";
    copyWindow.dataset.layoutItem = "sociato32-copy-window";
    const copyLeft = split + (square ? .03 : .035);
    const copyRightMargin = square ? .035 : .03;
    Object.assign(copyWindow.style, {
      left: `${copyLeft * 100}%`,
      top: "5.5%",
      width: `${(1 - copyLeft - copyRightMargin) * 100}%`,
      height: "90%",
      padding: "1.4% 2.7%",
    });
    const copyContent = document.createElement("div");
    copyContent.className = "sociato-copy-content";
    copyContent.style.width = "100%";
    const highlight = document.createElement("span");
    highlight.className = "sociato-highlight";
    highlight.textContent = String(state.highlight ?? config.highlight);
    copyContent.append(highlight, document.createTextNode(` ${String(state.bodyCopy ?? config.bodyCopy)}`));
    copyWindow.append(copyContent);
    board.append(copyWindow);

    const minFontSize = 10;
    let low = minFontSize;
    let high = board.clientHeight * .072;
    const verticalPadding = copyWindow.clientWidth * .028;
    const fitHeight = copyWindow.clientHeight - verticalPadding * 2;
    for (let iteration = 0; iteration < 18; iteration += 1) {
      const fontSize = (low + high) / 2;
      copyWindow.style.fontSize = `${fontSize}px`;
      copyWindow.style.lineHeight = "1.18";
      if (copyContent.scrollHeight <= fitHeight &&
          copyContent.scrollWidth <= copyContent.clientWidth + 1) {
        low = fontSize;
      } else {
        high = fontSize;
      }
    }
    copyWindow.style.fontSize = `${low}px`;
  }

  function addOwlStoryComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const photo = document.createElement("img");
    photo.className = "owlstory-bg";
    photo.alt = "";
    photo.src = `${root}${square ? config.squarePhoto : config.photo}`;
    photo.dataset.layoutItem = "owlstory32-engraved-owl-background";
    board.append(photo);

    const titleBoxes = square
      ? [
          ["titleLineOne", [.045, .075, .34, .17], .21],
          ["titleLineTwo", [.045, .245, .36, .23], .26],
        ]
      : [
          ["titleLineOne", [.064, .072, .40, .285], .30],
          ["titleLineTwo", [.064, .351, .44, .31], .31],
        ];
    titleBoxes.forEach(([key, box, maxSize]) => makePlayGridText(
      board, key, state[key] ?? config[key], box, {
        className: "owlstory-type owlstory-title",
        templateId: "owlstory32",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
        scale,
        maxSize,
        targetWidth: .95,
        widthFactor: .96,
        heightFactor: .90,
        tracking: -.055,
        align: "left",
        justify: "flex-start",
        color: "#373750",
      },
    ));

    const captionBoxes = square
      ? [
          ["captionOne", [.060, .535, .30, .10]],
          ["captionTwo", [.060, .640, .34, .10]],
          ["captionThree", [.060, .745, .30, .10]],
        ]
      : [
          ["captionOne", [.081, .680, .36, .10]],
          ["captionTwo", [.081, .780, .38, .10]],
          ["captionThree", [.081, .880, .35, .10]],
        ];
    captionBoxes.forEach(([key, box]) => makePlayGridText(
      board, key, state[key] ?? config[key], box, {
        className: "owlstory-type owlstory-caption",
        templateId: "owlstory32",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
        scale,
        maxSize: .085,
        targetWidth: .94,
        widthFactor: .96,
        heightFactor: .90,
        tracking: -.025,
        align: "left",
        justify: "flex-start",
        color: "#373750",
      },
    ));
  }

  function addHazySkyComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const background = document.createElement("img");
    background.className = "hazysky-background";
    background.alt = "";
    background.src = `${root}${square ? config.squarePhoto : config.photo}`;
    background.dataset.layoutItem = "hazysky32-painted-wave-background";
    board.append(background);

    const rows = square
      ? [
          ["headlineOne", [.045, .075, .91, .29], .37],
          ["headlineTwo", [.075, .355, .85, .30], .39],
          ["caption", [.20, .735, .60, .11], .105],
        ]
      : [
          ["headlineOne", [.105, .055, .79, .37], .42],
          ["headlineTwo", [.17, .405, .66, .39], .43],
          ["caption", [.245, .825, .51, .10], .105],
        ];
    rows.forEach(([key, box, maxSize]) => makePlayGridText(
      board, key, state[key] ?? config[key], box, {
        className: `hazysky-type ${key === "caption" ? "hazysky-caption" : "hazysky-headline"}`,
        templateId: "hazysky32",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
        scale,
        maxSize,
        targetWidth: key === "headlineTwo" ? .87 : .92,
        widthFactor: .95,
        heightFactor: .88,
        tracking: key === "caption" ? .02 : -.04,
        align: "center",
        justify: "center",
        color: "#070708",
      },
    ));
  }

  function addItsOkayComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const background = document.createElement("img");
    background.className = "itsokay-background";
    background.alt = "";
    background.src = `${root}${square ? config.squarePhoto : config.photo}`;
    background.dataset.layoutItem = "itsokay32-text-free-violet-rose-background";
    board.append(background);

    const rows = square
      ? [
          ["studioOne", [.055, .055, .26, .075], .085, "brand"],
          ["studioTwo", [.055, .125, .23, .075], .085, "brand"],
          ["headlineOne", [.24, .105, .55, .245], .31, "headline"],
          ["headlineTwo", [.045, .365, .91, .345], .43, "headline"],
          ["footer", [.075, .875, .85, .075], .075, "footer"],
        ]
      : [
          ["headlineOne", [.29, .075, .44, .30], .33, "headline"],
          ["headlineTwo", [.075, .365, .85, .39], .44, "headline"],
          ["studioOne", [.105, .245, .20, .075], .086, "brand"],
          ["studioTwo", [.115, .325, .19, .075], .086, "brand"],
          ["footer", [.205, .895, .59, .065], .073, "footer"],
        ];

    rows.forEach(([key, box, maxSize, kind]) => makePlayGridText(
      board, key, state[key] ?? config[key], box, {
        className: `itsokay-type itsokay-${kind}`,
        templateId: "itsokay32",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
        scale,
        maxSize,
        targetWidth: key === "headlineOne"
          ? (square ? .52 : .40)
          : key === "headlineTwo"
            ? (square ? .90 : .78)
            : key === "footer"
              ? (square ? .78 : .62)
              : (square ? .21 : .17),
        widthFactor: .95,
        heightFactor: .88,
        tracking: kind === "footer" ? .13 : kind === "headline" ? -.055 : -.015,
        align: "center",
        justify: "center",
        color: kind === "brand" ? "#c59bdf" : "#fff9e8",
      },
    ));
  }

  function addNightOnEarthComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const rows = square
      ? [
          ["headlineOne", [.035, .125, .93, .30], .37, .94],
          ["headlineTwo", [.035, .475, .84, .33], .39, .84],
        ]
      : [
          ["headlineOne", [.025, .125, .975, .37], .42, .974],
          ["headlineTwo", [.025, .50, .95, .43], .47, .71],
        ];
    rows.forEach(([key, box, maxSize, targetWidth]) => {
      makePlayGridText(
        board, key, state[key] ?? config[key], box, {
          className: "nightonearth-type nightonearth-display",
          templateId: "nightonearth32",
          fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
          scale,
          maxSize,
          targetWidth,
          widthFactor: .96,
          heightFactor: .90,
          tracking: -.045,
          align: "left",
          justify: "flex-start",
          color: "#4b00ff",
        },
      );
    });
  }

  function addGoodThingsCheckbox(board, key, label, box, labelBox, selected) {
    const checkbox = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    checkbox.setAttribute("viewBox", "0 0 100 100");
    checkbox.setAttribute("aria-hidden", "true");
    checkbox.classList.add("goodthings-checkbox");
    checkbox.dataset.layoutItem = `goodthingstothose32-checkbox-${key}`;
    Object.assign(checkbox.style, {
      left: `${box[0] * 100}%`, top: `${box[1] * 100}%`,
      width: `${box[2] * 100}%`, height: `${box[3] * 100}%`,
    });
    const outline = document.createElementNS("http://www.w3.org/2000/svg", "rect");
    outline.setAttribute("x", "7");
    outline.setAttribute("y", "7");
    outline.setAttribute("width", "86");
    outline.setAttribute("height", "86");
    outline.setAttribute("rx", "6");
    outline.setAttribute("fill", "none");
    outline.setAttribute("stroke", "#fffbf3");
    outline.setAttribute("stroke-width", "8");
    checkbox.append(outline);
    if (selected) {
      const tick = document.createElementNS("http://www.w3.org/2000/svg", "path");
      tick.setAttribute("d", "M20 52 L47 78 L112 14");
      tick.setAttribute("fill", "none");
      tick.setAttribute("stroke", "#f2a078");
      tick.setAttribute("stroke-width", "11");
      tick.setAttribute("stroke-linecap", "round");
      tick.setAttribute("stroke-linejoin", "round");
      checkbox.append(tick);
    }
    board.append(checkbox);

    const labelText = makePlayGridText(board, key, label, labelBox, {
      className: "goodthings-choice-label",
      templateId: "goodthingstothose32",
      scale: 1,
      maxSize: .064,
      targetWidth: labelBox[4],
      widthFactor: .97,
      heightFactor: .88,
      tracking: -.035,
      align: "left",
      justify: "flex-start",
      color: "#fffbf3",
    });
    const glyphs = labelText.element.querySelector(".pg-glyphs");
    const scaleY = Number(labelBox[5] ?? 1);
    if (scaleY !== 1) {
      glyphs.style.transformOrigin = "left top";
      glyphs.style.transform += ` scaleY(${scaleY})`;
    }
  }

  function addGoodThingsComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const text = (key, value, box, maxSize, targetWidth, className = "goodthings-title") =>
      makePlayGridText(board, key, state[key] ?? value, box, {
        className,
        templateId: "goodthingstothose32",
        scale,
        maxSize,
        targetWidth,
        widthFactor: .97,
        heightFactor: .88,
        tracking: -.045,
        align: "left",
        justify: "flex-start",
        color: "#fffbf3",
      });

    const rows = square
      ? {
          brand: [.902, .076, .05, .07],
          lineOne: [.048, .1893, .88, .195],
          lineTwo: [.050, .388, .91, .176],
          lineThree: [.054, .5513, .31, .19],
          period: [.662, .5386, .065, .19],
          underline: [.3634, .708, .303, .008],
          optionTop: .801,
        }
      : {
          brand: [.902, .076, .05, .07],
          lineOne: [.048, .1893, .88, .195],
          lineTwo: [.050, .388, .91, .176],
          lineThree: [.054, .5513, .31, .19],
          period: [.662, .5386, .065, .19],
          underline: [.3634, .708, .303, .008],
          optionTop: .801,
        };

    text("brandLetter", config.brandLetter, rows.brand, .080, .76, "goodthings-title goodthings-brand");
    text("lineOne", config.lineOne, rows.lineOne, .22, .895);
    text("lineTwo", config.lineTwo, rows.lineTwo, .22, .982);
    const lineThree = text("lineThree", config.lineThree, rows.lineThree, .22, .94, "goodthings-title goodthings-line-three");
    lineThree.element.querySelector(".pg-glyphs").style.transform += " scaleY(1.025)";
    const period = text("period", config.period, rows.period, .22, .88, "goodthings-title goodthings-period");
    period.element.querySelector(".pg-glyphs").style.transform += " scaleY(1.22)";

    const underline = document.createElement("div");
    underline.className = "goodthings-underline";
    underline.dataset.layoutItem = "goodthingstothose32-underline";
    Object.assign(underline.style, {
      left: `${rows.underline[0] * 100}%`, top: `${rows.underline[1] * 100}%`,
      width: `${rows.underline[2] * 100}%`, height: `${rows.underline[3] * 100}%`,
    });
    board.append(underline);

    const choices = [
      ["optionOne", config.optionOne, .0695, .117, .090, 1.00, .008, 1],
      ["optionTwo", config.optionTwo, .2205, .2657, .095, 1.05, -.002, 1.25],
      ["optionThree", config.optionThree, .3885, .437, .145, .91, .008, .89],
      ["optionFour", config.optionFour, .5955, .6405, .130, .94, .008, 1],
      ["optionFive", config.optionFive, .7865, .8322, .155, .83, .005, .86],
    ];
    const checkedOption = Math.max(1, Math.min(5, Number(state.checkedOption ?? config.checkedOption)));
    choices.forEach(([key, label, x, labelX, labelWidth, targetWidth, labelYOffset, scaleY], index) => {
      addGoodThingsCheckbox(
        board,
        key,
        state[key] ?? label,
        [x, rows.optionTop, .040, square ? .052 : .058],
        [labelX, rows.optionTop + labelYOffset, labelWidth, .064, targetWidth, scaleY],
        index + 1 === checkedOption,
      );
    });
  }

  function addRudyBrownieComposition(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const background = document.createElement("img");
    background.className = "rudybrownie-photo";
    background.alt = "";
    background.src = `${root}${square ? config.squarePhoto : config.photo}`;
    background.dataset.layoutItem = "rudybrownie32-text-free-sunset-photo";
    board.append(background);

    const rows = square
      ? [
          ["lineOne", [.055, .245, .89, .235], .265, .80],
          ["lineTwo", [.035, .487, .93, .285], .305, .91],
        ]
      : [
          ["lineOne", [.12, .235, .76, .245], .245, .64],
          ["lineTwo", [.065, .475, .87, .30], .29, .90],
        ];

    rows.forEach(([key, box, maxSize, targetWidth]) => {
      makePlayGridText(board, key, state[key] ?? config[key], box, {
        className: "rudybrownie-type",
        templateId: "rudybrownie32",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
        scale,
        maxSize,
        targetWidth,
        widthFactor: .96,
        heightFactor: .84,
        tracking: -.045,
        align: "center",
        justify: "center",
        color: "#fff3d8",
      });
    });
  }

  function addText(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.scale ?? 1);
    const maxSize = (square ? 255 : 300) * scale;
    const boxes = [
      { key: "lineOne", value: config.lineOne, box: [.055, .095, .89, .22] },
      { key: "lineTwo", value: config.lineTwo, box: [.055, .323, .80, .24] },
    ];
    const rows = boxes.map(({ key, value, box }) => {
      const element = document.createElement("div");
      element.className = "urc-line";
      element.dataset.layoutItem = `${config.style}-${key}`;
      element.dataset.displayItem = "true";
      element.textContent = String(state[key] ?? value);
      Object.assign(element.style, {
        left: `${box[0] * 100}%`,
        top: `${box[1] * 100}%`,
        width: `${box[2] * 100}%`,
        height: `${box[3] * 100}%`,
        color: "#08060c",
        fontWeight: "400",
        letterSpacing: "-.035em",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
      });
      board.append(element);
      return { element, box };
    });
    const fitted = rows.map(({ element, box }) => window.SupportLayout.fitLine(element, {
      width: board.clientWidth * box[2] * .97,
      height: board.clientHeight * box[3] * .91,
      maxSize,
      minSize: 8,
      tracking: -.035,
    }));
    const sharedSize = Math.min(...fitted);
    rows.forEach(({ element }) => { element.style.fontSize = `${sharedSize}px`; });
    makeStar(board);
  }

  function addEsensText(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const headlineScale = Number(state.headlineScale ?? 1);
    const headlineBox = square ? [.085, .369, .83, .35] : [.115, .369, .77, .35];
    const headline = document.createElement("div");
    headline.className = "urc-headline";
    headline.dataset.layoutItem = "esens32-headline";
    headline.dataset.displayItem = "true";
    const headlineGlyphs = document.createElement("span");
    headlineGlyphs.className = "urc-headline-glyphs";
    headlineGlyphs.textContent = String(state.headline ?? config.headline);
    headline.append(headlineGlyphs);
    Object.assign(headline.style, {
      left: `${headlineBox[0] * 100}%`,
      top: `${headlineBox[1] * 100}%`,
      width: `${headlineBox[2] * 100}%`,
      height: `${headlineBox[3] * 100}%`,
      color: "#ff3fa2",
      fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
      fontWeight: "400",
    });
    board.append(headline);
    const headlineSize = window.SupportLayout.fitLine(headline, {
      width: board.clientWidth * headlineBox[2] * .98,
      height: board.clientHeight * headlineBox[3] * .90,
      maxSize: 340 * headlineScale,
      minSize: 8,
      tracking: -.025,
    });
    headline.style.fontSize = `${headlineSize}px`;
    const titleRange = document.createRange();
    titleRange.selectNodeContents(headlineGlyphs);
    const naturalWidth = titleRange.getBoundingClientRect().width;
    const targetWidth = board.clientWidth * (square ? .80 : .747);
    const widthScale = naturalWidth > 0 ? Math.min(2.2, targetWidth / naturalWidth) : 1;
    headlineGlyphs.style.transform = `scaleX(${widthScale})`;

    const captionScale = Number(state.captionScale ?? 1);
    const captionBox = square ? [.235, .671, .53, .055] : [.315, .674, .37, .055];
    const caption = document.createElement("div");
    caption.className = "urc-caption";
    caption.dataset.layoutItem = "esens32-caption";
    caption.textContent = String(state.caption ?? config.caption);
    Object.assign(caption.style, {
      left: `${captionBox[0] * 100}%`,
      top: `${captionBox[1] * 100}%`,
      width: `${captionBox[2] * 100}%`,
      height: `${captionBox[3] * 100}%`,
      color: "#ff96d3",
      fontFamily: "Arial, Helvetica, sans-serif",
    });
    board.append(caption);
    const captionSize = window.SupportLayout.fitLine(caption, {
      width: board.clientWidth * captionBox[2] * .98,
      height: board.clientHeight * captionBox[3] * .90,
      maxSize: (square ? 15 : 22) * captionScale,
      minSize: 6,
      tracking: .19,
    });
    caption.style.fontSize = `${captionSize}px`;
  }

  function addAsbonHeadline(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.headlineScale ?? 1);
    const box = square ? [.12, .14, .76, .32] : [.11, .169, .78, .32];
    const headline = document.createElement("div");
    headline.className = "urc-asbon-headline";
    headline.dataset.layoutItem = "asbon32-headline";
    headline.dataset.displayItem = "true";
    const glyphs = document.createElement("span");
    glyphs.className = "urc-asbon-glyphs";
    glyphs.textContent = String(state.headline ?? config.headline);
    headline.append(glyphs);
    Object.assign(headline.style, {
      left: `${box[0] * 100}%`,
      top: `${box[1] * 100}%`,
      width: `${box[2] * 100}%`,
      height: `${box[3] * 100}%`,
      color: "#02000c",
      fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
      fontWeight: "400",
    });
    board.append(headline);
    const size = window.SupportLayout.fitLine(headline, {
      width: board.clientWidth * box[2] * .98,
      height: board.clientHeight * box[3] * .90,
      maxSize: 340 * scale,
      minSize: 8,
      tracking: -.025,
    });
    headline.style.fontSize = `${size}px`;
    const range = document.createRange();
    range.selectNodeContents(glyphs);
    const naturalWidth = range.getBoundingClientRect().width;
    const targetWidth = board.clientWidth * (square ? .76 : .712);
    const widthScale = naturalWidth > 0 ? Math.min(2.2, targetWidth / naturalWidth) : 1;
    glyphs.style.transform = `scaleX(${widthScale})`;
  }

  function addStyleCompareText(board, config, state) {
    const familyMemberFont = window.SupportFamilyAvailable?.includes("SupportFamily1")
      ? "SupportFamily1" : "SupportDisplay";
    const labels = [
      { key: "leftLabel", value: config.leftLabel, box: [.2922, .0732, .4097, .0758], familyMember: true },
      { key: "rightLabel", value: config.rightLabel, box: [.2120, .1515, .5769, .1010], familyMember: false },
    ];
    const glyphs = [
      { key: "leftGlyph", value: config.leftGlyph, box: [.0718, .2955, .4299, .6553], familyMember: true },
      { key: "rightGlyph", value: config.rightGlyph, box: [.5346, .2955, .3928, .6553], familyMember: false },
    ];
    const addLayer = ({ key, value, box, familyMember, kind }) => {
      const isGlyph = kind === "glyph";
      const face = familyMember ? familyMemberFont : "SupportDisplay";
      const element = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      element.classList.add(isGlyph ? "urc-compare-glyph" : "urc-compare-label");
      element.setAttribute("viewBox", "0 0 1000 1000");
      element.setAttribute("preserveAspectRatio", "none");
      element.dataset.layoutItem = `italicregular32-${key}`;
      element.dataset.displayItem = "true";
      Object.assign(element.style, {
        left: `${box[0] * 100}%`,
        top: `${box[1] * 100}%`,
        width: `${box[2] * 100}%`,
        height: `${box[3] * 100}%`,
        color: "#0a0908",
        fontSize: "1000px",
      });
      const content = document.createElementNS("http://www.w3.org/2000/svg", "text");
      content.setAttribute("x", "0");
      content.setAttribute("y", "0");
      content.setAttribute("font-size", "1000");
      content.setAttribute("font-family", face);
      content.setAttribute("font-style", "normal");
      content.setAttribute("font-weight", "400");
      content.setAttribute("fill", "#0a0908");
      content.textContent = String(state[key] ?? value);
      element.append(content);
      board.append(element);
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      context.font = `1000px ${face}`;
      const ink = context.measureText(content.textContent);
      const inkWidth = ink.actualBoundingBoxLeft + ink.actualBoundingBoxRight;
      const inkHeight = ink.actualBoundingBoxAscent + ink.actualBoundingBoxDescent;
      if (inkWidth > 0 && inkHeight > 0) {
        element.setAttribute("viewBox", `${-ink.actualBoundingBoxLeft} ${-ink.actualBoundingBoxAscent} ${inkWidth} ${inkHeight}`);
      } else {
        const fallback = content.getBBox();
        if (fallback.width > 0 && fallback.height > 0) {
          element.setAttribute("viewBox", `${fallback.x} ${fallback.y} ${fallback.width} ${fallback.height}`);
        }
      }
    };
    labels.forEach((row) => addLayer({ ...row, kind: "label" }));
    glyphs.forEach((row) => addLayer({ ...row, kind: "glyph" }));
  }

  function addSmokeLetters(board, config, state) {
    const labels = [
      { key: "topLeft", box: [.026, .039, .24, .022], align: "left" },
      { key: "topRight", box: [.735, .039, .239, .022], align: "right" },
      { key: "bottomLeft", box: [.026, .947, .27, .022], align: "left" },
      { key: "bottomRight", box: [.704, .949, .27, .022], align: "right" },
    ];
    const glyphs = [
      { key: "leftBrace", value: config.leftBrace, box: [.158, .180, .102, .615], italic: false },
      { key: "leftGlyph", value: config.leftGlyph, box: [.320, .180, .255, .700], italic: true },
      { key: "rightGlyph", value: config.rightGlyph, box: [.510, .348, .190, .385], italic: true },
      { key: "rightBrace", value: config.rightBrace, box: [.735, .180, .102, .615], italic: false },
    ];
    for (const row of labels) {
      const label = document.createElement("div");
      label.className = `urc-smoke-label urc-smoke-${row.align}`;
      label.dataset.layoutItem = `smokeletters32-${row.key}`;
      label.textContent = String(config[row.key]);
      Object.assign(label.style, {
        left: `${row.box[0] * 100}%`,
        top: `${row.box[1] * 100}%`,
        width: `${row.box[2] * 100}%`,
        height: `${row.box[3] * 100}%`,
      });
      board.append(label);
    }
    for (const row of glyphs) {
      const isLetter = row.key === "leftGlyph" || row.key === "rightGlyph";
      const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      svg.classList.add("urc-smoke-glyph");
      svg.setAttribute("viewBox", "0 0 1000 1000");
      svg.setAttribute("preserveAspectRatio", "none");
      svg.dataset.layoutItem = `smokeletters32-${row.key}`;
      svg.dataset.displayItem = "true";
      Object.assign(svg.style, {
        left: `${row.box[0] * 100}%`,
        top: `${row.box[1] * 100}%`,
        width: `${row.box[2] * 100}%`,
        height: `${row.box[3] * 100}%`,
        fontSize: "1000px",
      });
      const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
      text.setAttribute("x", "0");
      text.setAttribute("y", "0");
      text.setAttribute("font-size", "1000");
      text.setAttribute("font-family", "SupportDisplay, 'Noto Serif Display', Georgia, serif");
      text.setAttribute("font-style", row.italic ? "italic" : "normal");
      text.setAttribute("font-weight", "400");
      text.setAttribute("fill", "#090909");
      text.textContent = String(state[row.key] ?? row.value);
      svg.append(text);
      board.append(svg);
      const canvas = document.createElement("canvas");
      const context = canvas.getContext("2d");
      context.font = `${row.italic ? "italic " : ""}1000px SupportDisplay`;
      const metrics = context.measureText(text.textContent);
      const width = metrics.actualBoundingBoxLeft + metrics.actualBoundingBoxRight;
      const height = metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent;
      if (width > 0 && height > 0) {
        svg.setAttribute("viewBox", `${-metrics.actualBoundingBoxLeft} ${-metrics.actualBoundingBoxAscent} ${width} ${height}`);
      } else {
        const fallback = text.getBBox();
        if (fallback.width > 0 && fallback.height > 0) {
          svg.setAttribute("viewBox", `${fallback.x} ${fallback.y} ${fallback.width} ${fallback.height}`);
        }
      }
      if (!isLetter) svg.dataset.displayItem = "false";
    }
  }

  function addBlackerWearText(board, config, state) {
    const square = board.dataset.ratio === "1x1";
    const scale = Number(state.displayScale ?? 1);
    const rows = [
      { key: "leftTitle", value: config.leftTitle, box: [.041, .067, .445, .145], targetWidth: .43, color: "#fff", italic: false, tracking: -.04 },
      { key: "leftTagline", value: config.leftTagline, box: [.082, .806, .355, .135], targetWidth: .32, color: "#fff", italic: false, tracking: -.035 },
      { key: "rightTitle", value: config.rightTitle, box: [.565, .498, .414, .145], targetWidth: .41, color: "#0b0b0b", italic: false, tracking: -.04 },
      { key: "rightItalic", value: config.rightItalic, box: [.565, .665, .414, .137], targetWidth: .355, color: "#0b0b0b", italic: true, tracking: -.035 },
    ];
    for (const row of rows) {
      const box = square && row.key === "leftTitle"
        ? [.035, .065, .49, .145]
        : row.box;
      const element = document.createElement("div");
      element.className = "urc-fashion-type";
      element.dataset.layoutItem = `blackerwear32-${row.key}`;
      element.dataset.displayItem = "true";
      const glyphs = document.createElement("span");
      glyphs.className = "urc-fashion-glyphs";
      glyphs.textContent = String(state[row.key] ?? row.value);
      element.append(glyphs);
      Object.assign(element.style, {
        left: `${box[0] * 100}%`,
        top: `${box[1] * 100}%`,
        width: `${box[2] * 100}%`,
        height: `${box[3] * 100}%`,
        color: row.color,
        fontStyle: row.italic ? "italic" : "normal",
        letterSpacing: `${row.tracking}em`,
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
      });
      board.append(element);
      const maxSize = board.clientHeight * (row.key.startsWith("left") ? .19 : .18) * scale;
      window.SupportLayout.fitLine(element, {
        width: board.clientWidth * box[2] * .98,
        height: board.clientHeight * box[3] * .90,
        maxSize,
        minSize: 8,
        tracking: row.tracking,
      });
      const range = document.createRange();
      range.selectNodeContents(glyphs);
      const naturalWidth = range.getBoundingClientRect().width;
      const targetWidth = board.clientWidth * row.targetWidth;
      const widthScale = naturalWidth > 0
        ? Math.max(.65, Math.min(2.2, targetWidth / naturalWidth)) : 1;
      glyphs.style.transform = `scaleX(${widthScale})`;
    }

    const bodyBox = square ? [.574, .852, .398, .138] : [.574, .859, .398, .130];
    const body = document.createElement("div");
    body.className = "urc-fashion-copy";
    body.dataset.layoutItem = "blackerwear32-bodyCopy";
    body.textContent = String(state.bodyCopy ?? config.bodyCopy);
    Object.assign(body.style, {
      left: `${bodyBox[0] * 100}%`,
      top: `${bodyBox[1] * 100}%`,
      width: `${bodyBox[2] * 100}%`,
      height: `${bodyBox[3] * 100}%`,
      fontSize: `${board.clientWidth * (square ? .0143 : .0131)}px`,
    });
    board.append(body);
  }

  function addSilentNightText(board, config, state) {
    const scale = Number(state.textScale ?? 1);
    const rows = [
      { key: "leftWord", value: config.leftWord, box: [.040, .292, .43, .37], targetWidth: .42 },
      { key: "rightWord", value: config.rightWord, box: [.530, .292, .43, .37], targetWidth: .42 },
    ];
    const elements = rows.map((row) => {
      const element = document.createElement("div");
      element.className = "urc-night-word";
      element.dataset.layoutItem = `silentnight32-${row.key}`;
      element.dataset.displayItem = "true";
      const glyphs = document.createElement("span");
      glyphs.className = "urc-night-glyphs";
      glyphs.textContent = String(state[row.key] ?? row.value);
      element.append(glyphs);
      Object.assign(element.style, {
        left: `${row.box[0] * 100}%`,
        top: `${row.box[1] * 100}%`,
        width: `${row.box[2] * 100}%`,
        height: `${row.box[3] * 100}%`,
        color: "#f6f5f3",
        fontFamily: "SupportDisplay, 'Noto Serif Display', Georgia, serif",
      });
      board.append(element);
      return { element, glyphs, row };
    });
    const fontSize = window.SupportLayout.fitLinesTogether(
      elements.map(({ element }) => element),
      {
        width: board.clientWidth * .90,
        height: board.clientHeight * .37 * .90,
        maxSize: board.clientHeight * .44 * scale,
        minSize: 8,
        tracking: -.02,
      },
    );
    elements.forEach(({ glyphs, row }) => {
      const range = document.createRange();
      range.selectNodeContents(glyphs);
      const naturalWidth = range.getBoundingClientRect().width;
      const targetWidth = board.clientWidth * row.targetWidth;
      const widthScale = naturalWidth > 0
        ? Math.max(.45, Math.min(2.4, targetWidth / naturalWidth)) : 1;
      glyphs.style.transform = `scaleX(${widthScale})`;
    });
    return fontSize;
  }

  window.UserReferenceBatchC = {
    ids: Object.keys(templates),
    create(id) {
      const config = templates[id];
      if (!config) throw new Error(`Unknown reference template: ${id}`);
      const design = {
        id,
        title: config.title,
        literalKeys: id === "rudybrownie32"
          ? ["lineOne", "lineTwo"]
          : id === "goodthingstothose32"
          ? ["brandLetter", "lineOne", "lineTwo", "lineThree", "period", "optionOne", "optionTwo", "optionThree", "optionFour", "optionFive"]
          : id === "nightonearth32"
          ? ["headlineOne", "headlineTwo"]
          : id === "itsokay32"
          ? ["headlineOne", "headlineTwo", "studioOne", "studioTwo", "footer"]
          : id === "hazysky32"
          ? ["headlineOne", "headlineTwo", "caption"]
          : id === "owlstory32"
          ? ["titleLineOne", "titleLineTwo", "captionOne", "captionTwo", "captionThree"]
          : id === "sociato32"
          ? ["initial", "highlight", "bodyCopy"]
          : id === "allworkplay32"
          ? ["lineOne", "lineTwo", "lineThree", "lineFour"]
          : id === "soulrevenge32"
          ? ["cinemaCredit", "titleOne", "titleTwo", "director", "castOne", "castTwo", "castThree", "castFour", "dragonTitle", "yearOne", "yearTwo", "yearThree", "yearFour", "dragonTagline"]
          : id === "littlemadquote32"
          ? ["topLeft", "topRight", "lineOne", "lineTwo", "lineThree", "attribution", "footerLeft", "footerRight"]
          : id === "medievalcreatures32"
          ? ["topLine", "yearLine", "bottomLine"]
          : id === "fridayrunning32"
          ? ["topLeftLabel", "topRightLabel", "topTitle", "headline", "leftNumber", "club", "rightNumber", "footerLeft", "footerRight"]
          : id === "playgrid32"
          ? ["topLeft", "topRight", "label", "year", "gridTitle", "topNumber", "leftNumber", "rightNumber", "bottomNumber"]
          : id === "esens32" ? ["headline", "caption"]
          : id === "asbon32" ? ["headline"]
            : id === "italicregular32"
              ? ["leftLabel", "rightLabel", "leftGlyph", "rightGlyph"]
              : id === "smokeletters32"
                ? ["topLeft", "topRight", "bottomLeft", "bottomRight", "leftGlyph", "rightGlyph"]
                : id === "blackerwear32"
                  ? ["leftTitle", "leftTagline", "rightTitle", "rightItalic", "bodyCopy"]
                  : id === "silentnight32" ? ["leftWord", "rightWord"]
                  : ["lineOne", "lineTwo"],
        defaults: id === "rudybrownie32" ? {
          lineOne: config.lineOne, lineTwo: config.lineTwo, displayScale: 1,
        } : id === "goodthingstothose32" ? {
          brandLetter: config.brandLetter, lineOne: config.lineOne,
          lineTwo: config.lineTwo, lineThree: config.lineThree, period: config.period,
          optionOne: config.optionOne, optionTwo: config.optionTwo,
          optionThree: config.optionThree, optionFour: config.optionFour,
          optionFive: config.optionFive, checkedOption: config.checkedOption,
          displayScale: 1,
        } : id === "nightonearth32" ? {
          headlineOne: config.headlineOne, headlineTwo: config.headlineTwo,
          displayScale: 1,
        } : id === "itsokay32" ? {
          headlineOne: config.headlineOne, headlineTwo: config.headlineTwo,
          studioOne: config.studioOne, studioTwo: config.studioTwo,
          footer: config.footer, displayScale: 1,
        } : id === "hazysky32" ? {
          headlineOne: config.headlineOne, headlineTwo: config.headlineTwo,
          caption: config.caption, displayScale: 1,
        } : id === "owlstory32" ? {
          titleLineOne: config.titleLineOne, titleLineTwo: config.titleLineTwo,
          captionOne: config.captionOne, captionTwo: config.captionTwo,
          captionThree: config.captionThree, displayScale: 1,
        } : id === "sociato32" ? {
          initial: config.initial, highlight: config.highlight,
          bodyCopy: config.bodyCopy, displayScale: 1,
        } : id === "allworkplay32" ? {
          lineOne: config.lineOne, lineTwo: config.lineTwo,
          lineThree: config.lineThree, lineFour: config.lineFour,
          displayScale: 1,
        } : id === "soulrevenge32" ? {
          cinemaCredit: config.cinemaCredit, titleOne: config.titleOne,
          titleTwo: config.titleTwo, director: config.director,
          castOne: config.castOne, castTwo: config.castTwo,
          castThree: config.castThree, castFour: config.castFour,
          dragonTitle: config.dragonTitle, yearOne: config.yearOne,
          yearTwo: config.yearTwo, yearThree: config.yearThree,
          yearFour: config.yearFour, dragonTagline: config.dragonTagline,
          displayScale: 1,
        } : id === "littlemadquote32" ? {
          topLeft: config.topLeft, topRight: config.topRight,
          lineOne: config.lineOne, lineTwo: config.lineTwo,
          lineThree: config.lineThree, attribution: config.attribution,
          footerLeft: config.footerLeft, footerRight: config.footerRight,
          displayScale: 1,
        } : id === "medievalcreatures32" ? {
          topLine: config.topLine, yearLine: config.yearLine,
          bottomLine: config.bottomLine, displayScale: 1,
        } : id === "fridayrunning32" ? {
          topLeftLabel: config.topLeftLabel, topRightLabel: config.topRightLabel,
          topTitle: config.topTitle, headline: config.headline,
          leftNumber: config.leftNumber, club: config.club,
          rightNumber: config.rightNumber, footerLeft: config.footerLeft,
          footerRight: config.footerRight, displayScale: 1,
        } : id === "playgrid32" ? {
          topLeft: config.topLeft, topRight: config.topRight,
          label: config.label, year: config.year, gridTitle: config.gridTitle,
          topNumber: config.topNumber, leftNumber: config.leftNumber,
          rightNumber: config.rightNumber, bottomNumber: config.bottomNumber,
          displayScale: 1,
        } : id === "esens32"
          ? { headline: config.headline, caption: config.caption, headlineScale: 1, captionScale: 1 }
          : id === "asbon32" ? { headline: config.headline, headlineScale: 1 }
            : id === "italicregular32" ? {
              leftLabel: config.leftLabel, rightLabel: config.rightLabel,
              leftGlyph: config.leftGlyph, rightGlyph: config.rightGlyph,
            } : id === "smokeletters32" ? {
              leftGlyph: config.leftGlyph, rightGlyph: config.rightGlyph,
            } : id === "blackerwear32" ? {
              leftTitle: config.leftTitle, leftTagline: config.leftTagline,
              rightTitle: config.rightTitle, rightItalic: config.rightItalic,
              bodyCopy: config.bodyCopy, displayScale: 1,
            } : id === "silentnight32" ? {
              leftWord: config.leftWord, rightWord: config.rightWord, textScale: 1,
            } : { lineOne: config.lineOne, lineTwo: config.lineTwo, scale: 1 },
        controls: id === "rudybrownie32" ? [
          { key: "lineOne", label: "First display line", type: "text" },
          { key: "lineTwo", label: "Second display line", type: "text" },
          { key: "displayScale", label: "Type scale", min: .82, max: 1.12, step: .01, value: 1 },
        ] : id === "goodthingstothose32" ? [
          { key: "brandLetter", label: "Upper-right initial", type: "text" },
          { key: "lineOne", label: "Quote line one", type: "text" },
          { key: "lineTwo", label: "Quote line two", type: "text" },
          { key: "lineThree", label: "Quote line three", type: "text" },
          { key: "period", label: "Ending punctuation", type: "text" },
          { key: "optionOne", label: "Checkbox label one", type: "text" },
          { key: "optionTwo", label: "Checkbox label two", type: "text" },
          { key: "optionThree", label: "Checkbox label three", type: "text" },
          { key: "optionFour", label: "Checkbox label four", type: "text" },
          { key: "optionFive", label: "Checkbox label five", type: "text" },
          { key: "checkedOption", label: "Checked choice (1–5)", type: "range", min: 1, max: 5, step: 1, value: 2 },
          { key: "displayScale", label: "Quote scale", min: .82, max: 1.12, step: .01, value: 1 },
        ] : id === "nightonearth32" ? [
          { key: "headlineOne", label: "First display line", type: "text" },
          { key: "headlineTwo", label: "Second display line", type: "text" },
          { key: "displayScale", label: "Type scale", min: .82, max: 1.12, step: .01, value: 1 },
        ] : id === "itsokay32" ? [
          { key: "headlineOne", label: "First display line", type: "text" },
          { key: "headlineTwo", label: "Second display line", type: "text" },
          { key: "studioOne", label: "Studio line one", type: "text" },
          { key: "studioTwo", label: "Studio line two", type: "text" },
          { key: "footer", label: "Footer label", type: "text" },
          { key: "displayScale", label: "Type scale", min: .82, max: 1.12, step: .01, value: 1 },
        ] : id === "hazysky32" ? [
          { key: "headlineOne", label: "First display line", type: "text" },
          { key: "headlineTwo", label: "Second display line", type: "text" },
          { key: "caption", label: "Small caption", type: "text" },
          { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01, value: 1 },
        ] : id === "owlstory32" ? [
          { key: "titleLineOne", label: "Title line one", type: "text" },
          { key: "titleLineTwo", label: "Title line two", type: "text" },
          { key: "captionOne", label: "Subhead line one", type: "text" },
          { key: "captionTwo", label: "Subhead line two", type: "text" },
          { key: "captionThree", label: "Subhead line three", type: "text" },
          { key: "displayScale", label: "Type scale", min: .82, max: 1.12, step: .01, value: 1 },
        ] : id === "sociato32" ? [
          { key: "initial", label: "Large initial", type: "text" },
          { key: "highlight", label: "Gold lead-in", type: "text" },
          { key: "bodyCopy", label: "Editorial copy", type: "textarea", rows: 7 },
          { key: "displayScale", label: "Initial scale", min: .84, max: 1.12, step: .01, value: 1 },
        ] : id === "allworkplay32" ? [
          { key: "lineOne", label: "Quote line one", type: "text" },
          { key: "lineTwo", label: "Quote line two", type: "text" },
          { key: "lineThree", label: "Quote line three", type: "text" },
          { key: "lineFour", label: "Quote line four", type: "text" },
          { key: "displayScale", label: "Quote scale", min: .84, max: 1.12, step: .01, value: 1 },
        ] : id === "soulrevenge32" ? [
          { key: "cinemaCredit", label: "Cinema credit", type: "text" },
          { key: "titleOne", label: "Film title, line one", type: "text" },
          { key: "titleTwo", label: "Film title, line two", type: "text" },
          { key: "director", label: "Director credit", type: "text" },
          { key: "castOne", label: "Cast credit, lower left", type: "textarea", rows: 2 },
          { key: "castTwo", label: "Cast credit, left center", type: "textarea", rows: 2 },
          { key: "castThree", label: "Cast credit, right center", type: "textarea", rows: 2 },
          { key: "castFour", label: "Cast credit, lower right", type: "textarea", rows: 2 },
          { key: "dragonTitle", label: "Dragon Knight title", type: "text" },
          { key: "yearOne", label: "Upper-left numeral", type: "text" },
          { key: "yearTwo", label: "Upper-right numeral", type: "text" },
          { key: "yearThree", label: "Lower-left numeral", type: "text" },
          { key: "yearFour", label: "Lower-right numeral", type: "text" },
          { key: "dragonTagline", label: "Dragon Knight tagline", type: "text" },
          { key: "displayScale", label: "Display scale", min: .86, max: 1.12, step: .01, value: 1 },
        ] : id === "littlemadquote32" ? [
          { key: "topLeft", label: "Upper-left caption", type: "text" },
          { key: "topRight", label: "Upper-right caption", type: "text" },
          { key: "lineOne", label: "Quote line one", type: "text" },
          { key: "lineTwo", label: "Quote line two", type: "text" },
          { key: "lineThree", label: "Quote line three", type: "text" },
          { key: "attribution", label: "Attribution", type: "text" },
          { key: "footerLeft", label: "Lower-left caption", type: "text" },
          { key: "footerRight", label: "Lower-right caption", type: "text" },
          { key: "displayScale", label: "Quote scale", min: .86, max: 1.12, step: .01, value: 1 },
        ] : id === "medievalcreatures32" ? [
          { key: "topLine", label: "Upper caption", type: "text" },
          { key: "yearLine", label: "Bracketed numerals", type: "text" },
          { key: "bottomLine", label: "Lower caption", type: "text" },
          { key: "displayScale", label: "Specimen scale", min: .84, max: 1.12, step: .01, value: 1 },
        ] : id === "fridayrunning32" ? [
          { key: "topLeftLabel", label: "Upper-left label", type: "text" },
          { key: "topRightLabel", label: "Upper-right label", type: "text" },
          { key: "topTitle", label: "White title", type: "text" },
          { key: "headline", label: "Blue headline", type: "text" },
          { key: "leftNumber", label: "Left number", type: "text" },
          { key: "club", label: "Club line", type: "text" },
          { key: "rightNumber", label: "Right number", type: "text" },
          { key: "footerLeft", label: "Lower-left label", type: "text" },
          { key: "footerRight", label: "Lower-right label", type: "text" },
          { key: "displayScale", label: "Display scale", min: .84, max: 1.12, step: .01, value: 1 },
        ] : id === "playgrid32" ? [
          { key: "topLeft", label: "Poster upper-left label", type: "text" },
          { key: "topRight", label: "Poster upper-right label", type: "text" },
          { key: "label", label: "Poster title", type: "text" },
          { key: "year", label: "Large numerals", type: "text" },
          { key: "gridTitle", label: "Grid heading", type: "text" },
          { key: "topNumber", label: "Top center tile", type: "text" },
          { key: "leftNumber", label: "Middle left tile", type: "text" },
          { key: "rightNumber", label: "Middle right tile", type: "text" },
          { key: "bottomNumber", label: "Bottom center tile", type: "text" },
          { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01, value: 1 },
        ] : id === "esens32" ? [
          { key: "headline", label: "Display word", type: "text" },
          { key: "caption", label: "Caption", type: "text" },
          { key: "headlineScale", label: "Display scale", min: .78, max: 1.12, step: .01, value: 1 },
          { key: "captionScale", label: "Caption scale", min: .80, max: 1.20, step: .01, value: 1 },
        ] : id === "asbon32" ? [
          { key: "headline", label: "Display word", type: "text" },
          { key: "headlineScale", label: "Display scale", min: .78, max: 1.12, step: .01, value: 1 },
        ] : id === "italicregular32" ? [
          { key: "leftLabel", label: "Sibling style label", type: "text" },
          { key: "rightLabel", label: "Current style label", type: "text" },
          { key: "leftGlyph", label: "Sibling letter", type: "text" },
          { key: "rightGlyph", label: "Current letter", type: "text" },
        ] : id === "smokeletters32" ? [
          { key: "leftGlyph", label: "Left letter", type: "text" },
          { key: "rightGlyph", label: "Right letter", type: "text" },
        ] : id === "blackerwear32" ? [
          { key: "leftTitle", label: "Upper-left display line", type: "text" },
          { key: "leftTagline", label: "Lower-left display line", type: "text" },
          { key: "rightTitle", label: "Right headline", type: "text" },
          { key: "rightItalic", label: "Italic headline line", type: "text" },
          { key: "bodyCopy", label: "Editorial body copy", type: "textarea", rows: 4 },
          { key: "displayScale", label: "Display scale", min: .86, max: 1.12, step: .01, value: 1 },
        ] : id === "silentnight32" ? [
          { key: "leftWord", label: "First word", type: "text" },
          { key: "rightWord", label: "Second word", type: "text" },
          { key: "textScale", label: "Type scale", min: .86, max: 1.12, step: .01, value: 1 },
        ] : [
          { key: "lineOne", label: "First line", type: "text" },
          { key: "lineTwo", label: "Second line", type: "text" },
          { key: "scale", label: "Headline scale", min: .78, max: 1.12, step: .01, value: 1 },
        ],
          contrastException: {
          minimum: id === "rudybrownie32" ? 2.2 : id === "nightonearth32" ? 2.2 : id === "sociato32" ? 3 : id === "allworkplay32" ? 4.5 : id === "soulrevenge32" ? 3 : id === "littlemadquote32" ? 2.2 : id === "medievalcreatures32" ? 3 : 4.5,
            rationale: id === "rudybrownie32"
              ? "Warm cream display type overlays the source's dusk-sunset photography; a restrained dark shadow protects readability across sky and water."
              : id === "goodthingstothose32"
              ? "Warm cream lettering sits on the vivid electric blue-purple sampled from the original reference."
              : id === "nightonearth32"
              ? "The source uses saturated electric-indigo display type on near-black; this palette is retained for a faithful color specimen."
              : id === "itsokay32"
              ? "Warm cream and muted violet type sit on a near-black field with a dark violet rose illustration."
              : id === "hazysky32"
              ? "Dark serif lettering with a muted-gold edge sits over the source's pale pink, cream, and seafoam painted paper."
              : id === "owlstory32"
              ? "Deep indigo display lettering sits on the pale parchment field in the source illustration."
              : id === "sociato32"
              ? "The large white initial overlays the vivid portrait, and the oversized gold lead-in follows the source editorial palette."
              : id === "allworkplay32"
              ? "Lime italic copy follows the source over dark blue frozen texture with bright ice highlights."
              : id === "soulrevenge32"
              ? "The original poster uses deep crimson display type and numeral rings on solid black panels."
              : id === "littlemadquote32"
              ? "Crimson display copy follows the source over a purple glow fading into black."
              : id === "medievalcreatures32"
              ? "The source specimen uses deep red type on black across every text size."
              : id === "fridayrunning32"
            ? "White and cyan display lettering sits on the uninterrupted black field from the source reference."
            : id === "playgrid32"
            ? "The specimen pairs warm white numerals on dark violet tiles with near-black numerals on pale tiles."
            : id === "esens32"
            ? "Pink display lettering overlays the deliberately dark mauve fashion portrait from the source composition."
            : id === "asbon32"
              ? "Near-black display lettering sits on the vivid-pink field from the source composition."
              : id === "italicregular32"
                ? "Near-black type is printed on the light, warm paper field from the source composition."
                : id === "smokeletters32"
                  ? "Near-black display letters sit over a light central area in the source's monochrome smoky paper texture."
                  : id === "blackerwear32"
                    ? "White display lines sit over the dark monochrome portrait, while near-black editorial copy sits on the light gray panel."
              : id === "silentnight32"
                      ? "White display lettering and four-point star ornaments sit on the source's solid black field."
                    : "Near-black display lettering is placed on the uninterrupted vivid pink field from the source composition.",
        },
        render(board, state) {
          board.replaceChildren();
          board.className = `user-reference-board-c user-reference-${config.style}`;
          if (id === "rudybrownie32") {
            board.style.backgroundColor = "#35131b";
            addRudyBrownieComposition(board, config, state);
          } else if (id === "goodthingstothose32") {
            board.style.backgroundColor = "#3e00ff";
            addGoodThingsComposition(board, config, state);
          } else if (id === "nightonearth32") {
            board.style.backgroundColor = "#080806";
            addNightOnEarthComposition(board, config, state);
          } else if (id === "itsokay32") {
            board.style.backgroundColor = "#050307";
            addItsOkayComposition(board, config, state);
          } else if (id === "hazysky32") {
            board.style.backgroundColor = "#fff5ec";
            addHazySkyComposition(board, config, state);
          } else if (id === "owlstory32") {
            board.style.backgroundColor = "#eee7d7";
            addOwlStoryComposition(board, config, state);
          } else if (id === "sociato32") {
            board.style.backgroundColor = "#ffffff";
            addSociatoComposition(board, config, state);
          } else if (id === "allworkplay32") {
            board.style.backgroundColor = "#101923";
            addAllWorkPlayComposition(board, config, state);
          } else if (id === "soulrevenge32") {
            board.style.background = "radial-gradient(ellipse 84% 82% at 50% 50%, #5d427b 0%, #3c284e 58%, #201428 100%)";
            addSoulRevengeComposition(board, config, state);
          } else if (id === "littlemadquote32") {
            board.style.background = "radial-gradient(ellipse 86% 78% at 50% 18%, #4c3667 0%, #30213f 40%, #160f1d 76%, #000000 100%)";
            addLittleMadQuoteComposition(board, config, state);
          } else if (id === "medievalcreatures32") {
            board.style.backgroundColor = "#000000";
            addMedievalCreaturesComposition(board, config, state);
          } else if (id === "esens32") {
            board.style.backgroundColor = "#302831";
            makePortrait(board, config);
            addEsensText(board, config, state);
          } else if (id === "asbon32") {
            board.style.backgroundColor = "#02000c";
            makeAsbonCard(board);
            makeAsbonPhoto(board, config);
            addAsbonHeadline(board, config, state);
          } else if (id === "italicregular32") {
            board.style.backgroundColor = "#f2efe8";
            makePaper(board, config);
            addStyleCompareText(board, config, state);
          } else if (id === "smokeletters32") {
            board.style.backgroundColor = "#dfdfdd";
            makeSmokePaper(board, config);
            addSmokeLetters(board, config, state);
          } else if (id === "blackerwear32") {
            board.style.backgroundColor = "#eeeeec";
            makeBlackerWearPlate(board, config);
            addBlackerWearText(board, config, state);
          } else if (id === "silentnight32") {
            board.style.backgroundColor = "#000000";
            makeSilentNightStars(board);
            addSilentNightText(board, config, state);
          } else if (id === "playgrid32") {
            board.style.backgroundColor = "#000000";
            addPlayGridComposition(board, config, state);
          } else if (id === "fridayrunning32") {
            board.style.backgroundColor = "#000000";
            addFridayRunningComposition(board, config, state);
          } else {
            board.style.backgroundColor = "#ff96d3";
            makePhotoStrip(board, config);
            addText(board, config, state);
          }
          design.fitWarnings = [...board.querySelectorAll("[data-fit-failure]")].map(() =>
            "The headline is too long for its reserved area; shorten it or use a narrower font.");
        },
        getContrast() {
          return window.SupportLayout.contrast(
            id === "rudybrownie32" ? "#fff3d8" : id === "goodthingstothose32" ? "#fffbf3" : id === "nightonearth32" ? "#4b00ff" : id === "itsokay32" ? "#fff9e8" : id === "hazysky32" ? "#070708" : id === "owlstory32" ? "#373750" : id === "sociato32" ? "#a17c00" : id === "allworkplay32" ? "#cfff5c" : id === "soulrevenge32" ? "#d3000c" : id === "littlemadquote32" ? "#d3000c" : id === "medievalcreatures32" ? "#d3000c" : id === "fridayrunning32" ? "#f2f2f0" : id === "playgrid32" ? "#f3f3f0" : id === "esens32" ? "#261f22" : id === "asbon32" ? "#02000c"
              : id === "italicregular32" ? "#0a0908" : id === "silentnight32" ? "#f6f5f3" : "#08060c",
            id === "rudybrownie32" ? "#a53b1c" : id === "goodthingstothose32" ? "#3e00ff" : id === "nightonearth32" ? "#080806" : id === "itsokay32" ? "#523a6a" : id === "hazysky32" ? "#fff5ec" : id === "owlstory32" ? "#eee7d7" : id === "sociato32" ? "#ffffff" : id === "italicregular32" ? "#f2efe8" : id === "smokeletters32" ? "#e1e1df"
              : id === "blackerwear32" ? "#eeeeec" : id === "playgrid32" ? "#41328e"
              : id === "allworkplay32" ? "#162330" : id === "soulrevenge32" ? "#000000" : id === "littlemadquote32" ? "#2a1b36" : id === "medievalcreatures32" ? "#000000" : id === "fridayrunning32" ? "#000000"
                : id === "silentnight32" ? "#000000" : id === "esens32" ? "#ff3fa2" : "#ff96d3",
          );
        },
        getWarnings() { return design.fitWarnings || []; },
      };
      return design;
    },
    getConfig(id) { return templates[id]; },
  };
})();
