(function () {
  function starPoints(cx, cy, outer, inner) {
    const points = [];
    for (let i = 0; i < 16; i += 1) {
      const radius = i % 2 ? inner : outer;
      const angle = -Math.PI / 2 + i * Math.PI / 8;
      points.push(`${cx + Math.cos(angle) * radius},${cy + Math.sin(angle) * radius}`);
    }
    return points.join(" ");
  }

  const design = {
    id: "confident32",
    title: "Confidence poster",
    defaults: { scale: 1, top: .155, tracking: -.04, taglineScale: 1, eyeScale: 1 },
    controls: [
      { key: "scale", label: "Headline scale", min: .90, max: 1.08, step: .01 },
      { key: "top", label: "Headline position", min: .13, max: .18, step: .001 },
      { key: "tracking", label: "Headline spacing", min: -.065, max: -.015, step: .001 },
      { key: "taglineScale", label: "Tagline scale", min: .90, max: 1.10, step: .01 },
      { key: "eyeScale", label: "Eye framing", min: .98, max: 1.06, step: .01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scale = Number(props.scale ?? state.scale ?? 1);
      const top = Number(props.top ?? state.top ?? .155);
      const tracking = Number(props.tracking ?? state.tracking ?? -.04);
      const taglineScale = Number(props.taglineScale ?? state.taglineScale ?? 1);
      const eyeScale = Number(props.eyeScale ?? state.eyeScale ?? 1);
      board.style.setProperty("--eye-scale", String(eyeScale));
      board.style.setProperty("--label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "ConfidenceLabel, sans-serif");

      const eyeWindow = document.createElement("div");
      eyeWindow.className = "confidence-eye-window";
      eyeWindow.dataset.layoutItem = "source-eye-crop-frame";
      const eye = document.createElement("img");
      eye.className = "confidence-eye-art";
      eye.src = "../../../support-references/materials/T28576_04_eye-illustration-clean.png";
      eye.alt = "";
      eye.draggable = false;
      eyeWindow.append(eye);
      board.append(eyeWindow);

      const frame = document.createElement("div");
      frame.className = "confidence-frame";
      frame.dataset.layoutItem = "poster-frame";
      board.append(frame);

      for (const [name, left, width, className] of [
        ["divider-rule-left", .045, .42, "confidence-divider-left"],
        ["divider-rule-right", .535, .42, "confidence-divider-right"],
      ]) {
        const rule = document.createElement("div");
        rule.className = `confidence-divider-line ${className}`;
        rule.style.left = `${left * 100}%`;
        rule.style.width = `${width * 100}%`;
        rule.dataset.layoutItem = name;
        board.append(rule);
      }

      const cluster = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      cluster.setAttribute("viewBox", "0 0 120 30");
      cluster.setAttribute("aria-hidden", "true");
      cluster.classList.add("confidence-star-cluster");
      cluster.dataset.layoutItem = "center-star-divider";
      for (const [cx, outer, inner] of [[26, 6, 1.35], [60, 12, 2.7], [94, 6, 1.35]]) {
        const star = document.createElementNS("http://www.w3.org/2000/svg", "polygon");
        star.setAttribute("points", starPoints(cx, 15, outer, inner));
        star.setAttribute("fill", "#111112");
        cluster.append(star);
      }
      board.append(cluster);

      function addLabel(name, content, box, className, trackingValue, maxSize, align = "left") {
        const row = document.createElement("div");
        row.className = `confidence-row ${className}`;
        row.style.left = `${box.left * 100}%`;
        row.style.top = `${box.top * 100}%`;
        row.style.width = `${box.width * 100}%`;
        row.style.height = `${box.height * 100}%`;
        if (align === "right") row.style.justifyContent = "flex-end";
        row.dataset.layoutItem = `${name}-row`;
        const line = document.createElement("span");
        line.className = `confidence-label ${className}-label`;
        line.textContent = content;
        line.dataset.layoutItem = name;
        row.append(line);
        board.append(row);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * box.width * .96,
          height: board.clientHeight * box.height * .88,
          maxSize: board.clientHeight * maxSize,
          minSize: board.clientHeight * maxSize * .68,
          tracking: trackingValue,
          inkAware: true,
        });
        return row;
      }

      addLabel("poster-overline", props.overline || "Keep Looking",
        { left: .06, top: .07, width: .56, height: .075 },
        "confidence-overline", .08, .056);
      addLabel("poster-tag", props.tag || "Elthia Typeface",
        { left: .72, top: .07, width: .21, height: .075 },
        "confidence-tag", .04, .025);

      const heroRow = document.createElement("div");
      heroRow.className = "confidence-row confidence-hero-row";
      heroRow.style.left = "5.5%";
      heroRow.style.top = `${top * 100}%`;
      heroRow.style.width = "89%";
      heroRow.style.height = "19.5%";
      heroRow.dataset.layoutItem = "headline-row";
      const hero = document.createElement("span");
      hero.className = "confidence-hero";
      hero.textContent = props.headline || "Confident";
      hero.style.letterSpacing = `${tracking}em`;
      hero.dataset.layoutItem = "confidence-headline";
      hero.dataset.displayItem = "true";
      heroRow.append(hero);
      board.append(heroRow);
      window.SupportLayout.fitLine(hero, {
        width: board.clientWidth * .89 * .98,
        height: board.clientHeight * .205 * .90,
        maxSize: board.clientHeight * .205 * scale,
        minSize: board.clientHeight * .07,
        tracking,
        inkAware: true,
      });

      addLabel("tagline-left", props.taglineLeft || "Even When",
        { left: .06, top: .355, width: .39, height: .065 },
        "confidence-tagline", -.015 * taglineScale, .038 * taglineScale);
      addLabel("tagline-right", props.taglineRight || "Doubt Looks Back",
        { left: .49, top: .355, width: .45, height: .065 },
        "confidence-tagline", -.015 * taglineScale, .038 * taglineScale, "right");
    },
    getContrast() {
      return window.SupportLayout.contrast("#e20d24", "#ffffff");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Confident32 = design;
})();
