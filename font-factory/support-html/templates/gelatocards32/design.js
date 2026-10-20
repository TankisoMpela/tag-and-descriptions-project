(function () {
  const design = {
    id: "gelatocards32",
    title: "Gelato cards",
    labelFace: "GelatoLabel",
    defaults: {
      frontOne: "Sweet",
      frontTwo: "Scoops",
      backOne: "Sweet",
      backTwo: "Scoops",
      frontLabel: "Pastel  /  Frozen",
      backLabel: "Scoop  /  Shop",
      footer: "A Little Joy In Every Scoop",
      scale: 1,
      tracking: -0.04,
    },
    controls: [
      { key: "frontOne", label: "Pink card first line", type: "text", value: "Sweet" },
      { key: "frontTwo", label: "Pink card second line", type: "text", value: "Scoops" },
      { key: "backOne", label: "Blue card first line", type: "text", value: "Sweet" },
      { key: "backTwo", label: "Blue card second line", type: "text", value: "Scoops" },
      { key: "frontLabel", label: "Pink card top label", type: "text", value: "Pastel  /  Frozen" },
      { key: "backLabel", label: "Blue card top label", type: "text", value: "Scoop  /  Shop" },
      { key: "footer", label: "Pink card footer", type: "text", value: "A Little Joy In Every Scoop" },
      { key: "scale", label: "Display scale", min: 0.82, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Letter spacing", min: -0.10, max: 0.01, step: 0.005 },
    ],
    contrastException: {
      minimum: 4.5,
      rationale: "The source card uses cobalt display ink over its pale pink print panel.",
    },
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "GelatoLabel");

      const wash = document.createElement("div");
      wash.className = "gelato-wash";
      board.append(wash);
      for (const cls of ["gelato-shadow-back", "gelato-shadow-front"]) {
        const shadow = document.createElement("div");
        shadow.className = "gelato-shadow " + cls;
        board.append(shadow);
      }

      const back = document.createElement("div");
      back.className = "gelato-card gelato-back";
      back.dataset.layoutItem = "gelato-blue-card";
      const backPattern = document.createElement("div");
      backPattern.className = "gelato-pattern gelato-pattern-back";
      back.append(backPattern);
      board.append(back);
      const backLabel = document.createElement("div");
      backLabel.className = "gelato-label gelato-back-label";
      backLabel.dataset.layoutItem = "gelato-blue-label";
      backLabel.textContent = props.backLabel ?? state.backLabel ?? "Scoop  /  Shop";
      const backTexts = [
        [props.backOne ?? state.backOne ?? "Sweet", "gelato-back-copy gelato-back-line-one", "gelato-blue-headline-one"],
        [props.backTwo ?? state.backTwo ?? "Scoops", "gelato-back-copy gelato-back-line-two", "gelato-blue-headline-two"],
      ];
      back.append(backLabel);
      for (const [text, cls, name] of backTexts) {
        const line = document.createElement("div");
        line.className = cls;
        line.dataset.layoutItem = name;
        line.dataset.displayItem = "true";
        line.textContent = text;
        back.append(line);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * .25,
          height: board.clientHeight * .13,
          maxSize: 88 * state.scale,
          minSize: 24,
          tracking: state.tracking,
        });
        line.style.letterSpacing = state.tracking + "em";
      }
      const front = document.createElement("div");
      front.className = "gelato-card gelato-front";
      front.dataset.layoutItem = "gelato-pink-card";
      board.append(front);
      const frontPattern = document.createElement("div");
      frontPattern.className = "gelato-pattern gelato-pattern-front";
      const tint = document.createElement("div");
      tint.className = "gelato-tint";
      front.append(frontPattern, tint);
      const label = document.createElement("div");
      label.className = "gelato-label gelato-front-label";
      label.dataset.layoutItem = "gelato-pink-label";
      label.textContent = props.frontLabel ?? state.frontLabel ?? "Pastel  /  Frozen";
      const rule = document.createElement("div");
      rule.className = "gelato-rule";
      rule.dataset.layoutItem = "gelato-pink-rule";
      const frontTexts = [
        [props.frontOne ?? state.frontOne ?? "Sweet", "gelato-title gelato-title-one", "gelato-pink-headline-one"],
        [props.frontTwo ?? state.frontTwo ?? "Scoops", "gelato-title gelato-title-two", "gelato-pink-headline-two"],
      ];
      const footer = document.createElement("div");
      footer.className = "gelato-footer";
      footer.dataset.layoutItem = "gelato-pink-footer";
      footer.textContent = props.footer ?? state.footer ?? "A Little Joy In Every Scoop";
      front.append(label, rule);
      for (const [text, cls, name] of frontTexts) {
        const line = document.createElement("div");
        line.className = cls;
        line.dataset.layoutItem = name;
        line.dataset.displayItem = "true";
        line.textContent = text;
        front.append(line);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * .43,
          height: board.clientHeight * .13,
          maxSize: 126 * state.scale,
          minSize: 40,
          tracking: state.tracking,
        });
        line.style.letterSpacing = state.tracking + "em";
      }
      front.append(footer);
    },
    getContrast() { return window.SupportLayout.contrast("#254ad1", "#ffbfd7"); },
    getWarnings() { return design.warnings || []; },
  };
  window.GelatoCards32 = design;
})();
