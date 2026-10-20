(function () {
  function splitHeadline(value) {
    const normalized = (value || "Real Madrid").replace(/\s*\n\s*/g, "\n").trim();
    if (normalized.includes("\n")) {
      const lines = normalized.split("\n").map((line) => line.trim()).filter(Boolean);
      return [lines[0] || "Real", lines[1] || "Madrid"];
    }
    const words = normalized.split(/\s+/).filter(Boolean);
    if (words.length <= 1) {
      const first = words[0] || "Real";
      return first.toLowerCase() === "madrid" ? ["Real", "Madrid"] : [first, "Madrid"];
    }
    const split = Math.ceil(words.length / 2);
    return [words.slice(0, split).join(" "), words.slice(split).join(" ")];
  }

  function addText(board, className, name, text) {
    const element = document.createElement("div");
    element.className = className;
    element.dataset.layoutItem = name;
    element.dataset.displayItem = "true";
    element.textContent = text;
    board.append(element);
    return element;
  }

  const design = {
    id: "stadiumposter32",
    title: "Stadium poster",
    defaults: { lineOne: "Real", lineTwo: "Madrid", scale: 1, tracking: -0.045 },
    controls: [
      { key: "lineOne", label: "First headline line", type: "text", value: "Real" },
      { key: "lineTwo", label: "Second headline line", type: "text", value: "Madrid" },
      { key: "scale", label: "Display scale", min: 0.78, max: 1.08, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.10, max: 0.005, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");

      const topLeft = document.createElement("div");
      topLeft.className = "stadium-meta stadium-top-left";
      topLeft.dataset.layoutItem = "stadium-top-left";
      topLeft.textContent = "YWFT Becks";
      board.append(topLeft);
      const topRight = document.createElement("div");
      topRight.className = "stadium-meta stadium-top-right";
      topRight.dataset.layoutItem = "stadium-top-right";
      topRight.textContent = "A Distressed OpenType SVG Font";
      board.append(topRight);

      const headline = props.headline;
      const [firstCopy, secondCopy] = headline !== undefined
        ? splitHeadline(headline)
        : [state.lineOne || "Real", state.lineTwo || "Madrid"];
      const lineSpecs = [
        { text: firstCopy, className: "stadium-line stadium-line-one", name: "stadium-headline-one", left: .08, top: .17, width: .84, height: .29, size: 560 },
        { text: secondCopy, className: "stadium-line stadium-line-two", name: "stadium-headline-two", left: .08, top: .52, width: .84, height: .30, size: 560 },
      ];
      for (const spec of lineSpecs) {
        const line = addText(board, spec.className, spec.name, spec.text);
        line.style.left = `${spec.left * 100}%`;
        line.style.top = `${spec.top * 100}%`;
        line.style.width = `${spec.width * 100}%`;
        line.style.height = `${spec.height * 100}%`;
        line.style.textAlign = "center";
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * spec.width * .97,
          height: board.clientHeight * spec.height * .84,
          maxSize: spec.size * state.scale,
          minSize: board.clientHeight * .12,
          tracking: state.tracking,
        });
        line.style.letterSpacing = `${state.tracking}em`;
        line.style.transform = "none";
      }

      const footerLeft = document.createElement("div");
      footerLeft.className = "stadium-footer stadium-foot-left";
      footerLeft.dataset.layoutItem = "stadium-footer-left";
      footerLeft.textContent = "Designed By YouWorkForThem";
      board.append(footerLeft);
      const footerRight = document.createElement("div");
      footerRight.className = "stadium-footer stadium-foot-right";
      footerRight.dataset.layoutItem = "stadium-footer-right";
      footerRight.textContent = "Exclusive";
      board.append(footerRight);
    },
    getContrast() { return window.SupportLayout.contrast("#f6ebda", "#b82229"); },
    getWarnings() { return design.warnings || []; },
  };
  window.StadiumPoster32 = design;
})();
