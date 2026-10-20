(function () {
  const design = {
    id: "voguecover32",
    title: "Fashion editorial cover",
    defaults: {
      masthead: "Vogue",
      submast: "Japan",
      issue: "March\nIssue",
      leftKicker: "Discover",
      leftStory: "The New\nStreet Fashion\nTrends From",
      destination: "Tokyo",
      lowerKicker: "Reina Sato",
      lowerStory: "Shows You How\nTo Take The\nPerfect Selfie",
      featureLines: "Sakura\nYamaguchi",
      featureNote: "The Making Of\nAsia's Next\nTop Model",
      footerLead: "Follow Us On Social Media",
      footerNote: "Facebook / Instagram / TikTok",
      mastheadScale: 1,
      portraitScale: 1,
      columnScale: 1,
      featureScale: 1,
      tracking: -0.025,
    },
    controls: [
      { key: "masthead", label: "Masthead", type: "text" },
      { key: "submast", label: "Top subline", type: "text" },
      { key: "issue", label: "Issue mark · one line per row", type: "textarea", rows: 2 },
      { key: "leftKicker", label: "Left column heading", type: "text" },
      { key: "leftStory", label: "Left editorial copy · one line per row", type: "textarea", rows: 3 },
      { key: "destination", label: "Red accent word", type: "text" },
      { key: "lowerKicker", label: "Lower-left heading", type: "text" },
      { key: "lowerStory", label: "Lower-left copy · one line per row", type: "textarea", rows: 3 },
      { key: "featureLines", label: "Feature title · one line per row", type: "textarea", rows: 2 },
      { key: "featureNote", label: "Feature deck · one line per row", type: "textarea", rows: 3 },
      { key: "footerLead", label: "Footer heading", type: "text" },
      { key: "footerNote", label: "Footer line", type: "text" },
      { key: "mastheadScale", label: "Masthead scale", min: 0.88, max: 1.1, step: 0.01 },
      { key: "portraitScale", label: "Portrait scale", min: 0.94, max: 1.02, step: 0.005 },
      { key: "columnScale", label: "Editorial column scale", min: 0.82, max: 1.12, step: 0.01 },
      { key: "featureScale", label: "Feature title scale", min: 0.84, max: 1.14, step: 0.01 },
      { key: "tracking", label: "Display tracking", min: -0.06, max: 0.02, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      design.paper = props.paper || "#f9f7f1";
      design.red = props.red || "#de091c";
      design.ink = props.ink || "#111112";
      board.replaceChildren();
      board.style.setProperty("--cover-paper", design.paper);
      board.style.setProperty("--cover-red", design.red);
      board.style.setProperty("--cover-ink", design.ink);
      board.style.setProperty("--display-face", "SupportDisplay, 'Noto Serif Display', Georgia, serif");

      const portrait = document.createElement("img");
      portrait.className = "cover-portrait";
      portrait.dataset.layoutItem = "illustrated-portrait";
      portrait.src = "../../../support-references/materials/T28576_03_glamorous-manga-portrait.png";
      portrait.alt = "";
      portrait.style.transform = `scale(${state.portraitScale})`;
      board.append(portrait);

      function fitText(key, text, className, box) {
        const element = document.createElement("div");
        element.className = `cover-text ${className}`;
        element.dataset.layoutItem = key;
        if (box.display !== false) element.dataset.displayItem = "true";
        element.textContent = text;
        if (box.left !== undefined) element.style.left = `${box.left * 100}%`;
        if (box.right !== undefined) element.style.right = `${box.right * 100}%`;
        if (box.center) {
          element.style.left = "50%";
          element.style.transform = "translateX(-50%)";
        }
        element.style.top = `${box.top * 100}%`;
        if (box.align === "right") element.style.textAlign = "right";
        board.append(element);
        window.SupportLayout.fitLine(element, {
          width: board.clientWidth * box.width,
          height: board.clientHeight * box.height,
          maxSize: board.clientHeight * box.max * (box.scale || 1),
          minSize: board.clientHeight * box.min,
          tracking: box.tracking ?? state.tracking,
        });
        element.style.letterSpacing = `${box.tracking ?? state.tracking}em`;
        return element;
      }

      function fitRows(key, value, className, rows, box) {
        const lines = String(value || "").split("\n").slice(0, rows.length);
        rows.forEach((row, index) => {
          fitText(`${key}-${index + 1}`, lines[index] || "", className, {
            ...box,
            top: row.top,
            height: row.height,
            scale: box.scale || 1,
          });
        });
      }

      fitText("cover-masthead", props.masthead ?? state.masthead ?? "Vogue",
        "masthead", { center: true, top: .033, width: .95, height: .255,
          max: .31, min: .09, scale: state.mastheadScale, tracking: -.035 });
      fitRows("cover-issue", props.issue ?? state.issue ?? "March\nIssue",
        "small-meta issue", [
          { top: .291, height: .019 }, { top: .309, height: .019 },
        ], { left: .037, width: .12, max: .016, min: .01,
          display: false, tracking: .025 });
      fitText("cover-submast", props.submast ?? state.submast ?? "Japan",
        "submast", { right: .04, top: .302, width: .15, height: .064,
          max: .056, min: .032, tracking: .01 });

      fitText("left-kicker", props.leftKicker ?? state.leftKicker ?? "Discover",
        "left-kicker", { left: .038, top: .355, width: .29, height: .072,
          max: .09, min: .055, scale: state.columnScale, tracking: -.035 });
      fitRows("left-story", props.leftStory ?? state.leftStory ?? "The New\nStreet Fashion\nTrends From",
        "left-story", [
          { top: .436, height: .058 }, { top: .511, height: .058 },
          { top: .586, height: .058 },
        ], { left: .04, width: .32, max: .055, min: .035,
          scale: state.columnScale, tracking: -.015 });
      fitText("accent-destination", props.destination ?? state.destination ?? "Tokyo",
        "accent-destination", { left: .038, top: .67, width: .28, height: .065,
          max: .078, min: .045, scale: state.columnScale, tracking: .075 });

      fitText("lower-kicker", props.lowerKicker ?? state.lowerKicker ?? "Reina Sato",
        "lower-kicker", { left: .038, top: .75, width: .30, height: .045,
          max: .055, min: .035, scale: state.columnScale, tracking: -.025 });
      fitRows("lower-story", props.lowerStory ?? state.lowerStory ?? "A study of\nshape, line and\nsilhouette",
        "lower-story", [
          { top: .816, height: .031 }, { top: .850, height: .031 },
          { top: .884, height: .031 },
        ], { left: .04, width: .31, max: .038, min: .028,
          scale: state.columnScale, tracking: -.01 });

      fitRows("feature-title", props.featureLines ?? state.featureLines ?? "Sakura\nYamaguchi",
        "feature-title", [
          { top: .51, height: .09 }, { top: .64, height: .09 },
        ], { right: .043, width: .50, max: .105, min: .055,
          scale: state.featureScale, align: "right", tracking: -.035 });
      fitRows("feature-note", props.featureNote ?? state.featureNote ?? "A study of\nshape and form\nin motion",
        "feature-note", [
          { top: .760, height: .036 }, { top: .803, height: .036 },
          { top: .846, height: .036 },
        ], { right: .045, width: .46, max: .039, min: .022,
          display: false, align: "right", tracking: .005 });
      fitText("cover-footer-lead", props.footerLead ?? state.footerLead ?? "Follow Us On Social Media",
        "small-meta footer-lead", { right: .045, top: .936, width: .30, height: .022,
          max: .019, min: .012, display: false, align: "right", tracking: .025 });
      fitText("cover-footer-note", props.footerNote ?? state.footerNote ?? "Facebook / Instagram / TikTok",
        "small-meta footer-note", { right: .045, top: .970, width: .33, height: .022,
          max: .017, min: .011, display: false, align: "right", tracking: .025 });
    },
    getContrast() { return window.SupportLayout.contrast(design.ink, design.paper); },
    getWarnings() { return design.warnings || []; },
  };
  window.VogueCover32 = design;
})();
