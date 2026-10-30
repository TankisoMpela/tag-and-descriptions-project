(function () {
  const config = {
    brandCredit: "Yukas",
    monogram: "Q",
    headline: "Player",
    secondLine: "your game",
    thirdLine: "manifestation",
  };

  function createPlayerGlyph() {
    const design = {
      id: "playerglyph32",
      title: "Player display specimen",
      literalKeys: ["brandCredit", "monogram", "headline", "secondLine", "thirdLine"],
      defaults: { ...config, displayScale: 1 },
      controls: [
        { key: "brandCredit", type: "text", label: "Top credit" },
        { key: "monogram", type: "text", label: "Featured glyph" },
        { key: "headline", type: "text", label: "Display line one" },
        { key: "secondLine", type: "text", label: "Display line two" },
        { key: "thirdLine", type: "text", label: "Display line three" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 1.8,
        rationale: "The source uses a pale pink Q inside a vivid pink block; these sampled brand colors preserve that original two-pink glyph treatment.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-playerglyph");
        board.classList.toggle("playerglyph-square", square);
        board.replaceChildren();

        const credit = document.createElement("div");
        credit.className = "pg-credit";
        credit.textContent = String(state.brandCredit ?? config.brandCredit);
        credit.dataset.layoutItem = "playerglyph32-brandCredit";
        credit.dataset.displayItem = "true";
        board.append(credit);
        window.SupportLayout.fitLine(credit, {
          width: board.clientWidth * (square ? .26 : .24),
          height: board.clientHeight * (square ? .09 : .14),
          maxSize: board.clientHeight * (square ? .145 : .18) * scale,
          minSize: 38,
          tracking: -.02,
        });

        const panel = document.createElement("div");
        panel.className = "pg-glyph-panel";
        panel.dataset.layoutItem = "playerglyph32-glyph-panel";
        board.append(panel);

        const monogram = document.createElement("div");
        monogram.className = "pg-monogram";
        monogram.textContent = String(state.monogram ?? config.monogram);
        monogram.dataset.layoutItem = "playerglyph32-monogram";
        monogram.dataset.displayItem = "true";
        panel.append(monogram);
        window.SupportLayout.fitLine(monogram, {
          width: panel.clientWidth * .84,
          height: panel.clientHeight * .78,
          maxSize: Math.min(panel.clientHeight * .78 * scale, panel.clientHeight * .80),
          minSize: 38,
          tracking: -.02,
        });

        const lines = [
          ["headline", "pg-line pg-headline"],
          ["secondLine", "pg-line pg-second-line"],
          ["thirdLine", "pg-line pg-third-line"],
        ];
        const items = [];
        for (const [key, className] of lines) {
          const line = document.createElement("div");
          line.className = className;
          line.textContent = String(state[key] ?? config[key]);
          line.dataset.layoutItem = `playerglyph32-${key}`;
          line.dataset.displayItem = "true";
          board.append(line);
          items.push(line);
        }

        const specs = square
          ? [
              { left: 35, top: 3, width: 61, height: 25, max: .24 },
              { left: 35, top: 32, width: 61, height: 25, max: .24 },
              { left: 35, top: 61, width: 61, height: 26, max: .25 },
            ]
          : [
              { left: 34, top: 3, width: 62, height: 34, max: .36 },
              { left: 34, top: 39, width: 62, height: 28, max: .30 },
              { left: 34, top: 71, width: 62, height: 26, max: .27 },
            ];
        items.forEach((line, index) => {
          const spec = specs[index];
          line.style.left = `${spec.left}%`;
          line.style.top = `${spec.top}%`;
          line.style.width = `${spec.width}%`;
          line.style.height = `${spec.height}%`;
          window.SupportLayout.fitLine(line, {
            width: board.clientWidth * spec.width / 100 * .94,
            height: board.clientHeight * spec.height / 100 * .84,
            maxSize: board.clientHeight * spec.max * scale,
            minSize: 38,
            tracking: -.02,
          });
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#da1536", "#242328"),
          window.SupportLayout.contrast("#ed7388", "#242328"),
          window.SupportLayout.contrast("#fcb3c3", "#242328"),
          window.SupportLayout.contrast("#fcb3c3", "#fc5a78"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  window.UserReferenceBatchH = {
    ids: ["playerglyph32"],
    create(id) {
      if (id !== "playerglyph32") throw new Error(`Unknown reference template: ${id}`);
      return createPlayerGlyph();
    },
  };
})();
