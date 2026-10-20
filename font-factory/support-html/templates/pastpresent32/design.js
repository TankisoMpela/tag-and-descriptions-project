(function () {
  const defaults = {
    past: "Past",
    present: "Present",
    future: "Future",
    credit: "Our SunKits © Rivari Studio 2024",
    scale: 1,
    tracking: 0,
    gap: 1,
  };
  const design = {
    id: "pastpresent32",
    title: "Past / Present / Future",
    labelFace: "PastPresentLabel",
    defaults,
    controls: [
      { key: "past", label: "Top sign", type: "text", value: defaults.past },
      { key: "present", label: "Center sign", type: "text", value: defaults.present },
      { key: "future", label: "Bottom sign", type: "text", value: defaults.future },
      { key: "credit", label: "Studio credit", type: "text", value: defaults.credit },
      { key: "scale", label: "Sign lettering scale", min: .82, max: 1.12, step: .01 },
      { key: "tracking", label: "Letter spacing", min: -.02, max: .04, step: .005 },
      { key: "gap", label: "Sign separation", min: .82, max: 1.18, step: .01 },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "PastPresentLabel");
      const art = document.createElement("div");
      art.className = "timeline-art";
      art.dataset.layoutItem = "source-hand-sign-art";
      art.setAttribute("role", "img");
      art.setAttribute("aria-label", "Illustrated peace-sign and rock-hand badges surrounding three blank retro signs");
      board.append(art);

      const words = [
        ["past", defaults.past, "timeline-past", "timeline-word timeline-past", .42, .15, .28, 116],
        ["present", defaults.present, "timeline-present", "timeline-word timeline-present", .68, .16, .30, 120],
        ["future", defaults.future, "timeline-future", "timeline-word timeline-future", .44, .16, .28, 116],
      ];
      const gap = Number(props.gap ?? state.gap);
      const topOffsets = [(gap - 1) * -1.7, 0, (gap - 1) * 1.7];
      words.forEach(([key, fallback, name, className, width, height, maxFactor, maxSize], index) => {
        const line = document.createElement("div");
        line.className = className;
        line.dataset.layoutItem = name;
        line.dataset.displayItem = "true";
        line.textContent = props[key] ?? state[key] ?? fallback;
        board.append(line);
        const baseSize = board.clientHeight * maxFactor * Number(props.scale ?? state.scale);
        line.style.top = `calc(${index === 0 ? 15.5 : index === 1 ? 41 : 66}% + ${board.clientHeight * .008}px + ${topOffsets[index]}%)`;
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * width,
          height: board.clientHeight * height,
          maxSize: Math.max(maxSize * board.clientWidth / 1200, baseSize),
          minSize: board.clientHeight * .065,
          tracking: Number(props.tracking ?? state.tracking),
          inkAware: true,
        });
        line.style.letterSpacing = (props.tracking ?? state.tracking) + "em";
      });
      const credit = document.createElement("div");
      credit.className = "timeline-credit";
      credit.dataset.layoutItem = "timeline-studio-credit";
      credit.textContent = props.credit ?? state.credit ?? defaults.credit;
      board.append(credit);
    },
    getContrast() { return window.SupportLayout.contrast("#251f1d", "#fff4db"); },
    getWarnings() { return design.warnings || []; },
  };
  window.PastPresent32 = design;
})();
