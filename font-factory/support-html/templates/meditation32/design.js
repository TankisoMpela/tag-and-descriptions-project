(function () {
  const design = {
    id: "meditation32",
    title: "Meditation workshop",
    labelFace: "MeditationLabel",
    defaults: {
      headline: "Meditation",
      workshop: "Workshop",
      badge: "Disc 30%",
      date: "September 30",
      year: "2025",
      tagline: "Sign Up Here\nwww.meditatewithdelaine.com",
      scale: 1,
      tracking: -0.035,
    },
    controls: [
      { key: "headline", label: "Main word", type: "text", value: "Meditation" },
      { key: "workshop", label: "Pill caption", type: "text", value: "Workshop" },
      { key: "badge", label: "Burst words", type: "text", value: "Disc 30%" },
      { key: "date", label: "Date caption", type: "text", value: "September 30" },
      { key: "year", label: "Year", type: "text", value: "2025" },
      { key: "tagline", label: "Sign-up caption", type: "text", value: "Sign Up Here / www.meditatewithdelaine.com" },
      { key: "scale", label: "Headline scale", min: 0.82, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Headline spacing", min: -0.10, max: 0.01, step: 0.005 },
    ],
    contrastException: {
      minimum: 1.55,
      rationale: "The source keeps large white display lettering over a deliberately soft pastel gradient.",
    },
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "MeditationLabel");

      const weave = document.createElement("div");
      weave.className = "meditation-weave";
      weave.dataset.layoutItem = "meditation-woven-paper";
      board.append(weave);
      const bubbles = document.createElement("div");
      bubbles.className = "meditation-bubbles";
      bubbles.dataset.layoutItem = "meditation-bubble-art";
      board.append(bubbles);
      for (const [cls, name] of [
        ["meditation-spark-one", "meditation-sparkle-top-left"],
        ["meditation-spark-two", "meditation-sparkle-right"],
        ["meditation-spark-three", "meditation-sparkle-small"],
      ]) {
        const spark = document.createElement("div");
        spark.className = "meditation-spark " + cls;
        spark.dataset.layoutItem = name;
        spark.innerHTML = '<svg viewBox="0 0 100 100" aria-hidden="true"><path d="M50 0 58 42 100 50 58 58 50 100 42 58 0 50 42 42Z" fill="currentColor"/></svg>';
        board.append(spark);
      }

      const title = document.createElement("div");
      title.className = "meditation-title";
      title.dataset.layoutItem = "meditation-headline";
      title.dataset.displayItem = "true";
      title.textContent = props.headline ?? state.headline ?? "Meditation";
      board.append(title);
      window.SupportLayout.fitLine(title, {
        width: board.clientWidth * .84,
        height: board.clientHeight * .31,
        maxSize: 320 * state.scale,
        minSize: 58,
        tracking: state.tracking,
      });
      title.style.letterSpacing = state.tracking + "em";

      const pill = document.createElement("div");
      pill.className = "meditation-pill";
      pill.dataset.layoutItem = "meditation-workshop-pill";
      pill.textContent = props.workshop ?? state.workshop ?? "Workshop";
      board.append(pill);

      const photo = document.createElement("div");
      photo.className = "meditation-photo";
      photo.dataset.layoutItem = "meditation-sea-photo";
      board.append(photo);

      const badge = document.createElement("div");
      badge.className = "meditation-badge";
      badge.dataset.layoutItem = "meditation-reset-burst";
      const words = String(props.badge ?? state.badge ?? "Disc 30%").trim().split(/\s+/);
      badge.textContent = words.length > 1 ? words.join("\n") : words[0];
      badge.style.whiteSpace = "pre-line";
      board.append(badge);

      const date = document.createElement("div");
      date.className = "meditation-footer meditation-date";
      date.dataset.layoutItem = "meditation-footer-left";
      date.textContent = props.date ?? state.date ?? "September 30";
      board.append(date);
      const year = document.createElement("div");
      year.className = "meditation-footer meditation-year";
      year.dataset.layoutItem = "meditation-year";
      year.textContent = props.year ?? state.year ?? "2025";
      board.append(year);
      const tagline = document.createElement("div");
      tagline.className = "meditation-footer meditation-tagline";
      tagline.dataset.layoutItem = "meditation-footer-right";
      tagline.textContent = String(props.tagline ?? state.tagline ?? "Sign Up Here\nwww.meditatewithdelaine.com").replace(/\s*\/\s*/, "\n");
      board.append(tagline);
    },
    getContrast() { return window.SupportLayout.contrast("#ffffff", "#bbacd9"); },
    getWarnings() { return design.warnings || []; },
  };
  window.Meditation32 = design;
})();
