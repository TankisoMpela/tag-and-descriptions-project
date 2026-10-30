(function () {
  function titleCase(value) {
    const urls = [];
    let text = String(value ?? "").replace(/(?:https?:\/\/|www\.)[^\s]+/giu, (url) => {
      const token = `\uE000${urls.length}\uE001`;
      urls.push(url);
      return token;
    });
    text = text.replace(/\p{L}+(?:['’]\p{L}+)*/gu, (word) => {
      const first = word.slice(0, 1).toLocaleUpperCase("en");
      const rest = word === word.toLocaleUpperCase("en")
        ? word.slice(1).toLocaleLowerCase("en") : word.slice(1);
      return first + rest;
    });
    return text.replace(/\uE000(\d+)\uE001/gu, (_match, index) => urls[Number(index)]);
  }

  const C = (key, text, box, opts = {}) => ({ key, text, box, ...opts });
  function appendPlakatSymbolBand(board) {
    const band = document.createElement("div");
    band.className = "plakat-symbol-band";
    band.dataset.layoutItem = "plakat-symbol-strip";
    band.setAttribute("aria-hidden", "true");
    const rays = Array.from({ length: 20 }, (_, index) =>
      `<line x1="40" y1="5" x2="40" y2="19" transform="rotate(${index * 18} 40 40)"/>`
    ).join("");
    const petals = Array.from({ length: 8 }, (_, index) =>
      `<circle cx="40" cy="23" r="7" transform="rotate(${index * 45} 40 40)"/>`
    ).join("");
    const arrow = `<path d="M62 32a25 25 0 1 0 3 14"/><path d="M42 10h21v22"/>`;
    const icons = [
      `<svg viewBox="0 0 80 80" aria-hidden="true"><g>${arrow}</g></svg>`,
      `<svg viewBox="0 0 80 80" aria-hidden="true"><path d="M40 9v62M9 40h62M18 18l44 44M62 18 18 62"/></svg>`,
      `<svg viewBox="0 0 80 80" aria-hidden="true"><g>${rays}</g><circle cx="40" cy="40" r="5"/></svg>`,
      `<svg viewBox="0 0 80 80" aria-hidden="true"><path d="M40 68 13 42C-3 25 20 5 40 25 60 5 83 25 67 42Z"/></svg>`,
      `<svg viewBox="0 0 80 80" aria-hidden="true"><g transform="translate(80 0) scale(-1 1)">${arrow}</g></svg>`,
    ];
    icons.forEach((markup) => {
      const icon = document.createElement("span");
      icon.className = "plakat-symbol";
      icon.innerHTML = markup;
      band.append(icon);
    });
    board.append(band);
  }
  const definitions = {
    plakat32: {
      title: "Plakat Family Specimen", source: "T27673_00", contrast: ["#f6f0e5", "#071526"],
      defaults: { headline: "Plakat", note: "Glyph Count\nAvailable Styles", railOne: "Thin", railRightOne: "Black", railTwo: "Roman", railRightTwo: "Italic", markerOne: .74, markerTwo: .52, variable: "Family", footer: "A Typeface Family Study", scale: 1 },
      controls: [{ key: "headline", label: "Display Phrase", type: "text" }, { key: "scale", label: "Phrase Scale", min: .88, max: 1.08, step: .01 }],
      items: [
        C("headline", "headline", [.075,.15,.85,.34], { display: true, max: .31, track: -.035, className: "hero" }),
        C("note", "note", [.115,.52,.36,.12], { max: .037, track: .01, className: "metadata" }),
        C("variable", "variable", [.665,.52,.22,.12], { display: true, max: .11, track: -.02, className: "variable" }),
        C("railOne", "railOne", [.115,.65,.77,.05], { display: true, max: .036, track: .01, className: "rail" }),
        C("railRightOne", "railRightOne", [.115,.65,.77,.05], { display: true, max: .036, track: .01, className: "rail-right" }),
        C("railTwo", "railTwo", [.115,.715,.77,.05], { display: true, max: .036, track: .01, className: "rail" }),
        C("railRightTwo", "railRightTwo", [.115,.715,.77,.05], { display: true, max: .036, track: .01, className: "rail-right" }),
        C("footer", "footer", [.30,.855,.40,.055], { max: .025, track: .22, className: "footer" }),
      ],
    },
    plakatart32: {
      title: "Plakat Artwork Specimen", source: "T27673_10", contrast: ["#f8f2eb", "#111318"],
      defaults: { headline: "Plakat", metaStyles: "18 Styles", metaVariable: "Variable Font", metaWeights: "Thin · Black", metaItalics: "Italics", metaDesigned: "Designed By", metaFoundry: "Mabütype", metaYear: "2025", scale: 1 },
      controls: [{ key: "headline", label: "Display Phrase", type: "text" }, { key: "scale", label: "Headline Scale", min: .88, max: 1.08, step: .01 }],
      items: [
        C("metaStyles", "metaStyles", [.075,.075,.20,.035], { max: .029, track: .045, className: "meta cyan" }),
        C("metaVariable", "metaVariable", [.075,.115,.20,.035], { max: .029, track: .045, className: "meta cyan" }),
        C("metaWeights", "metaWeights", [.075,.155,.20,.035], { max: .029, track: .045, className: "meta cyan" }),
        C("metaItalics", "metaItalics", [.075,.195,.20,.035], { max: .029, track: .045, className: "meta cyan" }),
        C("metaDesigned", "metaDesigned", [.075,.38,.20,.035], { max: .029, track: .045, className: "meta" }),
        C("metaFoundry", "metaFoundry", [.075,.42,.20,.035], { max: .029, track: .045, className: "meta" }),
        C("metaYear", "metaYear", [.075,.46,.20,.035], { max: .029, track: .045, className: "meta" }),
        C("headline", "headline", [.075,.565,.62,.405], { display: true, max: .35, track: -.04, className: "hero" }),
      ],
    },
    birvase32: {
      title: "Red Cyan Print Specimen", source: "T33110_08", contrast: ["#101010", "#67d8e4"],
      defaults: { headline: "Birvase", scale: 1, shadow: 0 },
      controls: [{ key: "headline", label: "Specimen Word", type: "text" }, { key: "scale", label: "Word Scale", min: .86, max: 1.12, step: .01 }],
      items: [C("headline", "headline", [.08,.31,.84,.39], { display: true, max: .38, track: -.04, className: "hero" })],
    },
    weightfamily32: {
      title: "Three Weight Family Proof", source: "T30930_01", contrast: ["#f2f0ea", "#111213"],
      defaults: { row1: "ABCDEFGHIJKLM\nNOPQRSTUVWXYZ", row2: "ABCDEFGHIJKLM\nNOPQRSTUVWXYZ", row3: "ABCDEFGHIJKLM\nNOPQRSTUVWXYZ", label1: "Thin · 100", label2: "Regular · 400", label3: "Bold · 700", scale: 1 },
      controls: [{ key: "label1", label: "First Style Label", type: "text" }, { key: "label2", label: "Second Style Label", type: "text" }, { key: "label3", label: "Third Style Label", type: "text" }, { key: "scale", label: "Specimen Scale", min: .88, max: 1.06, step: .01 }],
      items: [
        C("label1", "Thin · 100", [.045,.115,.19,.07], { max: .04, track: .02, className: "weight-label" }),
        C("row1", "row1", [.245,.085,.715,.18], { display: true, literal: true, face: 1, max: .13, track: -.025, className: "alphabet thin" }),
        C("label2", "Regular · 400", [.045,.405,.19,.07], { max: .04, track: .02, className: "weight-label" }),
        C("row2", "row2", [.245,.36,.715,.18], { display: true, literal: true, face: 2, max: .135, track: -.025, className: "alphabet regular" }),
        C("label3", "Bold · 700", [.045,.72,.19,.07], { max: .04, track: .02, className: "weight-label" }),
        C("row3", "row3", [.245,.66,.715,.18], { display: true, literal: true, face: 3, max: .145, track: -.025, className: "alphabet bold" }),
      ],
    },
    mangosboard32: {
      title: "Modular Typeface Family Board", source: "T30930_04", contrast: ["#f4f1ea", "#111214"],
      defaults: { glyphs: "C€Ω½?†qTTD0123456789", familyThin: "Mangos Thin", familyRegular: "Mangos Regular", familyBlack: "Mangos Black", variable: "Variable", tileA: "Aa", tileWord: "Mangos", tileAt: "@", scale: 1 },
      controls: [{ key: "familyThin", label: "First Family Style", type: "text" }, { key: "familyRegular", label: "Second Family Style", type: "text" }, { key: "familyBlack", label: "Third Family Style", type: "text" }, { key: "glyphs", label: "Character Strip", type: "text" }, { key: "variable", label: "Variable Card", type: "text" }, { key: "tileWord", label: "Center Tile", type: "text" }, { key: "scale", label: "Specimen Scale", min: .9, max: 1.08, step: .01 }],
      items: [
        C("familyThin", "Thin  Aa", [.06,.055,.33,.055], { display: true, face: 1, max: .05, track: -.025, className: "family-sample" }),
        C("familyRegular", "Regular  Aa", [.06,.115,.33,.055], { display: true, face: 2, max: .05, track: -.025, className: "family-sample" }),
        C("familyBlack", "Black  Aa", [.06,.175,.33,.055], { display: true, face: 3, max: .05, track: -.025, className: "family-sample" }),
        C("variable", "Variable", [.535,.075,.40,.16], { display: true, max: .14, track: -.04, className: "variable" }),
        C("glyphs", "glyphs", [.05,.31,.90,.29], { display: true, literal: true, max: .215, track: -.015, className: "glyph-strip" }),
        C("tileA", "Aa", [.05,.69,.19,.23], { display: true, max: .185, track: -.05, className: "tile tile-a" }),
        C("tileWord", "Shape", [.27,.69,.42,.23], { display: true, max: .18, track: -.04, className: "tile tile-word" }),
        C("tileAt", "@", [.72,.69,.23,.23], { display: true, max: .19, track: -.04, className: "tile tile-at" }),
      ],
    },
    ovalword32: {
      title: "Pearlescent Oval Wordmark", source: "T30332_00", contrast: ["#111016", "#fffdf9"],
      defaults: { kicker: "T&N Type Co.", headline: "Sadie", sub: "Display Sans", scale: 1 },
      controls: [{ key: "headline", label: "Oval Specimen", type: "text" }, { key: "scale", label: "Word Scale", min: .88, max: 1.08, step: .01 }],
      items: [
        C("kicker", "kicker", [.16,.13,.68,.075], { max: .052, track: .19, className: "kicker" }),
        C("headline", "headline", [.055,.262,.89,.43], { display: true, max: .245, track: -.01, className: "hero" }),
        C("sub", "sub", [.18,.72,.64,.075], { display: true, max: .048, track: .16, className: "sub" }),
      ],
    },
    stardust32: {
      title: "Stardust Editorial Poster", source: "T30332_01", contrast: ["#fffdf7", "#211d1d"],
      defaults: { eyebrow: "Type Studio", headline: "Dreams And\nStories", lineTwo: "Studio", footer: "In Good Company", scale: 1 },
      controls: [{ key: "headline", label: "Poster Headline", type: "textarea", rows: 2 }, { key: "lineTwo", label: "Closing Line", type: "text" }, { key: "scale", label: "Type Scale", min: .88, max: 1.08, step: .01 }],
      items: [
        C("eyebrow", "eyebrow", [.66,.09,.26,.055], { max: .034, track: .16, className: "eyebrow" }),
        C("headline", "headline", [.14,.255,.72,.33], { display: true, max: .29, track: -.035, className: "hero" }),
        C("lineTwo", "lineTwo", [.18,.595,.64,.14], { display: true, max: .115, track: -.035, className: "closing" }),
        C("footer", "footer", [.38,.82,.24,.055], { max: .038, track: .28, className: "footer" }),
      ],
    },
    blossom32: {
      title: "Blossom Wellness Landing Page", source: "T28576_08", contrast: ["#fffaf5", "#c90012"],
      defaults: { kicker: "A Retreat For The Senses", headline: "Bloom\nInto Calm", subhead: "Restore Your Natural Rhythm", body: "A Place To Rest And Reconnect.\nGentle Rituals Support Your Natural Rhythm.\nTime To Return To Yourself.", button: "Book A Visit", scale: 1 },
      controls: [{ key: "headline", label: "Main Message", type: "textarea", rows: 2 }, { key: "body", label: "Supporting Copy", type: "textarea", rows: 2 }, { key: "scale", label: "Display Scale", min: .9, max: 1.08, step: .01 }],
      items: [
        C("kicker", "kicker", [.065,.105,.50,.05], { max: .031, track: .13, className: "kicker" }),
        C("headline", "headline", [.055,.22,.53,.235], { display: true, max: .205, track: -.025, className: "hero" }),
        C("subhead", "subhead", [.065,.49,.49,.08], { max: .051, track: .035, className: "subhead" }),
        C("body", "body", [.065,.60,.49,.145], { max: .041, track: .015, className: "body" }),
        C("button", "button", [.16,.80,.31,.09], { max: .044, track: .13, className: "button" }),
      ],
    },
    neue32: {
      title: "Neue Repetition Poster", source: "T25441_04", contrast: ["#111018", "#f7b5c8"],
      defaults: { repeated: "Neue!", pillTop: "Instant", pillMid: "Type", pillBottom: "Form", scale: 1 },
      controls: [{ key: "repeated", label: "Repeated Word", type: "text" }, { key: "pillTop", label: "First Signal Pill", type: "text" }, { key: "pillMid", label: "Second Signal Pill", type: "text" }, { key: "pillBottom", label: "Third Signal Pill", type: "text" }, { key: "scale", label: "Word Scale", min: .9, max: 1.08, step: .01 }],
      items: [
        C("metaLeft", "Type Study / 01", [.06,.07,.35,.04], { max: .025, track: .08, className: "meta" }),
        C("metaRight", "Display Sans Design", [.68,.07,.26,.04], { max: .024, track: .06, className: "meta right" }),
        C("word1", "repeated", [.045,.155,.58,.24], { display: true, literal: true, max: .26, track: -.04, className: "repeat repeat-one" }),
        C("word2", "repeated", [.26,.39,.65,.25], { display: true, literal: true, max: .28, track: -.04, className: "repeat repeat-two" }),
        C("word3", "repeated", [.40,.62,.59,.28], { display: true, literal: true, max: .30, track: -.04, className: "repeat repeat-three" }),
        C("pillTop", "pillTop", [.54,.11,.39,.14], { max: .055, track: .03, className: "pill pill-top" }),
        C("pillMid", "pillMid", [.73,.435,.25,.12], { max: .047, track: .06, className: "pill pill-mid" }),
        C("pillBottom", "pillBottom", [.02,.69,.34,.145], { max: .05, track: .06, className: "pill pill-bottom" }),
        C("footer", "A Study In Geometric Form", [.06,.92,.43,.035], { max: .024, track: .06, className: "footer" }),
      ],
    },
    electromagnetic32: {
      title: "Electromagnetic Signal Poster", source: "T19827_01", contrast: ["#111018", "#eee9f1"],
      defaults: { kickerLeft: "Type Study / 03", kickerRight: "Frequency / Field", headline: "Electro\nMagnetic\nShady-01\nCourse-", footerLeft: "Noise / Light / Motion", footerRight: "Type / 03", scale: 1 },
      controls: [{ key: "headline", label: "Signal Stack", type: "textarea", rows: 4 }, { key: "scale", label: "Display Scale", min: .9, max: 1.08, step: .01 }],
      items: [
        C("kickerLeft", "kickerLeft", [.15,.10,.34,.05], { max: .03, track: .11, className: "kicker" }),
        C("kickerRight", "kickerRight", [.57,.10,.25,.05], { max: .028, track: .08, className: "kicker right" }),
        C("headline", "headline", [.155,.23,.70,.53], { display: true, max: .125, track: -.018, className: "hero" }),
        C("footerLeft", "footerLeft", [.15,.83,.48,.05], { max: .031, track: .10, className: "footer" }),
        C("footerRight", "footerRight", [.71,.83,.15,.05], { max: .03, track: .08, className: "footer right" }),
      ],
    },
  };

  function build(id) {
    const spec = definitions[id];
    const design = {
      id,
      title: spec.title,
      defaults: { ...spec.defaults },
      controls: spec.controls,
      render(board, state) {
        const props = state.props || state;
        board.replaceChildren();
        board.className = `source-board source-board--${id}`;
        if (id === "plakat32") appendPlakatSymbolBand(board);
        if (id === "weightfamily32") {
          board.dataset.familySampleCount = String(Math.max(2, Math.min(3, Number(props.familySampleCount) || 3)));
        }
        const items = [];
        let itemSpecs = spec.items.map((item) => ({ ...item, box: [...item.box] }));
        if (id === "neue32" && board.dataset.ratio === "1x1") {
          const squareBoxes = {
            pillTop: [.66,.12,.32,.13],
            word2: [.24,.39,.56,.25],
            pillMid: [.82,.435,.17,.12],
          };
          itemSpecs.forEach((item) => {
            if (squareBoxes[item.key]) item.box = squareBoxes[item.key];
          });
        }
        if (id === "plakat32") {
          itemSpecs = itemSpecs.filter((item) => item.key !== "glyphs");
        }
        if ((id === "weightfamily32" || id === "mangosboard32") && Number(props.familySampleCount) >= 2) {
          const count = Math.max(2, Math.min(3, Number(props.familySampleCount)));
          if (id === "weightfamily32") {
            const rows = ["row1", "row2", "row3"].slice(0, count);
            const labels = ["label1", "label2", "label3"].slice(0, count);
            itemSpecs = itemSpecs.filter((item) =>
              item.key.startsWith("row") ? rows.includes(item.key) :
                item.key.startsWith("label") ? labels.includes(item.key) : true);
            const ys = count === 2 ? [.10, .55] : [.085, .36, .66];
            const heights = count === 2 ? [.34, .34] : [.18, .18, .18];
            const lys = count === 2 ? [.235, .685] : [.115, .405, .72];
            itemSpecs.forEach((item) => {
              const rowIndex = rows.indexOf(item.key);
              const labelIndex = labels.indexOf(item.key);
              if (rowIndex >= 0) {
                item.box[1] = ys[rowIndex];
                item.box[3] = heights[rowIndex];
              }
              if (labelIndex >= 0) item.box[1] = lys[labelIndex];
            });
          } else {
            const keys = ["familyThin", "familyRegular", "familyBlack"].slice(0, count);
            itemSpecs = itemSpecs.filter((item) => !item.key.startsWith("family") || keys.includes(item.key));
            const ys = count === 2 ? [.075, .155] : [.055, .115, .175];
            itemSpecs.forEach((item) => {
              const index = keys.indexOf(item.key);
              if (index >= 0) item.box[1] = ys[index];
            });
          }
        }
        for (const item of itemSpecs) {
          const element = document.createElement("div");
          const customClasses = (item.className || "").split(/\s+/u).filter(Boolean)
            .map((name) => `source-item--${name}`).join(" ");
          element.className = `source-item source-item--${item.key} ${customClasses} ${item.className || ""}`;
          if (item.face && window.SupportFamilyAvailable?.includes(`SupportFamily${item.face}`)) {
            element.style.fontFamily = `SupportFamily${item.face}`;
          } else {
            element.style.fontFamily = "var(--display-face, Georgia, 'Times New Roman', serif)";
          }
          element.dataset.layoutItem = item.key;
          const box = item.box;
          Object.assign(element.style, { left: `${box[0] * 100}%`, top: `${box[1] * 100}%`, width: `${box[2] * 100}%`, height: `${box[3] * 100}%` });
          if (id === "plakat32" && item.key === "railOne") {
            const marker = Math.max(0.04, Math.min(0.96, Number(props.markerOne ?? .74)));
            element.style.setProperty("--rail-marker", `${marker * 100}%`);
          }
          if (id === "plakat32" && item.key === "railTwo") {
            const marker = Math.max(0.04, Math.min(0.96, Number(props.markerTwo ?? .08)));
            element.style.setProperty("--rail-marker", `${marker * 100}%`);
          }
          const raw = props[item.text] ?? state[item.text] ??
            props[item.key] ?? state[item.key] ?? item.text;
          const text = item.literal ? String(raw) : titleCase(raw);
          if (text.includes("\n")) {
            element.classList.add("source-item--multiline");
            element.style.flexDirection = "column";
            text.split("\n").forEach((line, index) => {
              const child = document.createElement("span");
              child.className = "source-item__line";
              child.dataset.layoutItem = `${item.key}-line-${index + 1}`;
              if (item.display) child.dataset.displayItem = "true";
              child.textContent = item.literal ? line : titleCase(line);
              element.append(child);
            });
          } else {
            if (item.display) element.dataset.displayItem = "true";
            element.textContent = text;
          }
          board.append(element);
          items.push({ element, item, text });
        }
        const scale = Number(props.scale ?? state.scale ?? 1);
        const displaySizes = [];
        for (const { element, item } of items) {
          const maxSize = board.clientHeight * (item.max || .08) *
            (item.display ? scale : 1);
          const lines = [...element.querySelectorAll(":scope > .source-item__line")];
          const fontSize = lines.length
            ? window.SupportLayout.fitLinesTogether(lines, {
              width: board.clientWidth * item.box[2] * .965,
              height: board.clientHeight * item.box[3] / lines.length * .84,
              maxSize,
              minSize: item.display ? 12 : 9,
              tracking: item.track || 0,
              inkAware: true,
            })
            : window.SupportLayout.fitLine(element, {
              width: board.clientWidth * item.box[2] * .965,
              height: board.clientHeight * item.box[3] * .88,
              maxSize,
              minSize: item.display ? 12 : 9,
              tracking: item.track || 0,
              inkAware: true,
            });
          if (lines.length) {
            lines.forEach((line) => { line.style.width = "100%"; });
          } else {
            element.style.width = `${item.box[2] * 100}%`;
          }
          if (item.display) displaySizes.push(fontSize);
        }
        design.headlineFontSize = `${Math.max(...displaySizes, 0)}px`;
        design.warnings = props.warnings || [];
      },
      getContrast() { return window.SupportLayout.contrast(...spec.contrast); },
      getWarnings() { return design.warnings || []; },
    };
    return design;
  }
  async function bindFamilyFiles(id) {
    for (let index = 1; index <= 3; index += 1) {
      const input = document.getElementById(`family-font-${index}`);
      if (!input) continue;
      input.addEventListener("change", async () => {
        const file = input.files?.[0];
        if (!file) return;
        const face = new FontFace(`SupportFamily${index}`, `url("${URL.createObjectURL(file)}")`);
        await face.load();
        document.fonts.add(face);
        window.SupportFamilyAvailable ||= [];
        if (!window.SupportFamilyAvailable.includes(`SupportFamily${index}`)) {
          window.SupportFamilyAvailable.push(`SupportFamily${index}`);
        }
        await document.fonts.ready;
        const style = titleCase(file.name.replace(/\.[^.]+$/u, "").replace(/[-_]+/gu, " "));
        const update = { familySampleCount: Math.max(Number(window.familySampleCount || 0), index) };
        if (id === "weightfamily32") update[`label${index}`] = style;
        if (id === "mangosboard32") {
          const keys = ["familyThin", "familyRegular", "familyBlack"];
          update[keys[index - 1]] = `${style}  Aa`;
        }
        window.configureTemplate(update);
        window.familySampleCount = Math.max(Number(window.familySampleCount || 0), index);
      });
    }
  }
  window.SourceLayoutDesign = { build, bindFamilyFiles };
})();
