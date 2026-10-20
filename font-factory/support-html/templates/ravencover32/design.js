(function () {
  const design = {
    id: "ravencover32",
    title: "Raven cover",
    defaults: { scale: 1, top: .365, tracking: -.035, captionScale: 1, shade: .20 },
    controls: [
      { key: "scale", label: "Headline scale", min: .90, max: 1.08, step: .01 },
      { key: "top", label: "Headline position", min: .345, max: .385, step: .001 },
      { key: "tracking", label: "Headline spacing", min: -.06, max: -.015, step: .001 },
      { key: "captionScale", label: "Editorial detail scale", min: .90, max: 1.10, step: .01 },
      { key: "shade", label: "Photo shade", min: .12, max: .32, step: .01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const scale = Number(props.scale ?? state.scale ?? 1);
      const top = Number(props.top ?? state.top ?? .365);
      const tracking = Number(props.tracking ?? state.tracking ?? -.035);
      const captionScale = Number(props.captionScale ?? state.captionScale ?? 1);
      const shade = Number(props.shade ?? state.shade ?? .20);
      board.style.setProperty("--raven-shade", String(shade));
      board.style.setProperty("--raven-label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "RavenCoverLabel, sans-serif");

      const photo = document.createElement("img");
      photo.className = "raven-photo";
      photo.dataset.layoutItem = "clean-tailoring-photo";
      photo.src = "../../../support-references/materials/T28660_00_red-jacket-photo.png";
      photo.alt = "";
      photo.draggable = false;
      board.append(photo);

      const veil = document.createElement("div");
      veil.className = "raven-veil";
      veil.dataset.layoutItem = "photo-veil";
      board.append(veil);

      for (const [className, name, topValue] of [
        ["raven-rule-top", "top-cover-rule", .03],
        ["raven-rule-bottom", "bottom-cover-rule", .935],
      ]) {
        const rule = document.createElement("div");
        rule.className = `raven-rule ${className}`;
        rule.dataset.layoutItem = name;
        rule.style.top = `${topValue * 100}%`;
        board.append(rule);
      }

      const badge = document.createElement("div");
      badge.className = "raven-badge";
      badge.dataset.layoutItem = "oval-issue-mark";
      board.append(badge);

      const labelRows = [];
      function addLabel(name, text, box, className) {
        const row = document.createElement("div");
        row.className = `raven-label-row ${className}`;
        row.style.left = `${box.left * 100}%`;
        row.style.top = `${box.top * 100}%`;
        row.style.width = `${box.width * 100}%`;
        row.style.height = `${box.height * 100}%`;
        row.dataset.layoutItem = `${name}-row`;
        const label = document.createElement("span");
        label.className = `raven-label ${className}-label`;
        label.textContent = text;
        label.dataset.layoutItem = name;
        row.append(label);
        board.append(row);
        labelRows.push({ element: label, box, name });
      }

      addLabel("cover-masthead", "Present By",
        { left: .4221, top: .0861, width: .1558, height: .027 }, "raven-kicker");
      addLabel("cover-issue", "Muksal Creative",
        { left: .4221, top: .1152, width: .1558, height: .026 }, "raven-issue");
      addLabel("cover-subtitle", "Modern Serif Display Font",
        { left: .08, top: .725, width: .84, height: .060 }, "raven-copy");
      addLabel("cover-details", "Regular & Italic Font",
        { left: .08, top: .810, width: .84, height: .055 }, "raven-details");

      const titleRow = document.createElement("div");
      titleRow.className = "raven-title-row";
      titleRow.style.left = "7.5%";
      titleRow.style.top = `${top * 100}%`;
      titleRow.style.width = "85%";
      titleRow.style.height = "23.5%";
      titleRow.dataset.layoutItem = "cover-headline-row";
      const title = document.createElement("span");
      title.className = "raven-title";
      title.dataset.layoutItem = "cover-headline";
      title.dataset.displayItem = "true";
      title.textContent = "Raven Court";
      title.style.letterSpacing = `${tracking}em`;
      titleRow.append(title);
      board.append(titleRow);

      for (const { element, box, name } of labelRows) {
        const isBadge = name === "cover-masthead" || name === "cover-issue";
        const heightScale = name === "cover-masthead" ? .0125
          : name === "cover-issue" ? .01125
          : name === "cover-subtitle" ? .023125 : .018125;
        window.SupportLayout.fitLine(element, {
          width: board.clientWidth * box.width * .94,
          height: board.clientHeight * box.height * .86,
          maxSize: board.clientHeight * heightScale * (isBadge ? 1 : captionScale),
          minSize: Math.max(7, board.clientHeight * heightScale * .72),
          tracking: name === "cover-masthead" ? .05
            : name === "cover-issue" ? .08
            : name === "cover-subtitle" ? .12 : .14,
          inkAware: true,
        });
      }
      window.SupportLayout.fitLine(title, {
        width: board.clientWidth * .85 * .96,
        height: board.clientHeight * .235 * .90,
        maxSize: board.clientHeight * .20625 * scale,
        minSize: board.clientHeight * .068,
        tracking,
        inkAware: true,
      });
    },
    contrastException: {
      minimum: 3,
      rationale: "The cover type sits directly over a variable red-tailoring photograph under the source-matched veil.",
    },
    getContrast() {
      return window.SupportLayout.contrast("#f5ebd8", "#50312d");
    },
    getWarnings() { return design.warnings || []; },
  };
  window.RavenCover32 = design;
})();
