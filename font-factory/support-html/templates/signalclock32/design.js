(function () {
  const design = {
    id: "signalclock32",
    title: "Signal clock",
    defaults: { value: "$50.50", scale: 1, valueWidth: 0.58, tracking: -0.06 },
    controls: [
      { key: "value", label: "Price specimen", type: "text", value: "$50.50" },
      { key: "scale", label: "Numeral scale", min: 0.8, max: 1.12, step: 0.01 },
      { key: "valueWidth", label: "Price width", min: 0.48, max: 0.66, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.12, max: 0.005, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", `${design.labelFace || "SignalLabel"}, Arial, sans-serif`);

      const value = document.createElement("div");
      value.className = "signal-value";
      value.dataset.layoutItem = "signal-price";
      value.dataset.displayItem = "true";
      value.textContent = props.value ?? state.value ?? "$50.50";
      board.append(value);
      window.SupportLayout.fitLine(value, {
        width: board.clientWidth * .94,
        height: board.clientHeight * .68,
        maxSize: 660 * state.scale,
        minSize: 74,
        tracking: state.tracking,
      });
      value.style.letterSpacing = `${state.tracking}em`;
      const naturalValueWidth = value.getBoundingClientRect().width;
      const valueScaleX = board.clientWidth * state.valueWidth / Math.max(naturalValueWidth, 1);
      value.style.transform = `translate(-50%, -50%) scaleX(${valueScaleX})`;

      const plaque = document.createElement("div");
      plaque.className = "signal-plaque";
      plaque.dataset.layoutItem = "signal-currency-plaque";
      const label = document.createElement("span");
      label.className = "signal-currency";
      label.dataset.layoutItem = "signal-currency-label";
      label.dataset.displayItem = "true";
      label.textContent = props.label ?? state.label ?? "Dollar";
      plaque.append(label);
      board.append(plaque);
      window.SupportLayout.fitLine(label, {
        width: board.clientWidth * .32,
        height: board.clientHeight * .105,
        maxSize: board.clientHeight * .085,
        minSize: board.clientHeight * .035,
        tracking: -.04,
      });
      label.style.letterSpacing = "-.04em";
      const naturalLabelWidth = label.getBoundingClientRect().width;
      const innerWidth = board.clientWidth * .145;
      label.style.transform = `translate(-50%, -50%) scaleX(${Math.min(1, innerWidth / Math.max(naturalLabelWidth, 1))})`;
    },
    getContrast() { return window.SupportLayout.contrast("#f8f7f4", "#000000"); },
    getWarnings() { return design.warnings || []; },
  };
  window.SignalClock32 = design;
})();
