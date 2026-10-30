(function () {
  const photoUrl = "../../../support-references/materials/reference-batch-2026-10-26-f/33a5cffa-user-photo.png";
  const defaults = {
    eyebrowOne: "TYPE STUDY",
    eyebrowTwo: "DISPLAY FORM",
    headline: "Embrace",
    article: "The",
    highlight: "Sexiest",
    tagline: "with bold & simplicity",
    displayScale: 1,
  };
  const rows = [
    { key: "eyebrowOne", className: "es-small", top: .045, squareTop: .035, left: .045, squareLeft: .05, width: .34, squareWidth: .42, height: .075, squareHeight: .075, max: .046, squareMax: .044, tracking: .055 },
    { key: "eyebrowTwo", className: "es-small es-small-second", top: .112, squareTop: .104, left: .045, squareLeft: .05, width: .34, squareWidth: .42, height: .065, squareHeight: .065, max: .035, squareMax: .033, tracking: .075 },
    { key: "headline", className: "es-headline", top: .355, squareTop: .255, left: .02, squareLeft: .035, width: .94, squareWidth: .93, height: .22, squareHeight: .22, max: .30, squareMax: .22, tracking: .07, squareTracking: -.025 },
    { key: "article", className: "es-article", top: .585, squareTop: .49, left: .025, squareLeft: .035, width: .205, squareWidth: .205, height: .19, squareHeight: .19, max: .19, squareMax: .145, tracking: .01, squareTracking: -.02 },
    { key: "highlight", className: "es-highlight", top: .585, squareTop: .49, left: .235, squareLeft: .245, width: .735, squareWidth: .72, height: .19, squareHeight: .19, max: .245, squareMax: .185, tracking: .08, squareTracking: -.04 },
    { key: "tagline", className: "es-tagline", top: .79, squareTop: .735, left: .045, squareLeft: .04, width: .91, squareWidth: .92, height: .14, squareHeight: .15, max: .13, squareMax: .105, tracking: .025, squareTracking: -.015 },
  ];

  function createEmbraceSexiest() {
    const design = {
      id: "embracesexiest32",
      title: "Embrace The Sexiest",
      literalKeys: rows.map((row) => row.key),
      defaults,
      controls: [
        { key: "eyebrowOne", type: "text", label: "Top line" },
        { key: "eyebrowTwo", type: "text", label: "Second label" },
        { key: "headline", type: "text", label: "Main line" },
        { key: "article", type: "text", label: "Article" },
        { key: "highlight", type: "text", label: "Gold word" },
        { key: "tagline", type: "text", label: "Lower line" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        board.classList.add("user-reference-embracesexiest");
        board.classList.toggle("es-square", square);
        board.replaceChildren();

        const photo = document.createElement("img");
        photo.className = "es-photo";
        photo.src = photoUrl;
        photo.alt = "";
        photo.setAttribute("aria-hidden", "true");
        photo.draggable = false;
        board.append(photo);

        const fitted = rows.map((spec) => {
          const line = document.createElement("div");
          line.className = `es-line ${spec.className}`;
          line.dataset.layoutItem = `embracesexiest32-${spec.key}`;
          line.dataset.displayItem = "true";
          line.textContent = String(state[spec.key] ?? defaults[spec.key]);
          line.style.top = `${(square ? spec.squareTop : spec.top) * 100}%`;
          line.style.left = `${(square ? spec.squareLeft : spec.left) * 100}%`;
          line.style.width = `${(square ? spec.squareWidth : spec.width) * 100}%`;
          line.style.height = `${(square ? spec.squareHeight : spec.height) * 100}%`;
          board.append(line);
          return window.SupportLayout.fitLine(line, {
            width: board.clientWidth * (square ? spec.squareWidth : spec.width),
            height: board.clientHeight * (square ? spec.squareHeight : spec.height),
            maxSize: board.clientHeight * (square ? spec.squareMax : spec.max) * scale,
            minSize: 32,
            tracking: square ? (spec.squareTracking ?? spec.tracking) : spec.tracking,
          });
        });

        design.headlineFontSize = `${Math.max(...fitted.slice(2))}px`;
        design.warnings = board.querySelectorAll(".es-line[data-fit-failure]").length
          ? ["One or more lines cannot fit its safe area at the minimum type size."]
          : [];
      },
      getContrast() {
        const shadowField = "#302319";
        return Math.min(
          window.SupportLayout.contrast("#fff9ef", shadowField),
          window.SupportLayout.contrast("#e2c100", shadowField),
        );
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  window.UserReferenceBatchL = {
    ids: ["embracesexiest32"],
    create(id) {
      if (id === "embracesexiest32") return createEmbraceSexiest();
      throw new Error(`Unknown reference template: ${id}`);
    },
  };
})();
