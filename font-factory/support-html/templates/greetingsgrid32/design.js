(function () {
  const colors = {
    pale: "#d3a1aa", blue: "#00567e", yellow: "#ffca05",
    pink: "#ef245d", green: "#00745e", navy: "#111a4d",
    brown: "#302320", lime: "#dce253", red: "#e21a34",
    gold: "#ffdf55", cream: "#ffebcd",
  };
  const tiles = [
    { name: "zdravo", text: "Zdravo!", cls: "tile-zdravo", size: 72, min: 34, width: 1 / 3, height: .25, bg: colors.pale, fg: colors.brown },
    { name: "howdy", text: "Howdy!", cls: "tile-howdy", size: 94, min: 34, width: 1 / 3, height: .25, bg: colors.blue, fg: colors.lime },
    { name: "halla", text: "Hallå!", cls: "tile-halla", size: 238, min: 42, width: 2 / 3, height: .5, bg: colors.yellow, fg: colors.red },
    { name: "bonjour", text: "Bonjour!", cls: "tile-bonjour", size: 218, min: 42, width: 2 / 3, height: .5, bg: colors.pink, fg: colors.gold },
    { name: "privet", text: "Privet!", cls: "tile-privet", size: 96, min: 34, width: 1 / 3, height: .25, bg: colors.green, fg: colors.cream },
    { name: "ola", text: "Olá!", cls: "tile-ola", size: 102, min: 34, width: 1 / 3, height: .25, bg: colors.navy, fg: colors.yellow },
  ];

  const design = {
    id: "greetingsgrid32",
    title: "Greeting grid",
    defaults: { scale: 1 },
    controls: [
      { key: "scale", label: "Greeting scale", min: 0.78, max: 1.05, step: 0.01 },
    ],
    contrastException: {
      minimum: 3,
      rationale: "The original saturated print palette is retained for large greeting headlines.",
    },
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      let smallest = Infinity;
      const values = props.greetings || {};
      for (const spec of tiles) {
        const text = values[spec.name] || spec.text;
        const panel = document.createElement("div");
        panel.className = `greeting-tile ${spec.cls}`;
        panel.style.backgroundColor = spec.bg;
        panel.setAttribute("aria-hidden", "true");
        board.append(panel);
        const slot = document.createElement("div");
        slot.className = `greeting-copy greet-${spec.name}`;
        const run = document.createElement("span");
        run.className = "greeting-run";
        run.dataset.layoutItem = `greeting-${spec.name}`;
        run.dataset.displayItem = "true";
        run.textContent = text;
        slot.append(run);
        board.append(slot);
        const size = window.SupportLayout.fitLine(run, {
          width: board.clientWidth * spec.width * .80,
          height: board.clientHeight * spec.height * .74,
          maxSize: spec.size * state.scale,
          minSize: spec.min,
          tracking: -.025,
          inkAware: true,
        });
        run.style.letterSpacing = "-.025em";
        smallest = Math.min(smallest, size);
      }
      const pressSeal = document.createElement("div");
      pressSeal.className = "greeting-seal seal-press";
      pressSeal.setAttribute("aria-hidden", "true");
      pressSeal.innerHTML = "<span>M</span><small>Type Study</small>";
      board.append(pressSeal);
      const studioSeal = document.createElement("div");
      studioSeal.className = "greeting-seal seal-studio";
      studioSeal.setAttribute("aria-hidden", "true");
      studioSeal.innerHTML = "<span>Type</span>";
      board.append(studioSeal);
      const grain = document.createElement("div");
      grain.className = "greeting-grain";
      grain.setAttribute("aria-hidden", "true");
      board.append(grain);
      board.dataset.minimumGreetingSize = String(smallest);
    },
    getContrast() {
      return Math.min(
        window.SupportLayout.contrast(colors.brown, colors.pale),
        window.SupportLayout.contrast(colors.lime, colors.blue),
        window.SupportLayout.contrast(colors.red, colors.yellow),
        window.SupportLayout.contrast(colors.gold, colors.pink),
        window.SupportLayout.contrast(colors.cream, colors.green),
        window.SupportLayout.contrast(colors.yellow, colors.navy),
      );
    },
    getWarnings() { return design.warnings || []; },
  };
  window.GreetingsGrid32 = design;
})();
