(function () {
  const config = {
    title: "Pretty in Pink poster specimen",
    lineOne: "Pretty",
    lineTwo: "in Pink!",
  };

  const svgNode = (tag, attrs) => {
    const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
    for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
    return node;
  };

  function createPrettyInPink() {
    const design = {
      id: "prettyinpink32",
      title: config.title,
      literalKeys: ["lineOne", "lineTwo"],
      defaults: { lineOne: config.lineOne, lineTwo: config.lineTwo, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "Upper lettering" },
        { key: "lineTwo", type: "text", label: "Lower lettering" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 1.5,
        rationale: "The source uses hot-pink display lettering with a thick white edge across a black panel and its bright yellow border field.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-prettyinpink");
        board.classList.toggle("prettyinpink-square", square);
        board.replaceChildren();

        const confetti = svgNode("svg", {
          class: "pip-confetti",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "xMidYMid slice",
          "aria-hidden": "true",
        });
        const marks = [
          ["path", { d: "M335 -18h61v37h-28v24h-27v31h-45v-31h25v-26h14z", fill: "#11110f" }],
          ["circle", { cx: 774, cy: 0, r: 30, fill: "#04b9a8" }],
          ["rect", { x: 1135, y: 42, width: 48, height: 48, fill: "#28242d", transform: "rotate(-12 1159 66)" }],
          ["path", { d: "M1408 -8h192v23h-192z", fill: "#f52870", transform: "rotate(18 1504 3)" }],
          ["path", { d: "M-24 156l142 31-9 30-141-31z", fill: "#11110f" }],
          ["rect", { x: -10, y: 526, width: 18, height: 82, fill: "#04b9a8" }],
          ["path", { d: "M1758 468h34v-20h33v-21h35v26h-38v21h-34v19h-30z", fill: "#f52870" }],
          ["path", { d: "M1710 699h105v24h-105z", fill: "#04b9a8", transform: "rotate(-13 1762 711)" }],
          ["path", { d: "M-17 904h136v22H-17z", fill: "#f52870", transform: "rotate(-16 51 915)" }],
          ["rect", { x: 91, y: 1102, width: 57, height: 54, fill: "#28242d", transform: "rotate(20 119 1129)" }],
          ["path", { d: "M573 1121h37v31h38v28h34v29h-39v-27h-39v-29h-31z", fill: "#04b9a8" }],
          ["circle", { cx: 1103, cy: 1171, r: 31, fill: "#f52870" }],
          ["path", { d: "M1277 1162h204v25h-204z", fill: "#11110f", transform: "rotate(-13 1379 1174)" }],
          ["path", { d: "M1696 1068l48 78h-96z", fill: "#11110f" }],
        ];
        for (const [tag, attrs] of marks) confetti.append(svgNode(tag, attrs));
        board.append(confetti);

        const frame = document.createElement("div");
        frame.className = "pip-frame";
        frame.dataset.layoutItem = "prettyinpink32-white-frame";
        board.append(frame);

        const panel = document.createElement("div");
        panel.className = "pip-panel";
        panel.dataset.layoutItem = "prettyinpink32-black-panel";
        board.append(panel);

        const panelMarks = svgNode("svg", {
          class: "pip-panel-marks",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        [
          ["path", { d: "M802 270l49 8-25 28z" }],
          ["path", { d: "M1280 259l48 8-24 27z" }],
          ["path", { d: "M423 429l43 9-23 27z" }],
          ["rect", { x: 633, y: 354, width: 33, height: 33 }],
          ["rect", { x: 910, y: 942, width: 37, height: 34 }],
          ["rect", { x: 1414, y: 181, width: 37, height: 33 }],
          ["path", { d: "M1297 766l43 6-23 31z" }],
          ["path", { d: "M485 822l42 6-24 34z" }],
          ["circle", { cx: 726, cy: 468, r: 13 }],
          ["circle", { cx: 1095, cy: 880, r: 11 }],
        ].forEach(([tag, attrs]) => panelMarks.append(svgNode(tag, attrs)));
        panel.append(panelMarks);

        const lines = [
          ["lineOne", "pip-title pip-title-one"],
          ["lineTwo", "pip-title pip-title-two"],
        ];
        const boxes = square
          ? [
              { left: 7, top: 15, width: 86, height: 32, max: .31 },
              { left: 4, top: 48, width: 92, height: 37, max: .32 },
            ]
          : [
              { left: 9, top: 8, width: 82, height: 38, max: .37 },
              { left: 8, top: 45, width: 85, height: 42, max: .39 },
            ];
        lines.forEach(([key, className], index) => {
          const item = document.createElement("div");
          const spec = boxes[index];
          item.className = className;
          item.style.left = `${spec.left}%`;
          item.style.top = `${spec.top}%`;
          item.style.width = `${spec.width}%`;
          item.style.height = `${spec.height}%`;
          item.textContent = String(state[key] ?? config[key]);
          item.dataset.layoutItem = `prettyinpink32-${key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * spec.width / 100,
            height: board.clientHeight * spec.height / 100,
            maxSize: board.clientHeight * spec.max * scale,
            minSize: 38,
            tracking: -.035,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f52870", "#0b0d0a"),
          window.SupportLayout.contrast("#ffffff", "#0b0d0a"),
          window.SupportLayout.contrast("#f52870", "#ffe35b"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createDynamicPlayful() {
    const defaults = { lineOne: "dynamic", lineTwo: "playful" };
    const squiggles = [
      "M-8 35c44-66 96 64 150-8s95 64 147-5",
      "M1500 37c42 60 93-59 140 1s91-57 149 10",
      "M-20 710c49-78 60 53 100-7s60 53 100-9",
      "M1710 643c33 67 59-65 92-4s59-61 93 5",
      "M671 198c25 44 63-40 98 1s64-39 103 5",
      "M965 1117c30-47 70 41 102-2s64 39 103-5",
    ];
    const svgNode = (tag, attrs) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    };

    const design = {
      id: "dynamicplayful32",
      title: "Dynamic Playful retro-script specimen",
      literalKeys: ["lineOne", "lineTwo"],
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "Upper lettering" },
        { key: "lineTwo", type: "text", label: "Lower lettering" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 2.1,
        rationale: "The source's yellow lettering sits directly on saturated teal, with a hard black offset shadow as part of the retro print treatment.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-dynamicplayful");
        board.classList.toggle("dynamicplayful-square", square);
        board.replaceChildren();

        const field = document.createElement("div");
        field.className = "dyp-field";
        field.setAttribute("aria-hidden", "true");
        board.append(field);

        const waves = svgNode("svg", {
          class: "dyp-squiggles",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        squiggles.forEach((d) => waves.append(svgNode("path", { d, class: "dyp-wave-shadow" })));
        squiggles.forEach((d) => waves.append(svgNode("path", { d, class: "dyp-wave-hot" })));
        board.append(waves);

        const labels = [
          ["RADICAL", "dyp-label dyp-label-top-left"],
          ["RETRO SCRIPT SPECIMEN", "dyp-label dyp-label-top-right"],
          ["EXPRESSIVE LETTERFORMS", "dyp-label dyp-label-bottom-left"],
          ["TYPE STUDY · 02", "dyp-label dyp-label-bottom-right"],
        ];
        labels.forEach(([text, className]) => {
          const label = document.createElement("span");
          label.className = className;
          label.textContent = text;
          board.append(label);
        });

        const boxes = square
          ? [
              { left: 3, top: 22, width: 94, height: 34, max: .405 },
              { left: 3, top: 49, width: 94, height: 33, max: .405 },
            ]
          : [
              { left: 7, top: 17, width: 86, height: 40, max: .435 },
              { left: 7, top: 47, width: 86, height: 40, max: .435 },
            ];
        const items = [];
        ["lineOne", "lineTwo"].forEach((key, index) => {
          const spec = boxes[index];
          const item = document.createElement("div");
          item.className = `dyp-title dyp-title-${index + 1}`;
          item.style.left = `${spec.left}%`;
          item.style.top = `${spec.top}%`;
          item.style.width = `${spec.width}%`;
          item.style.height = `${spec.height}%`;
          item.textContent = String(state[key] ?? defaults[key]);
          item.dataset.layoutItem = `dynamicplayful32-${key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          items.push(item);
        });
        window.SupportLayout.fitLinesTogether(items, {
          width: board.clientWidth * Math.min(...boxes.map((box) => box.width)) / 100,
          height: board.clientHeight * Math.min(...boxes.map((box) => box.height)) / 100,
          maxSize: board.clientHeight * Math.min(...boxes.map((box) => box.max)) * scale,
          minSize: 38,
          tracking: -.005,
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#ffec65", "#00977e");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createRetroShowcase() {
    const defaults = {
      topTitle: "The Golden Girls",
      middleTitle: "Full House",
      bottomTitle: "Sledge Hammer!",
    };
    const shapes = [
      ["rect", { x: 76, y: 18, width: 34, height: 36, fill: "#e83a76" }],
      ["path", { d: "M342 15l29 2-14 34z", fill: "#00a991" }],
      ["rect", { x: 601, y: 16, width: 32, height: 34, fill: "#f8dd51" }],
      ["rect", { x: 1419, y: 23, width: 35, height: 33, fill: "#e83a76" }],
      ["path", { d: "M1664 15l35 8-27 31z", fill: "#00a991" }],
      ["rect", { x: 0, y: 476, width: 29, height: 31, fill: "#f8dd51" }],
      ["path", { d: "M178 637l36 9-26 31z", fill: "#00a991" }],
      ["rect", { x: 308, y: 492, width: 28, height: 30, fill: "#e83a76" }],
      ["path", { d: "M1710 508l37 5-23 31z", fill: "#00a991" }],
      ["rect", { x: 1716, y: 1128, width: 30, height: 32, fill: "#f8dd51" }],
      ["path", { d: "M1740 885l36-4-13 38z", fill: "#00a991" }],
      ["rect", { x: 70, y: 1161, width: 30, height: 29, fill: "#e83a76" }],
      ["path", { d: "M1670 1159l34-8-11 39z", fill: "#00a991" }],
      ["rect", { x: 1155, y: 17, width: 26, height: 32, fill: "#00a991" }],
    ];
    const bands = [
      { key: "topTitle", tone: "yellow", left: 5, top: 4, width: 90, height: 29, max: .255, angle: -1.6 },
      { key: "middleTitle", tone: "pink", left: 20, top: 34, width: 77, height: 31, max: .27, angle: -2.1 },
      { key: "bottomTitle", tone: "teal", left: 4, top: 64, width: 92, height: 29, max: .255, angle: -.6 },
    ];
    const svgNode = (tag, attrs) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    };
    const design = {
      id: "retroshowcase32",
      title: "Retro television titles panel specimen",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "topTitle", type: "text", label: "Top lettering" },
        { key: "middleTitle", type: "text", label: "Middle lettering" },
        { key: "bottomTitle", type: "text", label: "Lower lettering" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 1.4,
        rationale: "The original's pink display lettering crosses teal and yellow cut-paper bands as one source-matched three-color print palette.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-retroshowcase");
        board.classList.toggle("retroshowcase-square", square);
        board.replaceChildren();

        const paper = document.createElement("div");
        paper.className = "rts-paper";
        paper.setAttribute("aria-hidden", "true");
        board.append(paper);
        const confetti = svgNode("svg", {
          class: "rts-confetti",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        shapes.forEach(([tag, attrs]) => {
          confetti.append(svgNode(tag, { ...attrs, fill: "#10100f", transform: "translate(7 7)" }));
        });
        shapes.forEach(([tag, attrs]) => confetti.append(svgNode(tag, attrs)));
        board.append(confetti);

        bands.forEach((band) => {
          const layout = square
            ? {
                topTitle: { left: 3, top: 6, width: 94, height: 27, max: .25, angle: -1 },
                middleTitle: { left: 10, top: 36, width: 84, height: 27, max: .255, angle: -1.1 },
                bottomTitle: { left: 3, top: 66, width: 94, height: 25, max: .245, angle: -.4 },
              }[band.key]
            : band;
          const shadow = document.createElement("div");
          shadow.className = `rts-band-shadow rts-band-${band.tone}`;
          shadow.style.left = `${layout.left}%`;
          shadow.style.top = `${layout.top}%`;
          shadow.style.width = `${layout.width}%`;
          shadow.style.height = `${layout.height}%`;
          shadow.style.transform = `rotate(${layout.angle}deg) translate(.45%, 1.3%)`;
          shadow.dataset.layoutItem = `retroshowcase32-${band.key}-shadow`;
          board.append(shadow);

          const panel = document.createElement("div");
          panel.className = `rts-band rts-band-${band.tone}`;
          panel.style.left = `${layout.left}%`;
          panel.style.top = `${layout.top}%`;
          panel.style.width = `${layout.width}%`;
          panel.style.height = `${layout.height}%`;
          panel.style.transform = `rotate(${layout.angle}deg)`;
          panel.dataset.layoutItem = `retroshowcase32-${band.key}-panel`;
          board.append(panel);

          const text = document.createElement("div");
          text.className = `rts-title rts-title-${band.tone}`;
          text.style.left = `${layout.left + 1.2}%`;
          text.style.top = `${layout.top + 1.8}%`;
          text.style.width = `${layout.width - 2.4}%`;
          text.style.height = `${layout.height - 3.6}%`;
          text.style.transform = `rotate(${layout.angle}deg) skewX(-4deg)`;
          text.textContent = String(state[band.key] ?? defaults[band.key]);
          text.dataset.layoutItem = `retroshowcase32-${band.key}`;
          text.dataset.displayItem = "true";
          board.append(text);
          window.SupportLayout.fitLine(text, {
            width: board.clientWidth * (layout.width - 2.4) / 100,
            height: board.clientHeight * (layout.height - 3.6) / 100,
            maxSize: board.clientHeight * layout.max * scale,
            minSize: 38,
            tracking: -.025,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#ed1b68", "#ffdf56"),
          window.SupportLayout.contrast("#fffaf1", "#f31169"),
          window.SupportLayout.contrast("#ed1b68", "#00a98e"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createIconicPoster() {
    const defaults = { headline: "Iconic" };
    const shapes = [
      ["path", { d: "M56 310l122-21-23 143z", fill: "#00a98e" }],
      ["path", { d: "M253 328l57 42-56 46-57-43z", fill: "#ed2671" }],
      ["path", { d: "M592 285l70-14-24 23 63-12 22 25-133 26-15-24 44-9z", fill: "#ed2671" }],
      ["path", { d: "M1118 287l30-38 30 37-31 27z", fill: "#00a98e" }],
      ["path", { d: "M1282 210l75-16-38 57-64-14z", fill: "#ed2671" }],
      ["path", { d: "M1496 224l47 10-24 34-40-14z", fill: "#00a98e" }],
      ["path", { d: "M1619 181v106h-15V194h-13v94h-15V186h-13v102h-15V181z", fill: "#ed2671" }],
      ["path", { d: "M48 933l50-22 40 62-69 18z", fill: "#00a98e" }],
      ["path", { d: "M247 960h19v93h-17v-65h-12v65h-16v-65h-11v65h-17v-94h17v25h15v-25h16v24h15z", fill: "#ed2671" }],
      ["path", { d: "M501 908l35 31-41 43-28-37z", fill: "#ed2671" }],
      ["path", { d: "M695 922l64 5 31 86-60-11z", fill: "#00a98e" }],
      ["path", { d: "M928 956l52-20 48 53-76 19z", fill: "#ed2671" }],
      ["path", { d: "M1080 936l92 18-27 19 90-12 43 24-167 27-12-23-73 9z", fill: "#00a98e" }],
      ["path", { d: "M1630 834l47 12-26 75-39-22z", fill: "#ed2671" }],
    ];
    const svgNode = (tag, attrs) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    };
    const design = {
      id: "iconicposter32",
      title: "Iconic angled feature word poster",
      literalKeys: ["headline"],
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "headline", type: "text", label: "Main lettering" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 3,
        rationale: "The oversized headline uses a darkened teal to stay distinct from the saturated magenta slab and yellow paper.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-iconicposter");
        board.classList.toggle("iconicposter-square", square);
        board.replaceChildren();

        const paper = document.createElement("div");
        paper.className = "icp-paper";
        paper.setAttribute("aria-hidden", "true");
        board.append(paper);

        const confetti = svgNode("svg", {
          class: "icp-confetti",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        shapes.forEach(([tag, attrs]) => confetti.append(svgNode(tag, attrs)));
        board.append(confetti);

        const stripe = document.createElement("div");
        stripe.className = "icp-stripe-shadow";
        board.append(stripe);
        const slabShadow = document.createElement("div");
        slabShadow.className = "icp-slab-shadow";
        board.append(slabShadow);
        const slab = document.createElement("div");
        slab.className = "icp-slab";
        board.append(slab);

        const labels = [
          ["RADICAL", "icp-label icp-label-top-left"],
          ["RETRO SCRIPT SPECIMEN", "icp-label icp-label-top-right"],
          ["DISPLAY LETTERFORMS", "icp-label icp-label-bottom-left"],
          ["TYPE STUDY · 03", "icp-label icp-label-bottom-right"],
        ];
        labels.forEach(([text, className]) => {
          const label = document.createElement("span");
          label.className = className;
          label.textContent = text;
          board.append(label);
        });

        const item = document.createElement("div");
        item.className = "icp-headline";
        const geometry = square
          ? { left: 4, top: 14, width: 92, height: 72, max: .69, angle: -4.8 }
          : { left: 4, top: 14, width: 92, height: 72, max: .69, angle: -4.8 };
        item.style.left = `${geometry.left}%`;
        item.style.top = `${geometry.top}%`;
        item.style.width = `${geometry.width}%`;
        item.style.height = `${geometry.height}%`;
        item.style.transform = `rotate(${geometry.angle}deg)`;
        item.textContent = String(state.headline ?? defaults.headline);
        item.dataset.layoutItem = "iconicposter32-headline";
        item.dataset.displayItem = "true";
        board.append(item);
        window.SupportLayout.fitLine(item, {
          width: board.clientWidth * geometry.width / 100,
          height: board.clientHeight * geometry.height / 100,
          maxSize: board.clientHeight * geometry.max * scale,
          minSize: 38,
          tracking: -.04,
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#003a34", "#f31169");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createSummerParadise() {
    const defaults = { topLine: "Summer", bottomLine: "Paradise" };
    const rays = [
      "M554 165l-23-78", "M656 125l-12-86", "M781 103l7-84", "M902 107l22-82",
      "M1034 138l39-73", "M1152 206l55-62", "M443 206l-49-60", "M337 298l-73-35",
      "M1334 300l67-29", "M428 588l-59 41", "M1272 587l61 44", "M648 701l-8 64",
      "M1004 697l17 68",
    ];
    const cloudPaths = [
      "M0 1204V1112c31-41 62-59 104-57 24-75 124-90 174-29 60-38 127-3 139 69 44 7 81 48 85 109H0z",
      "M616 1204c14-61 68-95 127-76 17-65 92-85 141-40 50-42 132-24 153 42 57-2 101 31 113 74H616z",
      "M1332 1204c6-64 50-107 112-99 18-74 114-92 165-34 58-28 144-5 191 59v74h-468z",
    ];
    const svgNode = (tag, attrs) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    };
    const design = {
      id: "summerparadise32",
      title: "Summer Paradise sunburst lettering",
      literalKeys: ["topLine", "bottomLine"],
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "topLine", type: "text", label: "Upper lettering" },
        { key: "bottomLine", type: "text", label: "Lower lettering" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 1.5,
        rationale: "The source's warm cream lettering crosses a coral field and orange sun while retaining the original bright summer palette.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-summerparadise");
        board.classList.toggle("summerparadise-square", square);
        board.replaceChildren();

        const texture = document.createElement("div");
        texture.className = "spx-texture";
        texture.setAttribute("aria-hidden", "true");
        board.append(texture);

        const sun = document.createElement("div");
        sun.className = "spx-sun";
        sun.setAttribute("aria-hidden", "true");
        board.append(sun);

        const raySvg = svgNode("svg", {
          class: "spx-rays",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        rays.forEach((d) => raySvg.append(svgNode("path", { d })));
        board.append(raySvg);

        const cloudSvg = svgNode("svg", {
          class: "spx-clouds",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        cloudPaths.forEach((d, index) => cloudSvg.append(svgNode("path", {
          d,
          class: `spx-cloud spx-cloud-${index + 1}`,
        })));
        board.append(cloudSvg);

        const specs = square
          ? [
              { key: "topLine", left: 3, top: 20, width: 94, height: 28, max: .37 },
              { key: "bottomLine", left: 3, top: 43, width: 94, height: 28, max: .37 },
            ]
          : [
              { key: "topLine", left: 9, top: 17, width: 82, height: 29, max: .4 },
              { key: "bottomLine", left: 8, top: 41, width: 84, height: 29, max: .4 },
            ];
        const items = [];
        specs.forEach((spec) => {
          const item = document.createElement("div");
          item.className = `spx-title spx-title-${spec.key}`;
          item.style.left = `${spec.left}%`;
          item.style.top = `${spec.top}%`;
          item.style.width = `${spec.width}%`;
          item.style.height = `${spec.height}%`;
          item.textContent = String(state[spec.key] ?? defaults[spec.key]);
          item.dataset.layoutItem = `summerparadise32-${spec.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          items.push(item);
        });
        window.SupportLayout.fitLinesTogether(items, {
          width: board.clientWidth * Math.min(...specs.map((spec) => spec.width)) * .9 / 100,
          height: board.clientHeight * Math.min(...specs.map((spec) => spec.height)) / 100,
          maxSize: board.clientHeight * Math.min(...specs.map((spec) => spec.max)) * scale,
          minSize: 38,
          tracking: -.035,
        });

        const underline = svgNode("svg", {
          class: "spx-underline",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        underline.append(svgNode("path", { d: "M580 878c177-45 449-48 643-9", class: "spx-underline-shadow" }));
        underline.append(svgNode("path", { d: "M574 865c177-45 449-48 643-9", class: "spx-underline-mark" }));
        board.append(underline);
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#fff0d1", "#d94f48"),
          window.SupportLayout.contrast("#fff0d1", "#f6b648"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createCalgaryWelcome() {
    const defaults = { eyebrow: "Welcome to", headline: "Calgary" };
    const design = {
      id: "calgarywelcome32",
      title: "Calgary welcome lettering",
      literalKeys: ["eyebrow", "headline"],
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "eyebrow", type: "text", label: "Small lettering" },
        { key: "headline", type: "text", label: "Main lettering" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-calgarywelcome");
        board.classList.toggle("calgarywelcome-square", square);
        board.replaceChildren();

        const texture = document.createElement("div");
        texture.className = "cgw-texture";
        texture.setAttribute("aria-hidden", "true");
        board.append(texture);

        const eyebrow = document.createElement("div");
        eyebrow.className = "cgw-eyebrow";
        eyebrow.style.left = square ? "36%" : "52%";
        eyebrow.style.top = square ? "10%" : "7%";
        eyebrow.style.width = square ? "61%" : "43%";
        eyebrow.style.height = square ? "19%" : "20%";
        eyebrow.textContent = String(state.eyebrow ?? defaults.eyebrow);
        eyebrow.dataset.layoutItem = "calgarywelcome32-eyebrow";
        eyebrow.dataset.displayItem = "true";
        board.append(eyebrow);
        window.SupportLayout.fitLine(eyebrow, {
          width: board.clientWidth * (square ? .61 : .43),
          height: board.clientHeight * (square ? .19 : .20),
          maxSize: board.clientHeight * (square ? .21 : .225) * scale,
          minSize: 38,
          tracking: -.02,
        });

        const headline = document.createElement("div");
        headline.className = "cgw-headline";
        headline.style.left = square ? "3%" : "4%";
        headline.style.top = square ? "21%" : "16%";
        headline.style.width = square ? "94%" : "92%";
        headline.style.height = square ? "57%" : "58%";
        headline.textContent = String(state.headline ?? defaults.headline);
        headline.dataset.layoutItem = "calgarywelcome32-headline";
        headline.dataset.displayItem = "true";
        board.append(headline);
        window.SupportLayout.fitLine(headline, {
          width: board.clientWidth * (square ? .94 : .92),
          height: board.clientHeight * (square ? .57 : .58),
          maxSize: board.clientHeight * (square ? .62 : .66) * scale,
          minSize: 38,
          tracking: -.025,
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#fff8ed", "#70271a"),
          window.SupportLayout.contrast("#c0ded0", "#70271a"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createLatinMaxims() {
    const defaults = {
      lineOne: "A CANE NON MAGNO SAEPE TENETUR APER",
      lineTwo: "Nil sine magno labore vita dedit mortalibus",
      lineThree: "BENE QUI LATUIT BENE VIXIT",
      lineFour: "Exercitus ex fortuna",
      lineFive: "FELICITAS EST PARVUS CANIS CALLIDUS",
    };
    const design = {
      id: "latinmaxims32",
      title: "Five-line Latin type specimen",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "Top line" },
        { key: "lineTwo", type: "text", label: "Second line" },
        { key: "lineThree", type: "text", label: "Center line" },
        { key: "lineFour", type: "text", label: "Large line" },
        { key: "lineFive", type: "text", label: "Bottom line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-latinmaxims");
        board.classList.toggle("latinmaxims-square", square);
        board.replaceChildren();
        const rows = square
          ? [
              { key: "lineOne", top: 4, height: 12, max: .14 },
              { key: "lineTwo", top: 17, height: 13, max: .155 },
              { key: "lineThree", top: 32, height: 16, max: .215 },
              { key: "lineFour", top: 51, height: 21, max: .29 },
              { key: "lineFive", top: 85, height: 12, max: .14 },
            ]
          : [
              { key: "lineOne", top: 3, height: 13, max: .135 },
              { key: "lineTwo", top: 17, height: 17, max: .19 },
              { key: "lineThree", top: 35, height: 17, max: .235 },
              { key: "lineFour", top: 57, height: 24, max: .31 },
              { key: "lineFive", top: 85, height: 13, max: .17 },
            ];
        rows.forEach((row, index) => {
          const item = document.createElement("div");
          item.className = `ltm-line ltm-line-${index + 1}`;
          item.style.left = square ? "3%" : "6%";
          item.style.top = `${row.top}%`;
          item.style.width = square ? "94%" : "88%";
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `latinmaxims32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * (square ? .94 : .88),
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: 38,
            tracking: -.025,
          });
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#f8f7f4", "#09090b");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createOnlyGoodDieYoung() {
    const defaults = { lineOne: "Only", lineTwo: "the Good", lineThree: "Die Young" };
    const scene = [
      ["path", { d: "M953 107a74 74 0 1 0 93 105 88 88 0 0 1-93-105z", fill: "#ffb20d", stroke: "#111112", "stroke-width": 7 }],
      ["path", { d: "M52 171c30-42 85-42 119-9 35-38 96-32 117 15-32 40-82 52-118 22-35 32-83 28-118-9z", fill: "#414144", stroke: "#111112", "stroke-width": 8, "stroke-linejoin": "round" }],
      ["path", { d: "M358 122c34-52 107-63 153-16 42-46 111-34 135 22-32 41-80 52-122 28-44 39-114 28-166-5z", fill: "#3b3b3e", stroke: "#111112", "stroke-width": 9, "stroke-linejoin": "round" }],
      ["path", { d: "M174 220c30-27 57-55 74-91 8 43 21 68 47 92 28-38 51-59 77-72-4 40-20 69-47 100 27 20 44 39 59 65-42-4-73-16-103-43-19 33-40 54-70 74 4-45 15-77 40-109-35-5-58-10-77-16z", fill: "#28282a", stroke: "#111112", "stroke-width": 8, "stroke-linejoin": "round" }],
      ["path", { d: "M1270 83c49-51 127-61 194-26 51-45 137-36 193 12 49-14 103 3 135 45-58 7-107 0-156-21-44 33-102 39-152 9-58 27-122 22-175-7-38 8-62 3-89-12z", fill: "#28282a", stroke: "#111112", "stroke-width": 9, "stroke-linejoin": "round" }],
      ["path", { d: "M1326 389l95-99 118 82 113-45 93 102-19 345h-409z", fill: "#2b2b2e", stroke: "#111112", "stroke-width": 12, "stroke-linejoin": "round" }],
      ["path", { d: "M1085 495l98-131 82 74v337h-194z", fill: "#303033", stroke: "#111112", "stroke-width": 12, "stroke-linejoin": "round" }],
      ["path", { d: "M1181 364l132-142 122 120", fill: "none", stroke: "#111112", "stroke-width": 12, "stroke-linejoin": "round" }],
      ["path", { d: "M1467 800v-87c0-41 62-41 62 0v87z", fill: "#444447", stroke: "#111112", "stroke-width": 10 }],
      ["path", { d: "M1374 526v71h62v-71z M1533 530v67h62v-67z M1141 568v59h51v-59z M1241 568v59h51v-59z", fill: "#4b4b4e", stroke: "#111112", "stroke-width": 9 }],
      ["path", { d: "M-20 865c55-85 91-139 135-224 8 84 26 139 52 196 29-53 71-94 121-128-18 72-41 124-84 172 48 9 95 29 140 61", fill: "none", stroke: "#19191b", "stroke-width": 17, "stroke-linecap": "round", "stroke-linejoin": "round" }],
      ["path", { d: "M105 762l-62-39 M132 715l42-67 M164 799l69-48 M218 822l90-17 M74 817l-70-3", fill: "none", stroke: "#19191b", "stroke-width": 13, "stroke-linecap": "round" }],
      ["path", { d: "M0 917h1800 M0 950h1800", fill: "none", stroke: "#202023", "stroke-width": 15 }],
      ["path", { d: "M22 885v97 M78 880v107 M134 894v90 M190 882v108 M246 889v99 M301 887v102 M357 885v105 M413 883v111 M469 885v105 M525 881v111 M581 889v100 M637 883v109 M693 884v106 M749 886v104 M805 881v110 M861 884v106 M917 883v108 M973 884v106 M1029 881v110 M1085 887v104 M1141 883v108 M1197 886v106 M1253 881v110 M1309 884v107 M1365 882v109 M1421 885v105 M1477 881v112 M1533 884v108 M1589 883v109 M1645 882v108 M1701 885v106 M1757 883v108", fill: "none", stroke: "#202023", "stroke-width": 11 }],
      ["path", { d: "M0 1040l440 44 385-27 405 39 570-63v171H0z", fill: "#050506" }],
    ];
    const svgNode = (tag, attrs) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    };
    const design = {
      id: "onlygooddieyoung32",
      title: "Only the Good Die Young night poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "Upper line" },
        { key: "lineTwo", type: "text", label: "Middle line" },
        { key: "lineThree", type: "text", label: "Lower line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 2.2,
        rationale: "The original uses gold-orange lettering across slate gray and charcoal Halloween artwork with intentionally low tonal separation.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-onlygooddieyoung");
        board.classList.toggle("onlygooddieyoung-square", square);
        board.replaceChildren();

        const art = svgNode("svg", {
          class: "ogd-scene",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        scene.forEach(([tag, attrs]) => art.append(svgNode(tag, attrs)));
        board.append(art);

        const rows = square
          ? [
              { key: "lineOne", left: 14, top: 19, width: 72, height: 19, max: .25 },
              { key: "lineTwo", left: 7, top: 38, width: 86, height: 22, max: .32 },
              { key: "lineThree", left: 7, top: 60, width: 86, height: 23, max: .32 },
            ]
          : [
              { key: "lineOne", left: 19, top: 17, width: 62, height: 23, max: .285 },
              { key: "lineTwo", left: 13, top: 36, width: 74, height: 26, max: .33 },
              { key: "lineThree", left: 13, top: 59, width: 74, height: 28, max: .35 },
            ];
        rows.forEach((row, index) => {
          const item = document.createElement("div");
          item.className = `ogd-title ogd-title-${index + 1}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `onlygooddieyoung32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: 38,
            tracking: -.03,
          });
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#ffb20d", "#666669");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createBlackHoleSun() {
    const defaults = {
      titleOne: "BLACK",
      titleTwo: "HOLE SUN",
      lyric: "WON'T YOU COME",
      artist: "SOUNDGARDEN",
    };
    const streaks = [
      "M-20 352c203-44 353 32 524-11s327 14 504-27 362 25 525-15",
      "M-16 636c171-38 279 15 421-24s289 35 437-13 313 31 487-24 334 12 482-37",
      "M362 85c104 14 175-24 266-13s135 27 223 3",
      "M1040 1032c160-31 283 11 422-27s204 9 365-35",
    ];
    const svgNode = (tag, attrs) => {
      const node = document.createElementNS("http://www.w3.org/2000/svg", tag);
      for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
      return node;
    };
    const design = {
      id: "blackholesun32",
      title: "Black Hole Sun stacked title poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "titleOne", type: "text", label: "Top title line" },
        { key: "titleTwo", type: "text", label: "Second title line" },
        { key: "lyric", type: "text", label: "Blue lyric line" },
        { key: "artist", type: "text", label: "Lower credit" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 2.0,
        rationale: "The source intentionally uses saturated blue secondary lyrics beside bright cyan title text on near-black artwork.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-blackholesun");
        board.classList.toggle("blackholesun-square", square);
        board.replaceChildren();

        const texture = document.createElement("div");
        texture.className = "bhs-texture";
        texture.setAttribute("aria-hidden", "true");
        board.append(texture);

        const streakSvg = svgNode("svg", {
          class: "bhs-streaks",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        streaks.forEach((d, index) => streakSvg.append(svgNode("path", {
          d,
          class: `bhs-streak bhs-streak-${index + 1}`,
        })));
        board.append(streakSvg);

        const sun = document.createElement("div");
        sun.className = "bhs-sun";
        sun.setAttribute("aria-hidden", "true");
        board.append(sun);
        ["bhs-sun-cut bhs-sun-cut-one", "bhs-sun-cut bhs-sun-cut-two", "bhs-sun-glint"].forEach((className) => {
          const shape = document.createElement("div");
          shape.className = className;
          shape.setAttribute("aria-hidden", "true");
          board.append(shape);
        });

        const rows = square
          ? [
              { key: "titleOne", left: 7, top: 13, width: 82, height: 18, max: .26, className: "bhs-title" },
              { key: "titleTwo", left: 4, top: 31, width: 92, height: 20, max: .28, className: "bhs-title" },
              { key: "lyric", left: 7, top: 53, width: 56, height: 9, max: .13, className: "bhs-lyric" },
              { key: "artist", left: 55, top: 91, width: 39, height: 4.5, max: .055, className: "bhs-artist" },
            ]
          : [
              { key: "titleOne", left: 22, top: 17, width: 49, height: 20, max: .29, className: "bhs-title" },
              { key: "titleTwo", left: 27, top: 37, width: 60, height: 20, max: .29, className: "bhs-title" },
              { key: "lyric", left: 15, top: 59, width: 49, height: 9, max: .13, className: "bhs-lyric" },
              { key: "artist", left: 59, top: 91, width: 32, height: 4.5, max: .055, className: "bhs-artist" },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = row.className;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `blackholesun32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: 30,
            tracking: -.025,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#00edf0", "#030405"),
          window.SupportLayout.contrast("#304bcc", "#030405"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createSomethingAboutHer() {
    const defaults = {
      lineOne: "Something",
      lineTwo: "About",
      lineThree: "Her.",
    };
    const design = {
      id: "somethingabouther32",
      title: "Something About Her textured lettering poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "Top line" },
        { key: "lineTwo", type: "text", label: "Middle line" },
        { key: "lineThree", type: "text", label: "Bottom line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.14, step: .01 },
      ],
      contrastException: {
        minimum: 3.0,
        rationale: "The source uses warm ivory hand lettering on a mottled dark plum field; the textured surface slightly changes local contrast.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-somethingabouther");
        board.classList.toggle("somethingabouther-square", square);
        board.replaceChildren();

        const texture = document.createElement("div");
        texture.className = "sah-texture";
        texture.setAttribute("aria-hidden", "true");
        board.append(texture);

        const grainSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        grainSvg.classList.add("sah-grain");
        grainSvg.setAttribute("viewBox", "0 0 1800 1204");
        grainSvg.setAttribute("preserveAspectRatio", "none");
        grainSvg.setAttribute("aria-hidden", "true");
        grainSvg.innerHTML = '<filter id="sah-grain-filter"><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#sah-grain-filter)"/>';
        board.append(grainSvg);

        const rows = square
          ? [
              { key: "lineOne", left: 17, top: 19, width: 66, height: 17, max: .19 },
              { key: "lineTwo", left: 26, top: 38, width: 48, height: 17, max: .2 },
              { key: "lineThree", left: 31, top: 56, width: 38, height: 19, max: .22 },
            ]
          : [
              { key: "lineOne", left: 24, top: 18, width: 52, height: 18, max: .2 },
              { key: "lineTwo", left: 33, top: 37, width: 34, height: 18, max: .21 },
              { key: "lineThree", left: 38, top: 55, width: 24, height: 19, max: .23 },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `sah-title sah-title-${row.key}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `somethingabouther32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: 30,
            tracking: -.035,
          });
        });

        const underline = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        underline.classList.add("sah-underline");
        underline.setAttribute("viewBox", "0 0 360 40");
        underline.setAttribute("preserveAspectRatio", "none");
        underline.setAttribute("aria-hidden", "true");
        underline.innerHTML = '<path d="M8 30c64-15 161-9 340-28"/>';
        board.append(underline);
      },
      getContrast() {
        return window.SupportLayout.contrast("#f2eadb", "#392433");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createDarkNightBrighterDay() {
    const defaults = {
      lineOne: "For every",
      lineTwo: "dark night,",
      lineThree: "there's a",
      lineFour: "brighter day.",
    };
    const design = {
      id: "darknightbrighterday32",
      title: "For Every Dark Night quote poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "First line" },
        { key: "lineTwo", type: "text", label: "Second line" },
        { key: "lineThree", type: "text", label: "Third line" },
        { key: "lineFour", type: "text", label: "Final line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.14, step: .01 },
      ],
      contrastException: {
        minimum: 3.0,
        rationale: "The source keeps the warm white quote legible over a dark mottled charcoal-blue and burgundy texture.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-darknightbrighterday");
        board.classList.toggle("darknightbrighterday-square", square);
        board.replaceChildren();

        const texture = document.createElement("div");
        texture.className = "dnbd-texture";
        texture.setAttribute("aria-hidden", "true");
        board.append(texture);

        const grainSvg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
        grainSvg.classList.add("dnbd-grain");
        grainSvg.setAttribute("viewBox", "0 0 1800 1204");
        grainSvg.setAttribute("preserveAspectRatio", "none");
        grainSvg.setAttribute("aria-hidden", "true");
        grainSvg.innerHTML = '<filter id="dnbd-grain-filter"><feTurbulence type="fractalNoise" baseFrequency=".8" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#dnbd-grain-filter)"/>';
        board.append(grainSvg);

        const rows = square
          ? [
              { key: "lineOne", left: 16, top: 21, width: 68, height: 13, max: .16 },
              { key: "lineTwo", left: 11, top: 35, width: 78, height: 14, max: .18 },
              { key: "lineThree", left: 23, top: 50, width: 54, height: 13, max: .17 },
              { key: "lineFour", left: 7, top: 64, width: 86, height: 15, max: .19 },
            ]
          : [
              { key: "lineOne", left: 30, top: 20, width: 40, height: 14, max: .2 },
              { key: "lineTwo", left: 27, top: 35, width: 46, height: 14, max: .21 },
              { key: "lineThree", left: 32, top: 50, width: 36, height: 14, max: .21 },
              { key: "lineFour", left: 22, top: 65, width: 56, height: 16, max: .22 },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `dnbd-title dnbd-title-${row.key}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `darknightbrighterday32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: 30,
            tracking: -.025,
          });
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#ece9de", "#17191d");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createTcPanthomaSpecimen() {
    const defaults = {
      topLeft: "TC PANTHOMA",
      topCenter: "391 GLYPHS",
      topRight: "TYPE COLONY",
      titleOne: "TC PANTHOMA",
      titleTwo: "TYPEFACE",
      titleThree: "TC PANTHOMA",
      bottomLeft: "TC PANTHOMA",
      bottomCenter: "391 GLYPHS",
      bottomRight: "TYPE COLONY",
    };
    const design = {
      id: "tc-panthoma-specimen32",
      title: "TC Panthoma red specimen poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "topLeft", type: "text", label: "Upper left label" },
        { key: "topCenter", type: "text", label: "Upper center label" },
        { key: "topRight", type: "text", label: "Upper right label" },
        { key: "titleOne", type: "text", label: "First title line" },
        { key: "titleTwo", type: "text", label: "Middle title line" },
        { key: "titleThree", type: "text", label: "Final title line" },
        { key: "bottomLeft", type: "text", label: "Lower left label" },
        { key: "bottomCenter", type: "text", label: "Lower center label" },
        { key: "bottomRight", type: "text", label: "Lower right label" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.14, step: .01 },
      ],
      contrastException: {
        minimum: 3.0,
        rationale: "The original deliberately uses saturated red type on black; small specimen metadata is a darker red than the oversized title.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-tcpanthomaspecimen");
        board.classList.toggle("tcpanthoma-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "topLeft", left: 2, top: 3, width: 28, height: 5, max: .033, kind: "meta left" },
              { key: "topCenter", left: 36, top: 3, width: 28, height: 5, max: .033, kind: "meta center" },
              { key: "topRight", left: 70, top: 3, width: 28, height: 5, max: .033, kind: "meta right" },
              { key: "titleOne", left: 2, top: 15, width: 96, height: 16, max: .16, kind: "title" },
              { key: "titleTwo", left: 13, top: 34, width: 74, height: 16, max: .16, kind: "title" },
              { key: "titleThree", left: 2, top: 53, width: 96, height: 16, max: .16, kind: "title" },
              { key: "bottomLeft", left: 2, top: 92, width: 28, height: 5, max: .033, kind: "meta left" },
              { key: "bottomCenter", left: 36, top: 92, width: 28, height: 5, max: .033, kind: "meta center" },
              { key: "bottomRight", left: 70, top: 92, width: 28, height: 5, max: .033, kind: "meta right" },
            ]
          : [
              { key: "topLeft", left: 1.5, top: 2.4, width: 28, height: 5, max: .035, kind: "meta left" },
              { key: "topCenter", left: 36, top: 2.4, width: 28, height: 5, max: .035, kind: "meta center" },
              { key: "topRight", left: 70.5, top: 2.4, width: 28, height: 5, max: .035, kind: "meta right" },
              { key: "titleOne", left: 2, top: 13, width: 96, height: 21, max: .22, kind: "title" },
              { key: "titleTwo", left: 18, top: 34, width: 64, height: 20, max: .22, kind: "title" },
              { key: "titleThree", left: 2, top: 54, width: 96, height: 22, max: .23, kind: "title" },
              { key: "bottomLeft", left: 1.5, top: 92, width: 28, height: 5, max: .035, kind: "meta left" },
              { key: "bottomCenter", left: 36, top: 92, width: 28, height: 5, max: .035, kind: "meta center" },
              { key: "bottomRight", left: 70.5, top: 92, width: 28, height: 5, max: .035, kind: "meta right" },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `tps-${row.kind.replaceAll(" ", "-")}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `tc-panthoma-specimen32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.kind.includes("meta") ? 15 : 28,
            tracking: row.kind.includes("meta") ? 0 : -.02,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#ed1c24", "#030303"),
          window.SupportLayout.contrast("#bd1821", "#030303"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createTcPanthomaRepeat() {
    const defaults = {
      lineOne: "TC PANTHOMA",
      lineTwo: "TYPEFACE®",
      lineThree: "TC PANTHOMA",
      lineFour: "TYPEFACE®",
    };
    const design = {
      id: "tcpanthomarepeat32",
      title: "TC Panthoma repeated type specimen",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "First specimen line" },
        { key: "lineTwo", type: "text", label: "Second specimen line" },
        { key: "lineThree", type: "text", label: "Third specimen line" },
        { key: "lineFour", type: "text", label: "Fourth specimen line" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.14, step: .01 },
      ],
      contrastException: {
        minimum: 3.0,
        rationale: "The oversized near-black specimen lines retain the source red-orange field and meet the 3:1 large-type threshold; small edge labels use a brighter red.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-tcpanthomarepeat");
        board.classList.toggle("tcpanthomarepeat-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "lineOne", left: 4, top: 12, width: 92, height: 15, max: .155 },
              { key: "lineTwo", left: 17, top: 31, width: 66, height: 15, max: .155 },
              { key: "lineThree", left: 4, top: 50, width: 92, height: 15, max: .155 },
              { key: "lineFour", left: 17, top: 69, width: 66, height: 15, max: .155 },
            ]
          : [
              { key: "lineOne", left: 5, top: 4, width: 90, height: 20, max: .22 },
              { key: "lineTwo", left: 17, top: 27, width: 66, height: 20, max: .22 },
              { key: "lineThree", left: 5, top: 50, width: 90, height: 20, max: .22 },
              { key: "lineFour", left: 17, top: 73, width: 66, height: 20, max: .22 },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = "tpr-title";
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `tcpanthomarepeat32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: 28,
            tracking: -.02,
          });
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#050505", "#c72b20");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createStrongerQuote() {
    const defaults = {
      lineOne: "It Doesn't",
      lineTwo: "get easier,",
      lineThree: "you just get",
      lineFour: "stronger",
    };
    const design = {
      id: "strongerquote32",
      title: "It Does Not Get Easier quote poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOne", type: "text", label: "First line" },
        { key: "lineTwo", type: "text", label: "Second line" },
        { key: "lineThree", type: "text", label: "Third line" },
        { key: "lineFour", type: "text", label: "Final line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "White quote lettering sits against black and deep charcoal panels; the cleaned text-free portrait remains a cropped image layer.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-strongerquote");
        board.classList.toggle("strongerquote-square", square);
        board.replaceChildren();

        const photoFrame = document.createElement("div");
        photoFrame.className = "sq-photo-frame";
        photoFrame.setAttribute("aria-hidden", "true");
        const photo = document.createElement("img");
        photo.className = "sq-photo";
        photo.src = "../../../support-references/materials/T26790_05_text-free-portrait.png";
        photo.alt = "";
        photoFrame.append(photo);
        board.append(photoFrame);

        const textPanel = document.createElement("div");
        textPanel.className = "sq-text-panel";
        textPanel.setAttribute("aria-hidden", "true");
        board.append(textPanel);

        const quoteOpen = document.createElement("div");
        quoteOpen.className = "sq-quote-mark sq-quote-open";
        quoteOpen.textContent = "“";
        quoteOpen.setAttribute("aria-hidden", "true");
        board.append(quoteOpen);
        const quoteClose = document.createElement("div");
        quoteClose.className = "sq-quote-mark sq-quote-close";
        quoteClose.textContent = "”";
        quoteClose.setAttribute("aria-hidden", "true");
        board.append(quoteClose);

        const rows = square
          ? [
              { key: "lineOne", left: 49, top: 15, width: 49, height: 13, max: .13 },
              { key: "lineTwo", left: 49, top: 33, width: 49, height: 13, max: .13 },
              { key: "lineThree", left: 47, top: 51, width: 51, height: 13, max: .13 },
              { key: "lineFour", left: 51, top: 69, width: 47, height: 14, max: .135 },
            ]
          : [
              { key: "lineOne", left: 52, top: 16, width: 44, height: 15, max: .17 },
              { key: "lineTwo", left: 52, top: 34, width: 44, height: 15, max: .17 },
              { key: "lineThree", left: 51, top: 52, width: 45, height: 15, max: .17 },
              { key: "lineFour", left: 55, top: 70, width: 40, height: 15, max: .18 },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `sq-line sq-line-${row.key}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `strongerquote32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: 28,
            tracking: -.02,
          });
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#f2f1ed", "#090a0d");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createScaryGangsta() {
    const defaults = {
      titleOne: "SCARY",
      titleTwo: "GANGSTA",
      badge: "The",
      footer: "EVERY THURSDAY, 9 PM",
    };
    const forestShapes = [
      ["path", { d: "M0 0h170l-58 94 88 8-106 74 91 13-122 96 96 4-112 93 86 16-109 107 77 10L0 600z", fill: "#171027" }],
      ["path", { d: "M1800 0h-178l69 84-90 13 114 72-88 19 120 86-96 11 112 89-86 14 101 95-77 8L1800 600z", fill: "#171027" }],
      ["path", { d: "M0 405l118 44-83 4 142 74-112-11 154 100-137-21 179 118-149-12L0 744z", fill: "#1c1530" }],
      ["path", { d: "M1800 370l-130 58 97 5-152 80 112-8-160 104 142-23-176 118 167-17L1800 752z", fill: "#1c1530" }],
      ["path", { d: "M226 0l67 58-61 9 89 54-68 10 102 60-77-5 111 77-81-8 79 87-114-29-96-87-63-115z", fill: "#261938" }],
      ["path", { d: "M1576 0l-63 57 66 8-92 53 74 10-104 61 79-6-114 77 84-8-85 87 116-29 99-86 64-116z", fill: "#261938" }],
      ["path", { d: "M0 1044l191-180 97 87 81-70 145 121 91-70 140 113 88-78 160 107 103-82 170 92 107-88 146 76 121-105v253H0z", fill: "#151023" }],
    ];
    const design = {
      id: "scarygangsta32",
      title: "The Scary Gangsta moon poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "titleOne", type: "text", label: "Upper title" },
        { key: "titleTwo", type: "text", label: "Lower title" },
        { key: "badge", type: "text", label: "Badge copy" },
        { key: "footer", type: "text", label: "Footer line" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.14, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "The title and footer remain bright against the dark violet forest; the badge uses warm white on deep red.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-scarygangsta");
        board.classList.toggle("scarygangsta-square", square);
        board.replaceChildren();

        const moonLight = document.createElement("div");
        moonLight.className = "sg-moon-light";
        moonLight.setAttribute("aria-hidden", "true");
        board.append(moonLight);

        const moon = document.createElement("div");
        moon.className = "sg-moon";
        moon.setAttribute("aria-hidden", "true");
        board.append(moon);

        const forest = svgNode("svg", {
          class: "sg-forest",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        forestShapes.forEach(([tag, attrs]) => forest.append(svgNode(tag, attrs)));
        board.append(forest);

        const rows = square
          ? [
              { key: "titleOne", left: 16, top: 22, width: 68, height: 21, max: .22, kind: "title title-one" },
              { key: "titleTwo", left: 8, top: 43, width: 84, height: 22, max: .22, kind: "title title-two" },
              { key: "badge", left: 8, top: 28, width: 25, height: 12, max: .1, kind: "badge" },
              { key: "footer", left: 11, top: 85, width: 78, height: 7, max: .052, kind: "footer" },
            ]
          : [
              { key: "titleOne", left: 26, top: 17, width: 57, height: 26, max: .25, kind: "title title-one" },
              { key: "titleTwo", left: 18, top: 43, width: 66, height: 24, max: .24, kind: "title title-two" },
              { key: "badge", left: 14, top: 25, width: 23, height: 13, max: .1, kind: "badge" },
              { key: "footer", left: 20, top: 86, width: 60, height: 7, max: .054, kind: "footer" },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `sg-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `scarygangsta32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.key === "footer" ? 18 : 30,
            tracking: row.key === "footer" ? .32 : -.025,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#ff8b4c", "#1b1430"),
          window.SupportLayout.contrast("#ff6476", "#1b1430"),
          window.SupportLayout.contrast("#fff8eb", "#a52649"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createDarkBritonPoster() {
    const defaults = {
      eyebrow: "INTRODUCING",
      newLabel: "NEW",
      title: "DARK BRITON",
      glyphCount: "789 GLYPHS",
      copy: "BRUTAL TYPE · 789 GLYPHS · ALTERNATES · LIGATURES · MULTILINGUAL",
      footerLeft: "PROUDLY PRESENTED",
      footerCenter: "MULTILINGUAL",
      footerRight: "ACCENT",
    };
    const distress = [
      "M93 91l48-22m35 66l31-35m68 82l27-51m-18 273l59-42m-12 68l44-21m-8 95l55-38",
      "M422 58l23 37m48 6l-31 50m151-68l-13 45m211-28l37 48m64-25l-27 39",
      "M1290 71l-36 44m96 5l-50 38m93 67l-34 28m-10 281l49-18m-110 61l44-34",
      "M1680 105l-42 33m54 118l-47 21m89 103l-65 19m43 229l-50 42",
      "M534 584l68-34m79 53l41-19m274-34l48-24m86 49l57-26m-730 118l39-18",
    ];
    const design = {
      id: "darkbriton32",
      title: "Dark Briton distressed type poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "eyebrow", type: "text", label: "Top center" },
        { key: "newLabel", type: "text", label: "New label" },
        { key: "title", type: "text", label: "Main title" },
        { key: "glyphCount", type: "text", label: "Glyph count" },
        { key: "copy", type: "text", label: "Description line" },
        { key: "footerLeft", type: "text", label: "Footer left" },
        { key: "footerCenter", type: "text", label: "Footer center" },
        { key: "footerRight", type: "text", label: "Footer right" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.13, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "The source uses white specimen copy on nearly black and dark red artwork, with secondary red copy confined to small badges.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-darkbriton");
        board.classList.toggle("darkbriton-square", square);
        board.replaceChildren();

        const panel = document.createElement("div");
        panel.className = "db-panel";
        panel.setAttribute("aria-hidden", "true");
        board.append(panel);

        const grain = svgNode("svg", {
          class: "db-grain",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        grain.innerHTML = '<filter id="db-noise"><feTurbulence type="fractalNoise" baseFrequency=".76" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#db-noise)"/>';
        board.append(grain);

        const marks = svgNode("svg", {
          class: "db-marks",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        distress.forEach((d) => marks.append(svgNode("path", { d, class: "db-scratch" })));
        marks.append(svgNode("path", {
          d: "M650 232c70-60 128-59 201-28 40 18 74 20 106 1 68-42 146-33 208 37-49 59-85 111-103 169-22 73-25 168-73 226-39 47-99 54-171 45-113-15-189-87-191-206-1-79 24-164 23-244z",
          class: "db-figure",
        }));
        marks.append(svgNode("path", {
          d: "M744 364c47-52 104-49 137-9m94-5c38-37 84-39 122-4m-283 58l49 18m153-19l-42 19m-110 103c55 31 105 34 160-2",
          class: "db-figure-detail",
        }));
        board.append(marks);

        const trident = svgNode("svg", { class: "db-trident", viewBox: "0 0 120 64", "aria-hidden": "true" });
        [
          "M12 4c0 15 11 17 11 25V58H13V31C13 22 3 20 3 8c5 5 9 9 9 15z",
          "M49 4c0 15 11 17 11 25V58H50V31C50 22 40 20 40 8c5 5 9 9 9 15z",
          "M86 4c0 15 11 17 11 25V58H87V31C87 22 77 20 77 8c5 5 9 9 9 15z",
        ].forEach((d) => trident.append(svgNode("path", { d })));
        board.append(trident);

        const skullGroup = document.createElement("div");
        skullGroup.className = "db-skulls";
        skullGroup.setAttribute("aria-hidden", "true");
        for (let index = 0; index < 2; index += 1) {
          const skull = svgNode("svg", { viewBox: "0 0 64 70" });
          skull.append(svgNode("path", { d: "M32 3C15 3 6 17 7 34c.5 9 5 14 11 18v11h28V52c7-5 11-11 11-20C57 16 47 3 32 3z", class: "db-skull" }));
          skull.append(svgNode("circle", { cx: 22, cy: 31, r: 6, class: "db-skull-hole" }));
          skull.append(svgNode("circle", { cx: 42, cy: 31, r: 6, class: "db-skull-hole" }));
          skull.append(svgNode("path", { d: "M29 39l-4 9h14l-4-9z", class: "db-skull-hole" }));
          skullGroup.append(skull);
        }
        board.append(skullGroup);

        const footerArt = svgNode("svg", { class: "db-footer-art", viewBox: "0 0 520 90", "aria-hidden": "true" });
        for (let x = 8; x < 512; x += 9) footerArt.append(svgNode("path", { d: `M${x} 8v76`, class: "db-bar" }));
        board.append(footerArt);

        const rows = square
          ? [
              { key: "eyebrow", left: 27, top: 5, width: 46, height: 6, max: .045, kind: "eyebrow" },
              { key: "newLabel", left: 76, top: 5, width: 12, height: 5, max: .04, kind: "new" },
              { key: "title", left: 5, top: 34, width: 90, height: 18, max: .19, kind: "title" },
              { key: "glyphCount", left: 5, top: 75, width: 23, height: 8, max: .055, kind: "glyph" },
              { key: "copy", left: 29, top: 74, width: 67, height: 10, max: .044, kind: "copy" },
              { key: "footerLeft", left: 5, top: 89, width: 31, height: 5, max: .034, kind: "footer-left" },
              { key: "footerCenter", left: 40, top: 89, width: 34, height: 5, max: .034, kind: "footer-center" },
              { key: "footerRight", left: 78, top: 89, width: 17, height: 5, max: .034, kind: "footer-right" },
            ]
          : [
              { key: "eyebrow", left: 34, top: 6, width: 32, height: 6, max: .045, kind: "eyebrow" },
              { key: "newLabel", left: 76, top: 7, width: 12, height: 5, max: .04, kind: "new" },
              { key: "title", left: 6, top: 36, width: 88, height: 20, max: .23, kind: "title" },
              { key: "glyphCount", left: 17, top: 82, width: 13, height: 8, max: .055, kind: "glyph" },
              { key: "copy", left: 31, top: 82, width: 55, height: 8, max: .042, kind: "copy" },
              { key: "footerLeft", left: 6, top: 94, width: 24, height: 4, max: .03, kind: "footer-left" },
              { key: "footerCenter", left: 66, top: 94, width: 20, height: 4, max: .03, kind: "footer-center" },
              { key: "footerRight", left: 87, top: 94, width: 9, height: 4, max: .03, kind: "footer-right" },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `db-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `darkbriton32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.kind === "copy" ? 12 : 18,
            tracking: row.kind.includes("footer") || row.kind === "eyebrow" || row.kind === "new" ? .12 : -.02,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f7f5ef", "#171419"),
          window.SupportLayout.contrast("#f7f5ef", "#771924"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createDarkBritonThankYou() {
    const defaults = {
      eyebrow: "BEST REGARDS",
      title: "THANK YOU",
      glyphCount: "789 GLYPHS",
      copy: "BRUTAL TYPE · ALTERNATES · LIGATURES · MULTILINGUAL",
      footerLeft: "PROUDLY PRESENTED",
      footerCenter: "MULTILINGUAL",
      footerRight: "ACCENT",
    };
    const design = {
      id: "darkbritonthankyou32",
      title: "Dark Briton thank-you poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "eyebrow", type: "text", label: "Greeting" },
        { key: "title", type: "text", label: "Main headline" },
        { key: "glyphCount", type: "text", label: "Glyph count" },
        { key: "copy", type: "text", label: "Specimen detail" },
        { key: "footerLeft", type: "text", label: "Footer left" },
        { key: "footerCenter", type: "text", label: "Footer center" },
        { key: "footerRight", type: "text", label: "Footer right" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.13, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "The source uses white lettering on black and its original dark red artwork crop; the small details stay white.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-darkbriton-thankyou");
        board.classList.toggle("darkbriton-thankyou-square", square);
        board.replaceChildren();

        const grain = svgNode("svg", {
          class: "ty-grain",
          viewBox: "0 0 1800 1204",
          preserveAspectRatio: "none",
          "aria-hidden": "true",
        });
        grain.innerHTML = '<filter id="ty-noise"><feTurbulence type="fractalNoise" baseFrequency=".78" numOctaves="3" stitchTiles="stitch"/><feColorMatrix type="saturate" values="0"/></filter><rect width="100%" height="100%" filter="url(#ty-noise)"/>';
        board.append(grain);

        const artFrame = document.createElement("div");
        artFrame.className = "ty-art-frame";
        artFrame.setAttribute("aria-hidden", "true");
        const image = document.createElement("img");
        image.className = "ty-art-image";
        image.src = "../../../support-references/originals/reference-batch-2026-10-29-a/T25802_08.jpg";
        image.alt = "";
        artFrame.append(image);
        board.append(artFrame);

        const footerArt = svgNode("svg", { class: "ty-footer-art", viewBox: "0 0 520 90", "aria-hidden": "true" });
        for (let x = 8; x < 512; x += 9) footerArt.append(svgNode("path", { d: `M${x} 8v76`, class: "ty-bar" }));
        board.append(footerArt);

        const rows = square
          ? [
              { key: "eyebrow", left: 28, top: 4, width: 44, height: 6, max: .05, kind: "eyebrow" },
              { key: "title", left: 3, top: 12, width: 94, height: 21, max: .22, kind: "title" },
              { key: "glyphCount", left: 5, top: 68, width: 23, height: 8, max: .055, kind: "glyph" },
              { key: "copy", left: 29, top: 68, width: 67, height: 8, max: .045, kind: "copy" },
              { key: "footerLeft", left: 5, top: 87, width: 31, height: 5, max: .034, kind: "footer-left" },
              { key: "footerCenter", left: 40, top: 87, width: 34, height: 5, max: .034, kind: "footer-center" },
              { key: "footerRight", left: 78, top: 87, width: 17, height: 5, max: .034, kind: "footer-right" },
            ]
          : [
              { key: "eyebrow", left: 41, top: 5, width: 18, height: 6, max: .05, kind: "eyebrow" },
              { key: "title", left: 3, top: 10, width: 94, height: 28, max: .31, kind: "title" },
              { key: "glyphCount", left: 17, top: 82, width: 13, height: 8, max: .055, kind: "glyph" },
              { key: "copy", left: 31, top: 82, width: 55, height: 8, max: .045, kind: "copy" },
              { key: "footerLeft", left: 6, top: 94, width: 24, height: 4, max: .03, kind: "footer-left" },
              { key: "footerCenter", left: 66, top: 94, width: 20, height: 4, max: .03, kind: "footer-center" },
              { key: "footerRight", left: 87, top: 94, width: 9, height: 4, max: .03, kind: "footer-right" },
            ];
        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `ty-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `darkbritonthankyou32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.kind === "copy" ? 12 : 18,
            tracking: row.kind.includes("footer") || row.kind === "eyebrow" ? .12 : -.025,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f7f5ef", "#111012"),
          window.SupportLayout.contrast("#f7f5ef", "#861d29"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createHailCrash() {
    const defaults = {
      eyebrow: "DARK BRITON · TYPE SPECIMEN",
      hail: "HAIL",
      crash: "CRASH",
      cardTitle: "THORNY",
      cardLineOne: "CONCEPTS ARE THE ABSTRACT IDEAS",
      cardLineTwo: "PHENOMENA THAT ARE BEING STUDIED",
      callout: "CAN'T EVEN STAND STILL",
      status: "RESTRICTED",
      footerTitle: "EXTRAORDINARY",
      glyphCount: "789 GLYPHS",
      footerCopy: "A CHILD'S EDUCATION",
    };
    const design = {
      id: "hailcrash32",
      title: "Hail Crash specimen poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "eyebrow", type: "text", label: "Top label" },
        { key: "hail", type: "text", label: "Headline line one" },
        { key: "crash", type: "text", label: "Headline line two" },
        { key: "cardTitle", type: "text", label: "Specimen card title" },
        { key: "cardLineOne", type: "text", label: "Specimen card line one" },
        { key: "cardLineTwo", type: "text", label: "Specimen card line two" },
        { key: "callout", type: "text", label: "Callout" },
        { key: "status", type: "text", label: "Category label" },
        { key: "footerTitle", type: "text", label: "Footer title" },
        { key: "glyphCount", type: "text", label: "Glyph count" },
        { key: "footerCopy", type: "text", label: "Footer copy" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "White specimen lettering sits on charcoal and the source's dark red photographic texture; text on the paper card is near-black.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-hail-crash");
        board.classList.toggle("hail-crash-square", square);
        board.replaceChildren();

        const artFrame = document.createElement("div");
        artFrame.className = "hc-art-frame";
        artFrame.setAttribute("aria-hidden", "true");
        const image = document.createElement("img");
        image.className = "hc-art-image";
        image.src = "../../../support-references/originals/reference-batch-2026-10-29-a/T25802_09.jpg";
        image.alt = "";
        artFrame.append(image);
        board.append(artFrame);

        const paperCard = document.createElement("div");
        paperCard.className = "hc-card-paper";
        paperCard.setAttribute("aria-hidden", "true");
        board.append(paperCard);
        const redRule = document.createElement("div");
        redRule.className = "hc-red-rule";
        redRule.setAttribute("aria-hidden", "true");
        board.append(redRule);

        const globe = svgNode("svg", { class: "hc-globe", viewBox: "0 0 100 100", "aria-hidden": "true" });
        globe.innerHTML = '<circle cx="50" cy="50" r="42"/><ellipse cx="50" cy="50" rx="19" ry="42"/><path d="M10 36h80M8 50h84M12 65h76M50 8v84"/>';
        board.append(globe);

        const barcode = svgNode("svg", { class: "hc-barcode", viewBox: "0 0 240 54", preserveAspectRatio: "none", "aria-hidden": "true" });
        for (let x = 4; x < 236; x += 5) {
          const width = x % 4 === 0 ? 2.8 : x % 3 === 0 ? 1.9 : 1;
          barcode.append(svgNode("rect", { x, y: 2, width, height: 50 }));
        }
        board.append(barcode);

        const rows = square
          ? [
              { key: "eyebrow", left: 6, top: 3, width: 88, height: 4, max: .032, min: 16, kind: "eyebrow" },
              { key: "hail", left: 6, top: 48, width: 39, height: 16, max: .19, min: 24, kind: "title" },
              { key: "crash", left: 45, top: 48, width: 49, height: 16, max: .19, min: 24, kind: "title" },
              { key: "cardTitle", left: 8, top: 69, width: 26, height: 5, max: .052, min: 16, kind: "card-title" },
              { key: "cardLineOne", left: 18, top: 77, width: 30, height: 4, max: .027, min: 11, kind: "card-copy" },
              { key: "cardLineTwo", left: 18, top: 82, width: 30, height: 4, max: .027, min: 11, kind: "card-copy" },
              { key: "callout", left: 55, top: 69, width: 39, height: 5, max: .045, min: 13, kind: "callout" },
              { key: "status", left: 55, top: 78, width: 39, height: 5, max: .048, min: 14, kind: "status" },
              { key: "footerTitle", left: 6, top: 91, width: 33, height: 4, max: .034, min: 12, kind: "footer-title" },
              { key: "glyphCount", left: 42, top: 91, width: 19, height: 4, max: .034, min: 12, kind: "footer-count" },
              { key: "footerCopy", left: 63, top: 91, width: 31, height: 4, max: .027, min: 10, kind: "footer-copy" },
            ]
          : [
              { key: "eyebrow", left: 55, top: 8, width: 39, height: 5, max: .038, min: 18, kind: "eyebrow" },
              { key: "hail", left: 55, top: 14, width: 39, height: 13, max: .17, min: 26, kind: "title" },
              { key: "crash", left: 53, top: 27, width: 42, height: 22, max: .245, min: 28, kind: "title" },
              { key: "cardTitle", left: 20, top: 55, width: 22, height: 6, max: .058, min: 18, kind: "card-title" },
              { key: "cardLineOne", left: 20, top: 63, width: 24, height: 5, max: .035, min: 12, kind: "card-copy" },
              { key: "cardLineTwo", left: 20, top: 69, width: 24, height: 5, max: .035, min: 12, kind: "card-copy" },
              { key: "callout", left: 51, top: 56, width: 42, height: 7, max: .058, min: 18, kind: "callout" },
              { key: "status", left: 51, top: 65, width: 42, height: 7, max: .062, min: 18, kind: "status" },
              { key: "footerTitle", left: 5, top: 87, width: 27, height: 5, max: .04, min: 16, kind: "footer-title" },
              { key: "glyphCount", left: 35, top: 87, width: 15, height: 5, max: .04, min: 15, kind: "footer-count" },
              { key: "footerCopy", left: 55, top: 87, width: 40, height: 5, max: .031, min: 11, kind: "footer-copy" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `hc-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `hailcrash32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: row.kind.includes("footer") || row.kind === "eyebrow" || row.kind === "status" ? .08 : -.035,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f4f1ea", "#121012"),
          window.SupportLayout.contrast("#121012", "#f4f1ea"),
          window.SupportLayout.contrast("#fffaf3", "#b82537"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createAwakePortrait() {
    const defaults = {
      signature: "CLEWSE®",
      headline: "AWAKE",
      categoryOne: "BLACKLETTER",
      categoryTwo: "TYPEFACE",
      year: "MMXXVIII",
    };
    const design = {
      id: "awakeportrait32",
      title: "Awake portrait specimen",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "signature", type: "text", label: "Signature" },
        { key: "headline", type: "text", label: "Headline" },
        { key: "categoryOne", type: "text", label: "First category label" },
        { key: "categoryTwo", type: "text", label: "Second category label" },
        { key: "year", type: "text", label: "Year" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "The editable headline uses the source's pale pink on deep charcoal; pale ivory labels sit on the same dark field.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-awake-portrait");
        board.classList.toggle("awake-portrait-square", square);
        board.replaceChildren();

        const frame = document.createElement("div");
        frame.className = "ap-image-frame";
        frame.setAttribute("aria-hidden", "true");
        const image = document.createElement("img");
        image.className = "ap-image";
        image.src = "../../../support-references/materials/reference-batch-2026-10-29-a/T18400_00_awake-cleaned-background.png";
        image.alt = "";
        frame.append(image);

        const photoHeadline = document.createElement("div");
        photoHeadline.className = "ap-photo-headline";
        photoHeadline.textContent = String(state.headline ?? defaults.headline);
        photoHeadline.dataset.layoutItem = "awakeportrait32-headline-photo";
        photoHeadline.dataset.displayItem = "true";
        frame.append(photoHeadline);
        board.append(frame);

        window.SupportLayout.fitLine(photoHeadline, {
          width: frame.clientWidth * .57,
          height: frame.clientHeight * .27,
          maxSize: frame.clientHeight * .30 * scale,
          minSize: 28,
          tracking: -.035,
        });

        const rule = document.createElement("div");
        rule.className = "ap-rule";
        rule.setAttribute("aria-hidden", "true");
        board.append(rule);

        const pillOne = document.createElement("div");
        pillOne.className = "ap-pill ap-pill-one";
        pillOne.setAttribute("aria-hidden", "true");
        board.append(pillOne);
        const pillTwo = document.createElement("div");
        pillTwo.className = "ap-pill ap-pill-two";
        pillTwo.setAttribute("aria-hidden", "true");
        board.append(pillTwo);

        const rows = square
          ? [
              { key: "signature", left: 30, top: 2.8, width: 40, height: 4, max: .036, min: 16, kind: "signature" },
              { key: "categoryOne", left: 14, top: 85, width: 33, height: 5, max: .036, min: 13, kind: "category-one" },
              { key: "categoryTwo", left: 53, top: 85, width: 33, height: 5, max: .036, min: 13, kind: "category-two" },
              { key: "year", left: 35, top: 93, width: 30, height: 3.5, max: .036, min: 13, kind: "year" },
            ]
          : [
              { key: "signature", left: 66, top: 13, width: 30, height: 5, max: .042, min: 18, kind: "signature" },
              { key: "categoryOne", left: 66, top: 52, width: 14, height: 6, max: .034, min: 13, kind: "category-one" },
              { key: "categoryTwo", left: 82, top: 52, width: 14, height: 6, max: .034, min: 13, kind: "category-two" },
              { key: "year", left: 6, top: 75, width: 52, height: 7, max: .056, min: 15, kind: "year" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `ap-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `awakeportrait32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: row.kind.startsWith("category") ? .12 : row.kind === "signature" ? .1 : -.035,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f5e9e9", "#171316"),
          window.SupportLayout.contrast("#efadc7", "#171316"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createPixelLedger() {
    const defaults = {
      topLeft: "BENEDICT",
      topRight: "BLOGGS",
      secondLeft: "LAPHINE",
      secondRight: "VACLAV",
      numerals: "1263",
      footerLeft: "peter",
      footerMiddle: "pantinker",
      footerRight: "bell",
    };
    const design = {
      id: "pixelledger32",
      title: "Pixel specimen ledger",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "topLeft", type: "text", label: "Top line left" },
        { key: "topRight", type: "text", label: "Top line right" },
        { key: "secondLeft", type: "text", label: "Second line left" },
        { key: "secondRight", type: "text", label: "Second line right" },
        { key: "numerals", type: "text", label: "Large numeral specimen" },
        { key: "footerLeft", type: "text", label: "Footer left" },
        { key: "footerMiddle", type: "text", label: "Footer middle" },
        { key: "footerRight", type: "text", label: "Footer right" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "Cream and vivid teal type are rendered directly on the source's black background.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-pixel-ledger");
        board.classList.toggle("pixel-ledger-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "topLeft", left: 7, top: 6, width: 48, height: 8, max: .09, min: 20, kind: "top-left" },
              { key: "topRight", left: 57, top: 6, width: 36, height: 8, max: .09, min: 20, kind: "top-right" },
              { key: "secondLeft", left: 7, top: 15, width: 48, height: 8, max: .09, min: 20, kind: "second-left" },
              { key: "secondRight", left: 57, top: 15, width: 36, height: 8, max: .09, min: 20, kind: "second-right" },
              { key: "numerals", left: 7, top: 29, width: 86, height: 36, max: .34, min: 44, kind: "numerals" },
              { key: "footerLeft", left: 7, top: 78, width: 20, height: 9, max: .095, min: 20, kind: "footer-left" },
              { key: "footerMiddle", left: 29, top: 78, width: 42, height: 9, max: .095, min: 20, kind: "footer-middle" },
              { key: "footerRight", left: 73, top: 78, width: 20, height: 9, max: .095, min: 20, kind: "footer-right" },
            ]
          : [
              { key: "topLeft", left: 7, top: 12, width: 48, height: 8, max: .09, min: 20, kind: "top-left" },
              { key: "topRight", left: 57, top: 12, width: 36, height: 8, max: .09, min: 20, kind: "top-right" },
              { key: "secondLeft", left: 7, top: 26, width: 48, height: 8, max: .09, min: 20, kind: "second-left" },
              { key: "secondRight", left: 57, top: 26, width: 36, height: 8, max: .09, min: 20, kind: "second-right" },
              { key: "numerals", left: 7, top: 39, width: 86, height: 37, max: .36, min: 48, kind: "numerals" },
              { key: "footerLeft", left: 7, top: 82, width: 20, height: 8, max: .09, min: 20, kind: "footer-left" },
              { key: "footerMiddle", left: 29, top: 82, width: 42, height: 8, max: .09, min: 20, kind: "footer-middle" },
              { key: "footerRight", left: 73, top: 82, width: 20, height: 8, max: .09, min: 20, kind: "footer-right" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `pl-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `pixelledger32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: row.kind.includes("footer") ? -.035 : -.045,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#fff2e8", "#000000"),
          window.SupportLayout.contrast("#00aa88", "#000000"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createWineVintage() {
    const defaults = {
      topLine: "PRODUCED & BOTTLED BY",
      brand: "EREWHON",
      origin: "WINES, WAIPARA, NZ",
      vintage: "+2014+",
      footer: "PRODUCT OF NEW ZEALAND",
    };
    const design = {
      id: "winevintage32",
      title: "Waipara vintage label",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "topLine", type: "text", label: "Production line" },
        { key: "brand", type: "text", label: "Wine label name" },
        { key: "origin", type: "text", label: "Origin line" },
        { key: "vintage", type: "text", label: "Vintage year" },
        { key: "footer", type: "text", label: "Country of origin" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "Near-black and deep teal lettering sit on a warm cream label field.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-wine-vintage");
        board.classList.toggle("wine-vintage-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "topLine", left: 8, top: 8, width: 84, height: 7, max: .062, min: 18, kind: "top-line" },
              { key: "brand", left: 5, top: 19, width: 90, height: 18, max: .19, min: 30, kind: "brand" },
              { key: "origin", left: 8, top: 39, width: 84, height: 8, max: .078, min: 18, kind: "origin" },
              { key: "vintage", left: 7, top: 51, width: 86, height: 23, max: .26, min: 36, kind: "vintage" },
              { key: "footer", left: 8, top: 83, width: 84, height: 8, max: .078, min: 18, kind: "footer" },
            ]
          : [
              { key: "topLine", left: 7, top: 14, width: 86, height: 8, max: .082, min: 20, kind: "top-line" },
              { key: "brand", left: 5, top: 25, width: 90, height: 18, max: .21, min: 32, kind: "brand" },
              { key: "origin", left: 7, top: 47, width: 86, height: 8, max: .085, min: 20, kind: "origin" },
              { key: "vintage", left: 7, top: 61, width: 86, height: 24, max: .29, min: 40, kind: "vintage" },
              { key: "footer", left: 7, top: 88, width: 86, height: 7, max: .072, min: 18, kind: "footer" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `wv-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `winevintage32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: row.kind === "brand" ? -.04 : row.kind === "vintage" ? -.025 : .12,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#151313", "#fff1e8"),
          window.SupportLayout.contrast("#00765e", "#fff1e8"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createBlackgold() {
    const defaults = {
      brand: "YWFT BLACKGOLD",
      descriptor: "A BITMAP TYPEFACE DESIGN",
      firstLine: "BLACK",
      secondLine: "GOLD",
      credit: "DESIGNED BY YOUWORKFORTHEM",
      format: "OPENTYPE",
    };
    const design = {
      id: "blackgold32",
      title: "Blackgold bitmap specimen",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "brand", type: "text", label: "Typeface name" },
        { key: "descriptor", type: "text", label: "Descriptor" },
        { key: "firstLine", type: "text", label: "First display line" },
        { key: "secondLine", type: "text", label: "Second display line" },
        { key: "credit", type: "text", label: "Designer credit" },
        { key: "format", type: "text", label: "Format" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "The teal-to-cream headline gradient and ivory metadata sit directly on the source's black field.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-blackgold");
        board.classList.toggle("blackgold-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "brand", left: 7, top: 5, width: 86, height: 6, max: .052, min: 17, kind: "brand" },
              { key: "descriptor", left: 7, top: 12, width: 86, height: 6, max: .05, min: 16, kind: "descriptor" },
              { key: "firstLine", left: 6, top: 22, width: 88, height: 25, max: .28, min: 42, kind: "headline-one" },
              { key: "secondLine", left: 6, top: 49, width: 88, height: 25, max: .28, min: 42, kind: "headline-two" },
              { key: "credit", left: 7, top: 88, width: 60, height: 6, max: .052, min: 16, kind: "credit" },
              { key: "format", left: 71, top: 88, width: 22, height: 6, max: .052, min: 16, kind: "format" },
            ]
          : [
              { key: "brand", left: 7, top: 7, width: 42, height: 6, max: .05, min: 16, kind: "brand" },
              { key: "descriptor", left: 54, top: 7, width: 39, height: 6, max: .05, min: 16, kind: "descriptor" },
              { key: "firstLine", left: 6, top: 22, width: 88, height: 27, max: .31, min: 46, kind: "headline-one" },
              { key: "secondLine", left: 6, top: 50, width: 88, height: 27, max: .31, min: 46, kind: "headline-two" },
              { key: "credit", left: 7, top: 88, width: 60, height: 6, max: .05, min: 16, kind: "credit" },
              { key: "format", left: 71, top: 88, width: 22, height: 6, max: .05, min: 16, kind: "format" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `bg-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `blackgold32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: row.kind.startsWith("headline") ? -.045 : .08,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#fff5ed", "#000000"),
          window.SupportLayout.contrast("#00a888", "#000000"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createHongKongCrisis() {
    const defaults = {
      marker: "#921*",
      location: "HONG KONG",
      headline: "CRISIS",
    };
    const design = {
      id: "hongkongcrisis32",
      title: "Hong Kong crisis display",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "marker", type: "text", label: "Top glyph line" },
        { key: "location", type: "text", label: "Location line" },
        { key: "headline", type: "text", label: "Main headline" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "White source lettering is set on a saturated violet-blue field.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-hongkong-crisis");
        board.classList.toggle("hongkong-crisis-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "marker", left: 3, top: 7, width: 94, height: 22, max: .24, min: 40, kind: "marker" },
              { key: "location", left: 3, top: 31, width: 94, height: 24, max: .23, min: 40, kind: "location" },
              { key: "headline", left: 3, top: 61, width: 94, height: 24, max: .24, min: 40, kind: "headline" },
            ]
          : [
              { key: "marker", left: 2, top: 5, width: 96, height: 27, max: .3, min: 46, kind: "marker" },
              { key: "location", left: 2, top: 35, width: 96, height: 26, max: .29, min: 46, kind: "location" },
              { key: "headline", left: 2, top: 66, width: 96, height: 27, max: .3, min: 46, kind: "headline" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `hk-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `hongkongcrisis32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: row.kind === "location" ? -.06 : -.045,
          });
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#fffdf7", "#2b08d8");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createCaves465() {
    const defaults = {
      title: "CAVES:465",
      subtitle: "TO OSLO FROM ICELAND",
      year: "1983",
      finalLine: "KITCHEN SINK",
    };
    const design = {
      id: "caves46532",
      title: "Caves 465 text poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "title", type: "text", label: "Main title" },
        { key: "subtitle", type: "text", label: "Subtitle" },
        { key: "year", type: "text", label: "Year" },
        { key: "finalLine", type: "text", label: "Bottom line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 4.5,
        rationale: "Solid black specimen lettering sits on a pale white field, matching the source's stark contrast.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-caves-465");
        board.classList.toggle("caves-465-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "title", left: 4, top: 17, width: 92, height: 16, max: .18, min: 28, kind: "title" },
              { key: "subtitle", left: 5, top: 37, width: 90, height: 9, max: .087, min: 18, kind: "subtitle" },
              { key: "year", left: 8, top: 51, width: 84, height: 17, max: .19, min: 34, kind: "year" },
              { key: "finalLine", left: 5, top: 73, width: 90, height: 14, max: .15, min: 26, kind: "final-line" },
            ]
          : [
              { key: "title", left: 4, top: 25, width: 92, height: 17, max: .19, min: 30, kind: "title" },
              { key: "subtitle", left: 5, top: 45, width: 90, height: 9, max: .09, min: 18, kind: "subtitle" },
              { key: "year", left: 8, top: 58, width: 84, height: 18, max: .2, min: 34, kind: "year" },
              { key: "finalLine", left: 5, top: 78, width: 90, height: 12, max: .15, min: 26, kind: "final-line" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `c465-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `caves46532-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: row.kind === "subtitle" ? -.035 : -.06,
          });
        });
      },
      getContrast() {
        return window.SupportLayout.contrast("#111111", "#faf9f7");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createYabbaDabbaDoo() {
    const defaults = {
      firstLine: "YABBA",
      secondLine: "DABBA",
      thirdLine: "DO!",
    };
    const design = {
      id: "yabbadabbadoo32",
      title: "Yabba Dabba Do display poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "firstLine", type: "text", label: "First line" },
        { key: "secondLine", type: "text", label: "Second line" },
        { key: "thirdLine", type: "text", label: "Third line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 3,
        rationale: "The source uses extra-large violet lettering on black; the violet was lifted slightly for better large-display contrast while retaining the electric blue-violet palette. The white final line remains high contrast.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-yabba-dabba-doo");
        board.classList.toggle("yabba-dabba-doo-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { key: "firstLine", left: 5, top: 5, width: 90, height: 23, max: .23, min: 42, kind: "first-line" },
              { key: "secondLine", left: 5, top: 22, width: 90, height: 23, max: .23, min: 42, kind: "second-line" },
              { key: "thirdLine", left: 5, top: 43, width: 90, height: 52, max: .62, min: 48, kind: "third-line" },
            ]
          : [
              { key: "firstLine", left: 5, top: 3, width: 90, height: 25, max: .25, min: 44, kind: "first-line" },
              { key: "secondLine", left: 5, top: 24, width: 90, height: 25, max: .25, min: 44, kind: "second-line" },
              { key: "thirdLine", left: 5, top: 52, width: 90, height: 43, max: .58, min: 52, kind: "third-line" },
            ];

        rows.forEach((row) => {
          const item = document.createElement("div");
          item.className = `ydd-${row.kind}`;
          item.style.left = `${row.left}%`;
          item.style.top = `${row.top}%`;
          item.style.width = `${row.width}%`;
          item.style.height = `${row.height}%`;
          item.textContent = String(state[row.key] ?? defaults[row.key]);
          item.dataset.layoutItem = `yabbadabbadoo32-${row.key}`;
          item.dataset.displayItem = "true";
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * row.width / 100,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: -.025,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#fffdf9", "#181818"),
          window.SupportLayout.contrast("#6040ff", "#181818"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createChoosingHappiness() {
    const defaults = {
      firstLead: "I am",
      firstAccent: "in charge",
      secondLead: "of",
      secondAccent: "how I",
      thirdLead: "feel",
      thirdAccent: "and today",
      fourthLead: "I am",
      fourthAccent: "choosing",
      finalLine: "happiness",
    };
    const design = {
      id: "choosinghappiness32",
      title: "Choosing happiness quote poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "firstLead", type: "text", label: "Opening words" },
        { key: "firstAccent", type: "text", label: "First line accent" },
        { key: "secondLead", type: "text", label: "Second line lead" },
        { key: "secondAccent", type: "text", label: "Second line accent" },
        { key: "thirdLead", type: "text", label: "Third line lead" },
        { key: "thirdAccent", type: "text", label: "Third line accent" },
        { key: "fourthLead", type: "text", label: "Fourth line lead" },
        { key: "fourthAccent", type: "text", label: "Fourth line accent" },
        { key: "finalLine", type: "text", label: "Closing word" },
        { key: "displayScale", label: "Display scale", min: .86, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-choosing-happiness");
        board.classList.toggle("choosing-happiness-square", square);
        board.replaceChildren();

        const rows = square
          ? [
              { segments: [["firstLead", "sea", true], ["firstAccent", "peach"]], top: 4, height: 14.5, max: .155, min: 28 },
              { segments: [["secondLead", "peach", true], ["secondAccent", "ivory"]], top: 20, height: 14.5, max: .155, min: 28 },
              { segments: [["thirdLead", "ivory", true], ["thirdAccent", "orange"]], top: 36, height: 14.5, max: .155, min: 28 },
              { segments: [["fourthLead", "sea", true], ["fourthAccent", "sea"]], top: 52, height: 14.5, max: .155, min: 28 },
              { segments: [["finalLine", "orange"]], top: 69, height: 23, max: .225, min: 32 },
            ]
          : [
              { segments: [["firstLead", "sea", true], ["firstAccent", "peach"]], top: 3, height: 17, max: .185, min: 28 },
              { segments: [["secondLead", "peach", true], ["secondAccent", "ivory"]], top: 21, height: 16, max: .175, min: 28 },
              { segments: [["thirdLead", "ivory", true], ["thirdAccent", "orange"]], top: 38, height: 16, max: .175, min: 28 },
              { segments: [["fourthLead", "sea", true], ["fourthAccent", "sea"]], top: 55, height: 16, max: .175, min: 28 },
              { segments: [["finalLine", "orange"]], top: 73, height: 23, max: .225, min: 32 },
            ];

        rows.forEach((row, index) => {
          const item = document.createElement("div");
          item.className = `ch-row ch-row-${index + 1}`;
          item.style.left = "3.5%";
          item.style.top = `${row.top}%`;
          item.style.width = "93%";
          item.style.height = `${row.height}%`;
          item.dataset.layoutItem = `choosinghappiness32-row-${index + 1}`;
          item.dataset.displayItem = "true";
          row.segments.forEach(([key, color, spaceAfter]) => {
            const segment = document.createElement("span");
            segment.className = `ch-${color}`;
            segment.textContent = `${String(state[key] ?? defaults[key])}${spaceAfter ? " " : ""}`;
            item.append(segment);
          });
          board.append(item);
          window.SupportLayout.fitLine(item, {
            width: board.clientWidth * .93,
            height: board.clientHeight * row.height / 100,
            maxSize: board.clientHeight * row.max * scale,
            minSize: row.min,
            tracking: -.045,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#aadbd4", "#07162d"),
          window.SupportLayout.contrast("#f2b7a9", "#07162d"),
          window.SupportLayout.contrast("#fff9ed", "#07162d"),
          window.SupportLayout.contrast("#ff9b32", "#07162d"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createFatKillKat() {
    const defaults = {
      mainWord: "FAT",
      firstBottom: "KILLY",
      secondBottom: "KAT",
    };
    const design = {
      id: "fatkillkat32",
      title: "Fat Killy Kat textured display poster",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1, extrusion: 1 },
      controls: [
        { key: "mainWord", type: "text", label: "Main word" },
        { key: "firstBottom", type: "text", label: "Lower left word" },
        { key: "secondBottom", type: "text", label: "Lower right word" },
        { key: "displayScale", label: "Display scale", min: .86, max: 1.12, step: .01 },
        { key: "extrusion", label: "Blue extrusion", min: .55, max: 1.5, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        const extrusion = Number(state.extrusion ?? 1);
        board.classList.add("user-reference-fat-kill-kat");
        board.classList.toggle("fat-kill-kat-square", square);
        board.style.setProperty("--fkk-extrusion-x", `${8 * extrusion}px`);
        board.style.setProperty("--fkk-extrusion-y", `${10 * extrusion}px`);
        board.replaceChildren();

        const title = document.createElement("div");
        title.className = "fkk-title";
        title.style.left = "10%";
        title.style.top = "7%";
        title.style.width = "80%";
        title.style.height = "52%";
        const mainWord = String(state.mainWord ?? defaults.mainWord);
        const extrusionWord = document.createElement("span");
        extrusionWord.className = "fkk-title-extrusion";
        extrusionWord.textContent = mainWord;
        const faceWord = document.createElement("span");
        faceWord.className = "fkk-title-face";
        faceWord.textContent = mainWord;
        faceWord.dataset.layoutItem = "fatkillkat32-main-word";
        faceWord.dataset.displayItem = "true";
        title.append(extrusionWord, faceWord);
        board.append(title);

        const footer = document.createElement("div");
        footer.className = "fkk-footer";
        footer.style.left = square ? "5%" : "6%";
        footer.style.top = square ? "57%" : "55%";
        footer.style.width = square ? "90%" : "88%";
        footer.style.height = square ? "23%" : "24%";
        footer.dataset.layoutItem = "fatkillkat32-footer";
        footer.dataset.displayItem = "true";
        const left = document.createElement("span");
        left.className = "fkk-lower-blue";
        left.textContent = `${String(state.firstBottom ?? defaults.firstBottom)}  `;
        footer.append(left);
        const right = document.createElement("span");
        right.className = "fkk-lower-cream";
        right.textContent = String(state.secondBottom ?? defaults.secondBottom);
        footer.append(right);
        board.append(footer);

        window.SupportLayout.fitLine(faceWord, {
          width: board.clientWidth * .78,
          height: board.clientHeight * .52,
          maxSize: board.clientHeight * .50 * scale,
          minSize: 40,
          tracking: -.025,
        });
        extrusionWord.style.fontSize = getComputedStyle(faceWord).fontSize;
        window.SupportLayout.fitLine(footer, {
          width: board.clientWidth * (square ? .90 : .88),
          height: board.clientHeight * (square ? .23 : .24),
          maxSize: board.clientHeight * (square ? .25 : .27) * scale,
          minSize: 36,
          tracking: -.065,
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#ffb848", "#07162d"),
          window.SupportLayout.contrast("#91d5d4", "#07162d"),
          window.SupportLayout.contrast("#fff9ec", "#07162d"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  window.UserReferenceBatchM = {
    ids: ["prettyinpink32", "dynamicplayful32", "retroshowcase32", "iconicposter32", "summerparadise32", "calgarywelcome32", "latinmaxims32", "onlygooddieyoung32", "blackholesun32", "somethingabouther32", "darknightbrighterday32", "tc-panthoma-specimen32", "tcpanthomarepeat32", "strongerquote32", "scarygangsta32", "darkbriton32", "darkbritonthankyou32", "hailcrash32", "awakeportrait32", "pixelledger32", "winevintage32", "blackgold32", "hongkongcrisis32", "caves46532", "yabbadabbadoo32", "choosinghappiness32", "fatkillkat32"],
    create(id) {
      if (id === "prettyinpink32") return createPrettyInPink();
      if (id === "dynamicplayful32") return createDynamicPlayful();
      if (id === "retroshowcase32") return createRetroShowcase();
      if (id === "iconicposter32") return createIconicPoster();
      if (id === "summerparadise32") return createSummerParadise();
      if (id === "calgarywelcome32") return createCalgaryWelcome();
      if (id === "latinmaxims32") return createLatinMaxims();
      if (id === "onlygooddieyoung32") return createOnlyGoodDieYoung();
      if (id === "blackholesun32") return createBlackHoleSun();
      if (id === "somethingabouther32") return createSomethingAboutHer();
      if (id === "darknightbrighterday32") return createDarkNightBrighterDay();
      if (id === "tc-panthoma-specimen32") return createTcPanthomaSpecimen();
      if (id === "tcpanthomarepeat32") return createTcPanthomaRepeat();
      if (id === "strongerquote32") return createStrongerQuote();
      if (id === "scarygangsta32") return createScaryGangsta();
      if (id === "darkbriton32") return createDarkBritonPoster();
      if (id === "darkbritonthankyou32") return createDarkBritonThankYou();
      if (id === "hailcrash32") return createHailCrash();
      if (id === "awakeportrait32") return createAwakePortrait();
      if (id === "pixelledger32") return createPixelLedger();
      if (id === "winevintage32") return createWineVintage();
      if (id === "blackgold32") return createBlackgold();
      if (id === "hongkongcrisis32") return createHongKongCrisis();
      if (id === "caves46532") return createCaves465();
      if (id === "yabbadabbadoo32") return createYabbaDabbaDoo();
      if (id === "choosinghappiness32") return createChoosingHappiness();
      if (id === "fatkillkat32") return createFatKillKat();
      throw new Error(`Unknown reference template: ${id}`);
    },
  };
})();
