(function () {
  const rows = [
    [{ key: "lineOneLead", value: "This book" }, { key: "lineOneAccent", value: "Read", accent: true }],
    [{ key: "lineTwoAccent", value: "naked", accent: true }, { key: "lineTwoLead", value: "remind" }],
    [{ key: "lineThree", value: "me about my" }],
    [{ key: "lineFour", value: "Childhood..." }],
  ];

  function createChildhoodBook() {
    const defaults = Object.fromEntries(rows.flat().map(({ key, value }) => [key, value]));
    const design = {
      id: "childhoodbook32",
      title: "This Book Childhood display specimen",
      literalKeys: Object.keys(defaults),
      defaults: { ...defaults, displayScale: 1 },
      controls: [
        { key: "lineOneLead", type: "text", label: "First line · black copy" },
        { key: "lineOneAccent", type: "text", label: "First line · orange word" },
        { key: "lineTwoAccent", type: "text", label: "Second line · orange word" },
        { key: "lineTwoLead", type: "text", label: "Second line · black copy" },
        { key: "lineThree", type: "text", label: "Third line" },
        { key: "lineFour", type: "text", label: "Fourth line" },
        { key: "displayScale", label: "Display scale", min: .8, max: 1.12, step: .01 },
      ],
      contrastException: {
        minimum: 2.9,
        rationale: "The source uses vivid orange emphasis on white; keeping its sampled orange preserves the original two-ink lettering treatment.",
      },
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-childhoodbook");
        board.replaceChildren();
        const elements = [];
        const rowTops = [1, 25, 49, 73];

        rows.forEach((parts, index) => {
          const line = document.createElement("div");
          line.className = `cb-line cb-line-${index + 1}`;
          line.style.top = `${rowTops[index]}%`;
          line.dataset.layoutItem = `childhoodbook32-line-${index + 1}`;
          line.dataset.displayItem = "true";
          line.dataset.supportStackGroup = "childhoodbook32-quote";
          line.dataset.supportStackIndex = String(index);
          parts.forEach((part, partIndex) => {
            if (partIndex > 0) line.append(document.createTextNode(" "));
            const span = document.createElement("span");
            span.className = part.accent ? "cb-accent" : "cb-ink";
            span.textContent = String(state[part.key] ?? part.value);
            line.append(span);
          });
          board.append(line);
          elements.push(line);
        });

        window.SupportLayout.fitLinesTogether(elements, {
          width: board.clientWidth * (square ? .93 : .97),
          height: board.clientHeight * .22,
          maxSize: board.clientHeight * (square ? .16 : .205) * scale,
          minSize: 38,
          tracking: -.035,
        });
      },
      getContrast() {
        return Math.min(
          window.SupportLayout.contrast("#000000", "#ffffff"),
          window.SupportLayout.contrast("#ff6400", "#ffffff"),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  window.UserReferenceBatchG = {
    ids: ["childhoodbook32"],
    create(id) {
      if (id !== "childhoodbook32") throw new Error(`Unknown reference template: ${id}`);
      return createChildhoodBook();
    },
  };
})();
