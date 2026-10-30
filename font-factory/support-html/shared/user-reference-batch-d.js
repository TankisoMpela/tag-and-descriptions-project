(function () {
  const root = "../../../support-references/materials/reference-batch-2026-10-26-d/";
  function createScriptGrid() {
    const config = {
      title: "Script word grid specimen",
      words: ["Decline", "Courier", "Pianist", "Interim", "Actuals", "Fruited", "Decline", "Rolling"],
    };
    const design = {
      id: "scriptgrid32",
      title: config.title,
      literalKeys: ["familyName", "typeLabel", "creatorLabel", "formatLabel",
        ...config.words.map((_word, index) => `word${index + 1}`)],
      defaults: {
        familyName: "Font Family",
        typeLabel: "Type Specimen",
        creatorLabel: "Family Specimen",
        formatLabel: "OpenType",
        ...Object.fromEntries(config.words.map((word, index) => [`word${index + 1}`, word])),
        displayScale: 1,
      },
      controls: [
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        board.classList.add("user-reference-scriptgrid");
        board.replaceChildren();
        const scale = Number(state.displayScale ?? 1);
        const meta = [
          ["familyName", "sg-meta sg-meta-top-left"],
          ["typeLabel", "sg-meta sg-meta-top-right"],
          ["creatorLabel", "sg-meta sg-meta-bottom-left"],
          ["formatLabel", "sg-meta sg-meta-bottom-right"],
        ];
        for (const [key, className] of meta) {
          const item = document.createElement("div");
          item.className = className;
          item.textContent = String(state[key] || "");
          item.style.fontSize = `${Math.max(11, board.clientHeight * .019)}px`;
          item.dataset.layoutItem = `scriptgrid32-${key}`;
          board.append(item);
        }
        const words = [];
        config.words.forEach((_word, index) => {
          const row = Math.floor(index / 2);
          const col = index % 2;
          const item = document.createElement("div");
          item.className = "sg-word";
          item.style.left = col === 0 ? "12.5%" : "52.5%";
          item.style.top = `${12.5 + row * 18.2}%`;
          item.style.width = "35%";
          item.style.height = "14.5%";
          item.textContent = String(state[`word${index + 1}`] ?? config.words[index]);
          item.dataset.layoutItem = `scriptgrid32-word${index + 1}`;
          item.dataset.displayItem = "true";
          item.dataset.supportStackGroup = `scriptgrid-column-${col + 1}`;
          item.dataset.supportStackIndex = String(row);
          board.append(item);
          words.push(item);
        });
        window.SupportLayout.fitLinesTogether(words, {
          width: board.clientWidth * .32,
          height: board.clientHeight * .13,
          maxSize: board.clientHeight * .142 * scale,
          minSize: 38,
          tracking: -.025,
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#fbf8ff", "#2935b8");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createSmashCourt() {
    const config = {
      title: "Smash Court poster specimen",
      lines: ["“Smash Court", "Elevate Your", "Potential”"],
      rightCaption: "MASTER THE\nCOURT\nOWN THE\nMATCH",
      footerCaption: "UNLEASH YOUR\nPOTENTIAL ON THE COURT\nELEVATE YOUR GAME",
    };
    const design = {
      id: "smashcourt32",
      title: config.title,
      literalKeys: ["lineOne", "lineTwo", "lineThree", "rightCaption", "footerCaption"],
      defaults: {
        lineOne: config.lines[0],
        lineTwo: config.lines[1],
        lineThree: config.lines[2],
        rightCaption: config.rightCaption,
        footerCaption: config.footerCaption,
        displayScale: 1,
      },
      controls: [
        { key: "lineOne", type: "text", label: "Title line one" },
        { key: "lineTwo", type: "text", label: "Title line two" },
        { key: "lineThree", type: "text", label: "Title line three" },
        { key: "rightCaption", type: "textarea", rows: 4, label: "Right caption" },
        { key: "footerCaption", type: "textarea", rows: 3, label: "Lower-left caption" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-smashcourt");
        board.replaceChildren();

        const plate = document.createElement("img");
        plate.className = "sc-plate";
        plate.dataset.layoutItem = "smashcourt32-photo-plate";
        plate.src = `${root}smashcourt32-photo-${square ? "square" : "3x2"}.png`;
        plate.alt = "";
        plate.draggable = false;
        board.append(plate);

        const lines = [
          ["lineOne", "sc-line sc-line-one"],
          ["lineTwo", "sc-line sc-line-two"],
          ["lineThree", "sc-line sc-line-three"],
        ];
        const elements = [];
        for (const [key, className] of lines) {
          const item = document.createElement("div");
          item.className = className;
          item.textContent = String(state[key] ?? config.lines[lines.findIndex(([name]) => name === key)]);
          item.dataset.layoutItem = `smashcourt32-${key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          elements.push(item);
        }

        const rightCaption = document.createElement("div");
        rightCaption.className = "sc-caption sc-right-caption";
        rightCaption.textContent = String(state.rightCaption ?? config.rightCaption);
        rightCaption.dataset.layoutItem = "smashcourt32-right-caption";
        board.append(rightCaption);

        const footerCaption = document.createElement("div");
        footerCaption.className = "sc-caption sc-footer-caption";
        footerCaption.textContent = String(state.footerCaption ?? config.footerCaption);
        footerCaption.dataset.layoutItem = "smashcourt32-footer-caption";
        board.append(footerCaption);

        const rowWidths = square ? [.92, .94, .82] : [.78, .76, .68];
        const fontHeight = square ? .177 : .205;
        elements.forEach((item, index) => {
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * rowWidths[index],
            height: board.clientHeight * fontHeight,
            maxSize: board.clientHeight * (square ? .17 : .19) * scale,
            minSize: 38,
            tracking: -.035,
          });
        });
        for (const item of [rightCaption, footerCaption]) {
          item.style.fontSize = `${Math.max(11, board.clientHeight * .015)}px`;
        }
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f7f5f0", "#18312f"),
          window.SupportLayout.contrast("#f7f5f0", "#17263d"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createScriptPattern() {
    const config = {
      title: "Script on paper specimen",
      words: ["Everyday", "Time", "Sometimes", "Moon", "Sunday"],
    };
    const design = {
      id: "scriptpattern32",
      title: config.title,
      literalKeys: config.words.map((_word, index) => `word${index + 1}`),
      defaults: {
        ...Object.fromEntries(config.words.map((word, index) => [`word${index + 1}`, word])),
        displayScale: 1,
      },
      controls: [
        ...config.words.map((word, index) => ({
          key: `word${index + 1}`,
          type: "text",
          label: `Script specimen ${index + 1}`,
          value: word,
        })),
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        const placements = square
          ? [
              [1, -12, -12, 60, 26, -13],
              [4, 50, -4, 59, 24, -12],
              [0, -15, 12, 75, 27, -14],
              [1, 52, 23, 55, 23, -11],
              [2, -10, 38, 74, 27, -13],
              [3, 61, 47, 50, 22, -11],
              [4, -10, 66, 68, 25, -12],
              [0, 44, 79, 67, 25, -14],
            ]
          : [
              [1, -12, -14, 53, 28, -13],
              [4, 62, -8, 50, 24, -12],
              [0, -14, 9, 70, 29, -14],
              [1, 63, 20, 42, 23, -11],
              [2, -18, 34, 72, 28, -13],
              [3, 67, 41, 44, 23, -11],
              [4, -11, 63, 65, 28, -12],
              [0, 51, 76, 68, 27, -14],
            ];
        board.classList.add("user-reference-scriptpattern");
        board.replaceChildren();

        const plate = document.createElement("img");
        plate.className = "sp-plate";
        plate.dataset.layoutItem = "scriptpattern32-paper-plate";
        plate.src = `${root}T19363_09-paper-${square ? "square" : "3x2"}.png`;
        plate.alt = "";
        plate.draggable = false;
        board.append(plate);

        const pattern = document.createElement("div");
        pattern.className = "sp-pattern";
        pattern.dataset.layoutItem = "scriptpattern32-pattern";
        pattern.dataset.displayItem = "true";
        board.append(pattern);

        placements.forEach(([wordIndex, left, top, width, height, angle], index) => {
          const item = document.createElement("div");
          const word = config.words[wordIndex];
          item.className = `sp-word sp-word-${index + 1}`;
          item.style.left = `${left}%`;
          item.style.top = `${top}%`;
          item.style.width = `${width}%`;
          item.style.height = `${height}%`;
          item.style.setProperty("--sp-angle", `${angle}deg`);
          item.textContent = String(state[`word${wordIndex + 1}`] ?? word);
          pattern.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * width / 100,
            height: board.clientHeight * height / 100,
            maxSize: board.clientHeight * (square ? .34 : .36) * scale,
            minSize: 38,
            tracking: -.045,
          });
        });
        pattern.style.fontSize = `${Math.max(...[...pattern.children].map((item) =>
          Number.parseFloat(item.style.fontSize) || 0))}px`;
      },
      getContrast() {
        return window.SupportLayout.contrast("#5a5652", "#eeeae1");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createBrushPanel() {
    const config = {
      title: "Brush lettering panel specimen",
      topWordOne: "Orchid",
      topWordTwo: "North",
      topCaption: "DESIGN",
      repeatWord: "#FRESH +",
      beliefWord: "Believe",
      connector: "TO",
      achievement: "Achieve",
      bottomWord: "Vivid",
      bottomCaption: "BOUTIQUE",
    };
    const fields = [
      ["topWordOne", "Top-left first line"],
      ["topWordTwo", "Top-left second line"],
      ["topCaption", "Top-left caption"],
      ["repeatWord", "Mint-panel word"],
      ["beliefWord", "Lower-left first line"],
      ["connector", "Lower-left connector"],
      ["achievement", "Lower-left second line"],
      ["bottomWord", "Lower-right first line"],
      ["bottomCaption", "Lower-right caption"],
    ];
    const groups = [
      {
        id: "orchid",
        className: "bp-panel-orchid",
        items: [
          ["topWordOne", "bp-type bp-orchid", [6, 8, 88, 37], .40, -.035],
          ["topWordTwo", "bp-type bp-north", [17, 37, 77, 37], .40, -.035],
          ["topCaption", "bp-type bp-design", [29, 76, 49, 15], .18, .12],
        ],
      },
      {
        id: "fresh",
        className: "bp-panel-fresh",
        items: [
          ["repeatWord", "bp-type bp-fresh-row bp-fresh-ink", [-26, -18, 152, 29], .31, -.045, 2],
          ["repeatWord", "bp-type bp-fresh-row bp-fresh-paper", [-8, 7, 152, 29], .31, -.045, 2],
          ["repeatWord", "bp-type bp-fresh-row bp-fresh-ink", [-30, 33, 152, 29], .31, -.045, 2],
          ["repeatWord", "bp-type bp-fresh-row bp-fresh-paper", [-9, 59, 152, 29], .31, -.045, 2],
        ],
      },
      {
        id: "believe",
        className: "bp-panel-believe",
        items: [
          ["beliefWord", "bp-type bp-belief", [7, 8, 87, 38], .42, -.04],
          ["connector", "bp-type bp-connector", [3, 48, 25, 25], .30, -.02],
          ["achievement", "bp-type bp-achieve", [30, 48, 67, 42], .42, -.04],
        ],
      },
      {
        id: "vivid",
        className: "bp-panel-vivid",
        items: [
          ["bottomWord", "bp-type bp-vivid", [5, 9, 90, 57], .58, -.04],
          ["bottomCaption", "bp-type bp-boutique", [26, 63, 69, 26], .30, .04],
        ],
      },
    ];
    const design = {
      id: "brushpanel32",
      title: config.title,
      literalKeys: fields.map(([key]) => key),
      defaults: {
        ...Object.fromEntries(fields.map(([key]) => [key, config[key]])),
        displayScale: 1,
      },
      controls: [
        ...fields.map(([key, label]) => ({ key, type: "text", label })),
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 1.3,
        rationale: "Large white source lettering sits on blush and mint, with pink display copy over white; dark inline strokes and offset shadows define each edge.",
      },
      warnings: [],
      render(board, state) {
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-brushpanel");
        board.replaceChildren();
        groups.forEach((group) => {
          const panel = document.createElement("div");
          panel.className = `bp-panel ${group.className}`;
          panel.dataset.panelId = group.id;
          board.append(panel);
          group.items.forEach(([key, className, box, maxHeight, tracking, repeatCount = 1], index) => {
            const item = document.createElement("div");
            const [left, top, width, height] = box;
            item.className = className;
            item.style.left = `${left}%`;
            item.style.top = `${top}%`;
            item.style.width = `${width}%`;
            item.style.height = `${height}%`;
            const text = String(state[key] ?? config[key]);
            item.textContent = repeatCount > 1 ? Array(repeatCount).fill(text).join("   ") : text;
            if (group.id !== "fresh") {
              item.dataset.layoutItem = `brushpanel32-${group.id}-${key}-${index + 1}`;
              item.dataset.displayItem = "true";
            }
            if (group.id === "fresh") item.style.fontSize = `${panel.clientHeight * maxHeight * scale}px`;
            panel.append(item);
            if (group.id !== "fresh") {
              window.SupportLayout.fitLine(item, {
                width: panel.clientWidth * width / 100,
                height: panel.clientHeight * height / 100,
                maxSize: panel.clientHeight * maxHeight * scale,
                minSize: 20,
                tracking,
              });
            }
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#191719", "#f2d4d7"),
          window.SupportLayout.contrast("#ffffff", "#f2d4d7"),
          window.SupportLayout.contrast("#191719", "#9fe8db"),
          window.SupportLayout.contrast("#ffffff", "#9fe8db"),
          window.SupportLayout.contrast("#e4417f", "#f8f8f8"),
          window.SupportLayout.contrast("#ffffff", "#262628"),
          window.SupportLayout.contrast("#eb2ca8", "#262628"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createAvalonBrush() {
    const config = { title: "Avalon brush word specimen", mainWord: "Avalon" };
    const design = {
      id: "avalonbrush32",
      title: config.title,
      literalKeys: ["mainWord"],
      defaults: { mainWord: config.mainWord, displayScale: 1 },
      controls: [
        { key: "mainWord", type: "text", label: "Featured word" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const scale = Number(state.displayScale ?? 1);
        const mainWord = String(state.mainWord ?? config.mainWord);
        const square = board.dataset.ratio === "1x1";
        board.classList.add("user-reference-avalonbrush");
        board.replaceChildren();

        const pattern = document.createElement("div");
        pattern.className = "av-pattern";
        pattern.setAttribute("aria-hidden", "true");
        board.append(pattern);
        const rowCount = square ? 10 : 9;
        for (let index = 0; index < rowCount; index += 1) {
          const row = document.createElement("div");
          row.className = "av-pattern-row";
          row.style.top = `${index * 10}%`;
          row.style.left = `${index % 2 ? -23 : -7}%`;
          row.style.fontSize = `${board.clientHeight * .19 * scale}px`;
          row.textContent = Array(7).fill(mainWord).join("   ");
          pattern.append(row);
        }

        const addMainText = (key, className, text, box, maxSize, minSize = 20, tracking = -.025) => {
          const item = document.createElement("div");
          const [left, top, width, height] = box;
          item.className = className;
          item.style.left = `${left}%`;
          item.style.top = `${top}%`;
          item.style.width = `${width}%`;
          item.style.height = `${height}%`;
          item.textContent = text;
          item.dataset.layoutItem = `avalonbrush32-${key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * width / 100,
            height: board.clientHeight * height / 100,
            maxSize: board.clientHeight * maxSize * scale,
            minSize,
            tracking,
          });
          return item;
        };

        addMainText(
          "featured-word",
          "av-main",
          mainWord,
          square ? [5, 24, 88, 52] : [5, 23, 88, 54],
          .56,
          24,
          -.035,
        );

        const badge = document.createElement("div");
        const badgeSize = board.clientHeight * .20;
        badge.className = "av-badge";
        badge.textContent = "SVG\nFONT";
        badge.style.left = `${board.clientWidth * (square ? .69 : .70)}px`;
        badge.style.top = `${board.clientHeight * .62}px`;
        badge.style.width = `${badgeSize}px`;
        badge.style.height = `${badgeSize}px`;
        badge.dataset.layoutItem = "avalonbrush32-font-specimen-badge";
        badge.dataset.displayItem = "true";
        board.append(badge);
        window.SupportLayout.fitLine(badge, {
          width: badgeSize * .78,
          height: badgeSize * .58,
          maxSize: board.clientHeight * .047 * scale,
          minSize: 12,
          tracking: .02,
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#171717", "#fbfaf8"),
          window.SupportLayout.contrast("#d01875", "#f7f7f5"),
          window.SupportLayout.contrast("#ffffff", "#006b56"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createSsRange() {
    const config = {
      title: "S/S Range fashion lettering specimen",
      lineOne: "S/S_RANGE",
      lineTwo: "NEW_vogue",
    };
    const design = {
      id: "ssrange32",
      title: config.title,
      literalKeys: ["lineOne", "lineTwo"],
      defaults: { lineOne: config.lineOne, lineTwo: config.lineTwo, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "Upper lettering" },
        { key: "lineTwo", type: "text", label: "Lower lettering" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-ssrange");
        board.replaceChildren();

        const plate = document.createElement("img");
        plate.className = "ssr-plate";
        plate.dataset.layoutItem = "ssrange32-photo-plate";
        plate.src = `${root}T32952_09-background-${square ? "square" : "3x2"}.png`;
        plate.alt = "";
        plate.draggable = false;
        board.append(plate);

        const lines = [
          ["lineOne", "ssr-line ssr-line-one"],
          ["lineTwo", "ssr-line ssr-line-two"],
        ];
        const boxes = square
          ? [[5, 31, 90, 23], [4, 52, 92, 25]]
          : [[7, 31, 86, 23], [6, 52, 88, 25]];
        const widths = square ? [.86, .88] : [.82, .84];
        lines.forEach(([key, className], index) => {
          const item = document.createElement("div");
          const [left, top, width, height] = boxes[index];
          item.className = className;
          item.style.left = `${left}%`;
          item.style.top = `${top}%`;
          item.style.width = `${width}%`;
          item.style.height = `${height}%`;
          item.textContent = String(state[key] ?? config[key]);
          item.dataset.layoutItem = `ssrange32-${key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * widths[index],
            height: board.clientHeight * (square ? .21 : .20),
            maxSize: board.clientHeight * (square ? .205 : .21) * scale,
            minSize: 38,
            tracking: -.035,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f4ef00", "#171512"),
          window.SupportLayout.contrast("#f4ef00", "#51463e"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createAllSummerLong() {
    const config = {
      title: "All Summer Long photo specimen",
      lineOne: "ALL",
      lineTwo: "Summer",
      lineThree: "Long",
      familyLabel: "Family Name",
    };
    const design = {
      id: "allsummerlong32",
      title: config.title,
      literalKeys: ["lineOne", "lineTwo", "lineThree", "familyLabel"],
      defaults: {
        lineOne: config.lineOne,
        lineTwo: config.lineTwo,
        lineThree: config.lineThree,
        familyLabel: config.familyLabel,
        displayScale: 1,
      },
      controls: [
        { key: "lineOne", type: "text", label: "Upper word" },
        { key: "lineTwo", type: "text", label: "Middle word" },
        { key: "lineThree", type: "text", label: "Lower word" },
        { key: "familyLabel", type: "text", label: "Corner signature" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 1.6,
        rationale: "Large source-matched pink lettering crosses both dark foliage and pale clothing; a dark text stroke and offset shadow keep its edges readable across the photographs.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-allsummerlong");
        board.replaceChildren();

        const cards = square
          ? [
              { left: -71, width: 78, height: 78, top: 11 },
              { left: 11, width: 78, height: 78, top: 11 },
              { left: 93, width: 78, height: 78, top: 11 },
            ]
          : [
              { left: -34, width: 52, height: 77.5, top: 11 },
              { left: 24, width: 52, height: 77.5, top: 11 },
              { left: 82, width: 52, height: 77.5, top: 11 },
            ];
        const lineSpecs = [
          ["lineOne", "asl-line asl-line-one", [19, 7, 62, 28], .27],
          ["lineTwo", "asl-line asl-line-two", [6, 35, 88, 28], .26],
          ["lineThree", "asl-line asl-line-three", [25, 64, 50, 29], .27],
        ];
        const photoUrl = `${root}T35520_06-main-photo-square.png`;

        cards.forEach((cardSpec, cardIndex) => {
          const card = document.createElement("div");
          card.className = "asl-card";
          card.style.left = `${cardSpec.left}%`;
          card.style.top = `${cardSpec.top}%`;
          card.style.width = `${cardSpec.width}%`;
          card.style.height = `${cardSpec.height}%`;
          card.dataset.panelId = `photo-copy-${cardIndex + 1}`;
          board.append(card);

          const photo = document.createElement("img");
          photo.className = "asl-card-photo";
          photo.src = photoUrl;
          photo.alt = "";
          photo.draggable = false;
          if (cardIndex === 1) photo.dataset.layoutItem = "allsummerlong32-photo-card";
          card.append(photo);

          const label = document.createElement("div");
          label.className = "asl-family-label";
          label.style.left = "8%";
          label.style.top = "6%";
          label.style.width = "22%";
          label.style.height = "8%";
          label.textContent = String(state.familyLabel ?? config.familyLabel);
          if (cardIndex === 1) label.dataset.layoutItem = "allsummerlong32-family-label";
          card.append(label);
          window.SupportLayout.fitLine(label, {
            width: card.clientWidth * .22,
            height: card.clientHeight * .08,
            maxSize: card.clientHeight * .026 * scale,
            minSize: 12,
            tracking: .01,
          });

          lineSpecs.forEach(([key, className, box, maxHeight], index) => {
            const item = document.createElement("div");
            const [left, top, width, height] = box;
            item.className = className;
            item.style.left = `${left}%`;
            item.style.top = `${top}%`;
            item.style.width = `${width}%`;
            item.style.height = `${height}%`;
            item.textContent = String(state[key] ?? config[key]);
            if (cardIndex === 1) {
              item.dataset.layoutItem = `allsummerlong32-${key}`;
              item.dataset.displayItem = "true";
            }
            card.append(item);
            window.SupportLayout.fitLine(item, {
              width: card.clientWidth * width / 100,
              height: card.clientHeight * height / 100,
              maxSize: card.clientHeight * maxHeight * scale,
              minSize: 38,
              tracking: -.03,
            });
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f43b6a", "#1e2a1c"),
          window.SupportLayout.contrast("#f43b6a", "#b8aa96"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  const config = {
    title: "Retro Space Print specimen",
    source: "E9653_03",
    topWord: "HOLO",
    year: "2023",
  };

  window.UserReferenceBatchD = {
    ids: ["spaceprint32", "scriptgrid32", "smashcourt32", "scriptpattern32", "brushpanel32", "avalonbrush32", "ssrange32", "allsummerlong32"],
    create(id) {
      if (id === "scriptgrid32") return createScriptGrid();
      if (id === "smashcourt32") return createSmashCourt();
      if (id === "scriptpattern32") return createScriptPattern();
      if (id === "brushpanel32") return createBrushPanel();
      if (id === "avalonbrush32") return createAvalonBrush();
      if (id === "ssrange32") return createSsRange();
      if (id === "allsummerlong32") return createAllSummerLong();
      if (id !== "spaceprint32") throw new Error(`Unknown reference template: ${id}`);
      const design = {
        id,
        title: config.title,
        literalKeys: ["topWord", "year"],
        defaults: {
          topWord: config.topWord,
          year: config.year,
          displayScale: 1,
        },
        controls: [
          { key: "topWord", type: "text", label: "Top panel lettering" },
          { key: "year", type: "text", label: "Year / selected-font numerals" },
          { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
        ],
        warnings: [],
        render(board, state) {
          const ratio = board.dataset.ratio === "1x1" ? "square" : "3x2";
          const scale = Number(state.displayScale ?? 1);
          board.classList.add("user-reference-spaceprint");
          board.replaceChildren();

          const plate = document.createElement("img");
          plate.className = "spc-plate";
          plate.dataset.layoutItem = "spaceprint32-artwork-plate";
          plate.src = `${root}spaceprint32-plate-${ratio}.png`;
          plate.alt = "";
          plate.draggable = false;
          board.append(plate);

          const topWord = document.createElement("div");
          topWord.className = "spc-type spc-word";
          topWord.dataset.layoutItem = "spaceprint32-topWord";
          topWord.dataset.displayItem = "true";
          topWord.textContent = String(state.topWord ?? config.topWord);
          board.append(topWord);

          const year = document.createElement("div");
          year.className = "spc-type spc-year";
          year.dataset.layoutItem = "spaceprint32-year";
          year.dataset.displayItem = "true";
          year.textContent = String(state.year ?? config.year);
          board.append(year);

          window.SupportLayout.fitLine(topWord, {
            width: board.clientWidth * .145,
            height: board.clientHeight * .155,
            maxSize: board.clientHeight * .105 * scale,
            minSize: 38,
            tracking: -.035,
          });
          window.SupportLayout.fitLine(year, {
            width: board.clientWidth * .425,
            height: board.clientHeight * .205,
            maxSize: board.clientHeight * .235 * scale,
            minSize: 38,
            tracking: -.045,
          });
        },
        getContrast() {
          return Math.min(
            window.SupportLayout.contrast("#39205c", "#ff9800"),
            window.SupportLayout.contrast("#fff0cb", "#005359"),
            window.SupportLayout.contrast("#fff0cb", "#632f91"),
          );
        },
        getWarnings() {
          return design.warnings;
        },
      };
      return design;
    },
  };
})();
