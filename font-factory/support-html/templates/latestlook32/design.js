(function () {
  const design = {
    id: "latestlook32",
    title: "Latest look",
    labelFace: "LatestLabel",
    defaults: {
      lineOne: "Get The",
      lineTwo: "Latest",
      lineThree: "Style",
      caption: "Display Lettering",
      signature: "Autumn Lookbook",
      scale: 1,
      tracking: -0.025,
    },
    controls: [
      { key: "lineOne", label: "Opening line", type: "text", value: "Get The" },
      { key: "lineTwo", label: "Main line", type: "text", value: "Latest" },
      { key: "lineThree", label: "Closing line", type: "text", value: "Style" },
      { key: "caption", label: "Left footer caption", type: "text", value: "Display Lettering" },
      { key: "signature", label: "Right footer caption", type: "text", value: "Autumn Lookbook" },
      { key: "scale", label: "Display scale", min: 0.82, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.10, max: 0.01, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "LatestLabel");
      const lines = [
        [props.lineOne ?? state.lineOne ?? "Get The", "latest-line latest-intro", "latest-line-one", .62],
        [props.lineTwo ?? state.lineTwo ?? "Latest", "latest-line latest-headline", "latest-line-two", .62],
        [props.lineThree ?? state.lineThree ?? "Style", "latest-line latest-lastline", "latest-line-three", .54],
      ];
      for (const [text, className, name, width] of lines) {
        const line = document.createElement("div");
        line.className = className;
        line.dataset.layoutItem = name;
        line.dataset.displayItem = "true";
        line.textContent = text;
        board.append(line);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * width,
          height: board.clientHeight * .20,
          maxSize: 250 * state.scale,
          minSize: 38,
          tracking: state.tracking,
          inkAware: true,
        });
        line.style.letterSpacing = state.tracking + "em";
      }
      const rule = document.createElement("div");
      rule.className = "latest-rule";
      rule.dataset.layoutItem = "latest-footer-rule";
      board.append(rule);
      const left = document.createElement("div");
      left.className = "latest-footer latest-footer-left";
      left.dataset.layoutItem = "latest-caption";
      left.textContent = props.caption ?? state.caption ?? "Display Lettering";
      board.append(left);
      const right = document.createElement("div");
      right.className = "latest-footer latest-footer-right";
      right.dataset.layoutItem = "latest-signature";
      right.textContent = props.signature ?? state.signature ?? "Autumn Lookbook";
      board.append(right);
    },
    getContrast() { return window.SupportLayout.contrast("#fffaf4", "#33383d"); },
    getWarnings() { return design.warnings || []; },
  };
  window.LatestLook32 = design;
})();
