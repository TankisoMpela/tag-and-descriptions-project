(function () {
  const svgNS = "http://www.w3.org/2000/svg";
  const backgroundUrl = "../../../support-references/materials/reference-batch-2026-10-26-d/T16168_01-background-3x2.png";
  const practiceBackgroundUrl = "../../../support-references/materials/reference-batch-2026-10-26-d/T16168_07-background-3x2.png";
  const rainbowBackgroundUrl = "../../../support-references/materials/reference-batch-2026-10-26-d/T19310_08-background-3x2.png";
  const wakeFamousBackgroundUrl = "../../../support-references/materials/reference-batch-2026-10-26-d/T19310_10-background-3x2.png";
  const config = {
    topLine: "NOT",
    secondLine: "all roads",
    thirdLine: "ARE",
    bottomLine: "simple,",
  };
  const lines = [
    { key: "topLine", className: "nr-not", max: .225, width: .56, tracking: .015 },
    { key: "secondLine", className: "nr-all-roads nr-italic", max: .17, width: .92, tracking: -.025 },
    { key: "thirdLine", className: "nr-are", max: .225, width: .65, tracking: .015 },
    { key: "bottomLine", className: "nr-simple nr-italic", max: .205, width: .94, tracking: -.025 },
  ];

  function createNotAllRoads() {
    const design = {
      id: "notallroads32",
      title: "Not All Roads Are Simple",
      literalKeys: ["topLine", "secondLine", "thirdLine", "bottomLine"],
      defaults: { ...config, displayScale: 1, useItalicSibling: false },
      controls: [
        { key: "topLine", type: "text", label: "Upper gold line" },
        { key: "secondLine", type: "text", label: "Upper white line" },
        { key: "thirdLine", type: "text", label: "Lower gold line" },
        { key: "bottomLine", type: "text", label: "Lower white line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-notallroads");
        board.classList.toggle("nr-square", square);
        board.replaceChildren();

        const photo = document.createElement("img");
        photo.className = "nr-photo";
        photo.src = backgroundUrl;
        photo.alt = "";
        photo.setAttribute("aria-hidden", "true");
        photo.draggable = false;
        board.append(photo);

        const italicAvailable = Boolean(
          state.useItalicSibling &&
          window.SupportFamilyAvailable?.includes("SupportFamily1"),
        );
        const items = lines.map((spec) => {
          const line = document.createElement("div");
          line.className = `nr-line ${spec.className}`;
          line.dataset.layoutItem = `notallroads32-${spec.key}`;
          line.dataset.displayItem = "true";
          line.textContent = String(state[spec.key] ?? config[spec.key]);
          if (spec.className.includes("nr-italic")) {
            line.style.fontFamily = italicAvailable ? "SupportFamily1" : "SupportDisplay";
          }
          board.append(line);
          window.SupportLayout.fitLine(line, {
            width: board.clientWidth * (square ? Math.min(spec.width + .06, .99) : spec.width),
            height: board.clientHeight * (square ? .19 : .20),
            maxSize: board.clientHeight * spec.max * scale,
            minSize: 34,
            tracking: spec.tracking,
          });
          return line;
        });
        design.headlineFontSize = `${Math.max(...items.map((item) => parseFloat(item.style.fontSize) || 0))}px`;
        design.warnings = items
          .filter((item) => item.hasAttribute("data-fit-failure"))
          .map((item) => `${item.textContent}: the minimum type size exceeds its safe area.`);
      },
      getContrast() {
        const shadowField = "#202321";
        return Math.min(
          window.SupportLayout.contrast("#f4bd38", shadowField),
          window.SupportLayout.contrast("#f7f4ed", shadowField),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createPracticeHard() {
    const defaults = {
      verbOne: "Practice", powerOne: "HARD",
      verbTwo: "Train", powerTwo: "HARD",
      verbThree: "Work", powerThree: "HARD",
      verbFour: "Play", powerFour: "HARDER",
      displayScale: 1, useItalicSibling: false,
    };
    const rows = [
      { verb: "verbOne", power: "powerOne", top: .075, left: .12, width: .79, verbShare: .48 },
      { verb: "verbTwo", power: "powerTwo", top: .275, left: .23, width: .69, verbShare: .46 },
      { verb: "verbThree", power: "powerThree", top: .475, left: .23, width: .69, verbShare: .45 },
      { verb: "verbFour", power: "powerFour", top: .675, left: .25, width: .72, verbShare: .42 },
    ];
    const design = {
      id: "practicehard32",
      title: "Practice Hard",
      literalKeys: rows.flatMap((row) => [row.verb, row.power]),
      defaults,
      controls: [
        { key: "verbOne", type: "text", label: "First verb" },
        { key: "powerOne", type: "text", label: "First emphasis" },
        { key: "verbTwo", type: "text", label: "Second verb" },
        { key: "powerTwo", type: "text", label: "Second emphasis" },
        { key: "verbThree", type: "text", label: "Third verb" },
        { key: "powerThree", type: "text", label: "Third emphasis" },
        { key: "verbFour", type: "text", label: "Fourth verb" },
        { key: "powerFour", type: "text", label: "Fourth emphasis" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        const italicAvailable = Boolean(
          state.useItalicSibling &&
          window.SupportFamilyAvailable?.includes("SupportFamily1"),
        );
        board.classList.add("user-reference-practicehard");
        board.classList.toggle("ph-square", square);
        board.replaceChildren();

        const photo = document.createElement("img");
        photo.className = "ph-photo";
        photo.src = practiceBackgroundUrl;
        photo.alt = "";
        photo.setAttribute("aria-hidden", "true");
        photo.draggable = false;
        board.append(photo);

        const fitted = [];
        rows.forEach((spec, index) => {
          const row = document.createElement("div");
          row.className = "ph-row";
          row.style.top = `${(square ? .065 + index * .19 : spec.top) * 100}%`;
          row.style.left = `${(square ? .025 + index * .012 : spec.left) * 100}%`;
          row.style.width = `${(square ? .95 - index * .018 : spec.width) * 100}%`;

          const verb = document.createElement("span");
          verb.className = "ph-word ph-verb";
          verb.dataset.layoutItem = `practicehard32-${spec.verb}`;
          verb.dataset.displayItem = "true";
          verb.textContent = String(state[spec.verb] ?? defaults[spec.verb]);
          verb.style.width = `${(square ? .47 : spec.verbShare) * 100}%`;
          verb.style.fontFamily = italicAvailable ? "SupportFamily1" : "SupportDisplay";
          row.append(verb);

          const power = document.createElement("span");
          power.className = "ph-word ph-power";
          power.dataset.layoutItem = `practicehard32-${spec.power}`;
          power.dataset.displayItem = "true";
          power.textContent = String(state[spec.power] ?? defaults[spec.power]);
          power.style.width = `${(square ? .53 : 1 - spec.verbShare) * 100}%`;
          row.append(power);
          board.append(row);

          const maxSize = board.clientHeight * (square ? .145 : .19) * scale;
          const rowHeight = board.clientHeight * .19;
          fitted.push(window.SupportLayout.fitLine(verb, {
            width: board.clientWidth * (square ? .95 - index * .018 : spec.width) *
              (square ? .47 : spec.verbShare),
            height: rowHeight,
            maxSize,
            minSize: 34,
            tracking: -.012,
          }));
          fitted.push(window.SupportLayout.fitLine(power, {
            width: board.clientWidth * (square ? .95 - index * .018 : spec.width) *
              (square ? .53 : 1 - spec.verbShare),
            height: rowHeight,
            maxSize,
            minSize: 34,
            tracking: -.012,
          }));
        });
        design.headlineFontSize = `${Math.max(...fitted)}px`;
        design.warnings = board.querySelectorAll(".ph-word[data-fit-failure]").length
          ? ["One or more words cannot fit its safe area at the minimum type size."]
          : [];
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#f4bd38", "#111416"),
          window.SupportLayout.contrast("#f7f4ed", "#111416"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createRainbowStack() {
    const defaults = {
      outlineOne: "RAINBOW", solidOne: "RAINBOW",
      outlineTwo: "RAINBOW", solidTwo: "RAINBOW",
      displayScale: 1,
    };
    const rows = [
      { key: "outlineOne", top: .005, style: "outline" },
      { key: "solidOne", top: .255, style: "solid" },
      { key: "outlineTwo", top: .515, style: "outline" },
      { key: "solidTwo", top: .765, style: "solid" },
    ];
    const design = {
      id: "rainbowstack32",
      title: "Rainbow Stack",
      literalKeys: rows.map((row) => row.key),
      defaults,
      controls: [
        { key: "outlineOne", type: "text", label: "First outline row" },
        { key: "solidOne", type: "text", label: "First solid row" },
        { key: "outlineTwo", type: "text", label: "Second outline row" },
        { key: "solidTwo", type: "text", label: "Second solid row" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-rainbowstack");
        board.classList.toggle("rs-square", square);
        board.replaceChildren();

        const photo = document.createElement("img");
        photo.className = "rs-photo";
        photo.src = rainbowBackgroundUrl;
        photo.alt = "";
        photo.setAttribute("aria-hidden", "true");
        photo.draggable = false;
        board.append(photo);

        const fitted = rows.map((spec, index) => {
          const line = document.createElement("div");
          line.className = `rs-row rs-${spec.style}`;
          line.dataset.layoutItem = `rainbowstack32-${spec.key}`;
          line.dataset.displayItem = "true";
          line.textContent = String(state[spec.key] ?? defaults[spec.key]);
          line.style.top = `${(square ? .01 + index * .245 : spec.top) * 100}%`;
          line.style.left = square ? "2%" : "1.5%";
          line.style.width = square ? "96%" : "97%";
          board.append(line);
          return window.SupportLayout.fitLine(line, {
            width: board.clientWidth * (square ? .96 : .97),
            height: board.clientHeight * .235,
            maxSize: board.clientHeight * .22 * scale,
            minSize: 34,
            tracking: -.025,
          });
        });
        design.headlineFontSize = `${Math.max(...fitted)}px`;
        design.warnings = board.querySelectorAll(".rs-row[data-fit-failure]").length
          ? ["One or more rows cannot fit its safe area at the minimum type size."]
          : [];
      },
      getContrast() {
        return window.SupportLayout.contrast("#f7f4ed", "#111111");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function createWakeFamous() {
    const defaults = {
      lineOne: "WAKE ME UP",
      lineTwo: "WHEN I'M",
      lineThree: "FAMOUS!",
      displayScale: 1,
    };
    const rows = [
      { key: "lineOne", top: .19, squareTop: .095 },
      { key: "lineTwo", top: .385, squareTop: .385 },
      { key: "lineThree", top: .645, squareTop: .675 },
    ];
    const design = {
      id: "wakefamous32",
      title: "Wake Me Up Famous",
      literalKeys: rows.map((row) => row.key),
      defaults,
      controls: [
        { key: "lineOne", type: "text", label: "First line" },
        { key: "lineTwo", type: "text", label: "Second line" },
        { key: "lineThree", type: "text", label: "Third line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-wakefamous");
        board.classList.toggle("wf-square", square);
        board.replaceChildren();

        const photo = document.createElement("img");
        photo.className = "wf-photo";
        photo.src = wakeFamousBackgroundUrl;
        photo.alt = "";
        photo.setAttribute("aria-hidden", "true");
        photo.draggable = false;
        board.append(photo);

        const frame = document.createElement("div");
        frame.className = "wf-frame";
        frame.setAttribute("aria-hidden", "true");
        board.append(frame);

        const fitted = rows.map((spec) => {
          const line = document.createElement("div");
          line.className = "wf-line";
          line.dataset.layoutItem = `wakefamous32-${spec.key}`;
          line.dataset.displayItem = "true";
          line.textContent = String(state[spec.key] ?? defaults[spec.key]);
          line.style.top = `${(square ? spec.squareTop : spec.top) * 100}%`;
          line.style.left = square ? "10%" : "14%";
          line.style.width = square ? "80%" : "72%";
          board.append(line);
          return window.SupportLayout.fitLine(line, {
            width: board.clientWidth * (square ? .80 : .72),
            height: board.clientHeight * .23,
            maxSize: board.clientHeight * (square ? .205 : .20) * scale,
            minSize: 34,
            tracking: -.018,
          });
        });
        design.headlineFontSize = `${Math.max(...fitted)}px`;
        design.warnings = board.querySelectorAll(".wf-line[data-fit-failure]").length
          ? ["One or more lines cannot fit its safe area at the minimum type size."]
          : [];
      },
      getContrast() {
        return window.SupportLayout.contrast("#f7f4ed", "#1a1411");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function bindItalicFamily(inputId, statusId, description) {
    const input = document.getElementById(inputId);
    const status = document.getElementById(statusId);
    let face = null;
    let objectUrl = "";
    input?.addEventListener("change", async () => {
      const file = input.files?.[0];
      if (!file) return;
      if (status) status.textContent = `Loading ${file.name} as the optional real Italic member…`;
      if (face) document.fonts.delete(face);
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(file);
      try {
        face = new FontFace("SupportFamily1", `url("${objectUrl}")`);
        await face.load();
        document.fonts.add(face);
        window.SupportFamilyAvailable = [...new Set([
          ...(window.SupportFamilyAvailable || []), "SupportFamily1",
        ])];
        await document.fonts.ready;
        window.configureTemplate({ useItalicSibling: true });
        if (status) status.textContent = `Loaded ${file.name}; ${description}.`;
      } catch (error) {
        window.configureTemplate({ useItalicSibling: false });
        if (status) status.textContent = `Could not load ${file.name}. Choose a valid font file.`;
      }
    });
  }

  window.UserReferenceBatchJ = {
    ids: ["notallroads32", "practicehard32", "rainbowstack32", "wakefamous32"],
    create(id) {
      if (id === "notallroads32") return createNotAllRoads();
      if (id === "practicehard32") return createPracticeHard();
      if (id === "rainbowstack32") return createRainbowStack();
      if (id === "wakefamous32") return createWakeFamous();
      throw new Error(`Unknown reference template: ${id}`);
    },
    bindItalicFamily,
  };
})();
