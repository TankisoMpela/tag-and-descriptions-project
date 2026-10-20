(function () {
  const design = {
    id: "neon32",
    title: "Neon Marquee",
    defaults: {
      headline: "La Dolce\nMarea",
      comingSoon: "Coming Soon",
      scale: 1,
      glowStrength: .78,
      gateStrength: .82,
      wall: "#25160f",
      tube: "#fff2d7",
      glow: "#ffae5e",
      gate: "#f6e8cf",
    },
    controls: [
      { key: "headline", label: "Marquee · one line per row", type: "textarea", rows: 2, value: "La Dolce\nMarea" },
      { key: "comingSoon", label: "Small sign line", type: "text", value: "Coming Soon" },
      { key: "scale", label: "Marquee lettering scale", min: .82, max: 1.12, step: .01 },
      { key: "glowStrength", label: "Tube bloom", min: .25, max: 1.25, step: .01 },
      { key: "gateStrength", label: "Film-gate light", min: .4, max: 1, step: .01 },
      { key: "wall", label: "Theatre wall", type: "color", value: "#25160f" },
      { key: "tube", label: "Tube core", type: "color", value: "#fff2d7" },
      { key: "glow", label: "Warm bloom", type: "color", value: "#ffae5e" },
      { key: "gate", label: "Perforation light", type: "color", value: "#f6e8cf" },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", 'SupportDisplay, "URW Chancery L", "Brush Script MT", cursive');
      board.style.setProperty("--neon-wall", props.wall ?? state.wall ?? design.defaults.wall);
      board.style.setProperty("--neon-tube", props.tube ?? state.tube ?? design.defaults.tube);
      board.style.setProperty("--neon-glow", props.glow ?? state.glow ?? design.defaults.glow);
      board.style.setProperty("--neon-gate", props.gate ?? state.gate ?? design.defaults.gate);
      board.style.setProperty("--neon-glow-strength", String(props.glowStrength ?? state.glowStrength ?? design.defaults.glowStrength));
      board.style.setProperty("--neon-gate-strength", String(props.gateStrength ?? state.gateStrength ?? design.defaults.gateStrength));

      const layer = (className, name, parent = board) => {
        const element = document.createElement("div");
        element.className = className;
        element.dataset.layoutItem = name;
        parent.append(element);
        return element;
      };
      const fold = layer("wall-fold", "centre-door-seam");
      fold.setAttribute("aria-hidden", "true");
      const grain = layer("wall-grain", "photographic-wall-grain");
      grain.setAttribute("aria-hidden", "true");
      grain.innerHTML = '<svg viewBox="0 0 1200 800" preserveAspectRatio="none"><filter id="neon-grain"><feTurbulence type="fractalNoise" baseFrequency=".72" numOctaves="2" seed="3017307" stitchTiles="stitch"/></filter><rect width="100%" height="100%" filter="url(#neon-grain)" opacity=".38"/></svg>';

      for (const side of ["left", "right"]) {
        const strip = layer(`film-strip film-strip-${side}`, `film-gate-${side}`);
        strip.setAttribute("aria-hidden", "true");
        for (let index = 0; index < 7; index += 1) {
          const slot = document.createElement("span");
          slot.className = "film-slot";
          slot.dataset.layoutItem = `film-light-${side}-${index + 1}`;
          slot.style.top = `${.8 + index * 15}%`;
          strip.append(slot);
        }
        const rail = document.createElement("span");
        rail.className = "film-rail";
        rail.dataset.layoutItem = `film-rail-${side}`;
        strip.append(rail);
      }

      const lines = String(props.headline ?? state.headline ?? design.defaults.headline)
        .split(/\r?\n/).map((line) => line.trim()).filter(Boolean).slice(0, 5);
      const title = layer("marquee-stage", "lit-marquee-copy");
      title.style.gridTemplateRows = `repeat(${Math.max(1, lines.length)}, minmax(0, 1fr))`;
      title.style.rowGap = `${board.clientHeight * (lines.length > 2 ? .007 : .018)}px`;
      const scale = Number(props.scale ?? state.scale ?? design.defaults.scale);
      lines.forEach((text, index) => {
        const line = document.createElement("span");
        line.className = "marquee-line";
        line.dataset.layoutItem = `marquee-line-${index + 1}`;
        line.dataset.displayItem = "true";
        line.textContent = text;
        title.append(line);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * .71,
          height: (title.clientHeight / Math.max(1, lines.length)) * .8,
          maxSize: board.clientHeight * (lines.length > 2 ? .17 : .215) * scale,
          minSize: board.clientHeight * .035,
          tracking: 0,
          inkAware: true,
        });
      });

      const comingSoon = layer("coming-soon", "coming-soon-line");
      comingSoon.dataset.displayItem = "true";
      comingSoon.textContent = String(props.comingSoon ?? state.comingSoon ?? design.defaults.comingSoon).trim();
      window.SupportLayout.fitLine(comingSoon, {
        width: board.clientWidth * .45,
        height: board.clientHeight * .075,
        maxSize: board.clientHeight * .064 * scale,
        minSize: board.clientHeight * .024,
        tracking: .008,
        inkAware: true,
      });
      comingSoon.style.letterSpacing = ".008em";
    },
    getContrast() {
      const wall = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--neon-wall").trim() || "#25160f";
      const tube = getComputedStyle(document.getElementById("artboard")).getPropertyValue("--neon-tube").trim() || "#fff2d7";
      return window.SupportLayout.contrast(tube, wall);
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Neon32 = design;
})();
