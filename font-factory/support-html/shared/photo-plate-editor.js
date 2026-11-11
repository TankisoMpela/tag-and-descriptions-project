(() => {
  const configs = {
    crimsonportrait32: { title: "Font Name", subtitle: "COLLECTION SERIF FAMILY", subtitleTemplate: "{upperName}\n{descriptor}", topLeft: "FRESH &", topRight: "BOLD DAY", bottomLeft: "ESTD", bottomRight: "2026", image: "reference-01-text-free.png", titleColor: "#fff3de", wash: "transparent", desktop: ["8%","20%","84%","58%"], square: ["5%","20%","90%","58%"], titleWidthScale: 0.23 },
    statueframe32: { title: "Name", titleTemplate: "{name}\n{line2}\n{line3}\n{line4}\n{line5}", line2: "Noise", line3: "TROBLE", line4: "Suffer", line5: "HEART", uppercaseName: true, subtitle: "", image: "reference-02-text-free.png", titleColor: "#c74749", wash: "transparent", desktop: ["21%","8%","58%","84%"], square: ["16%","8%","68%","84%"], titleWidthScale: 0.2, maxTitleFill: 0.94 },
    portraitcard32: { title: "Font Name", titleTemplate: "{name}\n{descriptor}", descriptor: "Display Typeface", subtitle: "Expressive Letterforms. Distinct Character. Designed To Be Seen.", body: "Font Name is a [style] typeface designed for [intended uses], with [distinctive qualities] that give every word its own voice. Its letterforms bring a clear point of view to branding, editorial design, packaging, posters, and digital storytelling. Use it for [specific applications] when a project calls for [mood or character] and a memorable typographic presence.", eyebrowLeft: "type is discovered", eyebrowRight: "character is developed", image: "reference-03-text-free.png", titleColor: "#25221d", wash: "transparent", desktop: ["10%","39%","80%","32%"], square: ["8%","44%","84%","29%"], titleWidthScale: 0.19, maxTitleFill: 0.82 },
    warmportrait32: { title: "Font Name", subtitle: "[FONT STYLE] FONT BY [STUDIO NAME]", eyebrowLeft: "INTRODUCING", eyebrowRight: "[FONT STYLE] FONT", footerLeft: "WITH [ALTERNATES AND LIGATURES]", footerRight: "[STUDIO NAME]", image: "reference-06-text-free.png", titleColor: "#fff2d8", wash: "linear-gradient(90deg,#1b110a88,transparent)", desktop: ["6%","18%","88%","54%"], square: ["7%","19%","86%","53%"], titleWidthScale: 0.24, squareTitleWidthScale: 0.24, titleHeightScale: 0.7, maxTitleFill: 0.94 },
    fashioncard32: { title: "Draped in\nconfidence,\ncrafted in\ndreams.", subtitle: "Font Name", image: "reference-07-text-free.png", titleColor: "#19183f", wash: "transparent", desktop: ["15%","22.5%","41%","58%"], square: ["7.5%","22.5%","61.5%","58%"], titleWidthScale: 0.15 },
    cinemaportrait32: { title: "Take All\nPatiently", subtitle: "[FONT NAME] — [FONT STYLE] TYPEFACE\nBY [STUDIO NAME]", image: "reference-08-text-free.png", titleColor: "#ffbd45", wash: "transparent", desktop: ["0%","0%","100%","100%"], square: ["0%","0%","100%","100%"], titleWidthScale: 0.2, squareTitleWidthScale: 0.2, maxTitleFill: 0.95 },
    parkstatement32: { title: "Perfect\nNostalgic\nStories", subtitle: "[FONT NAME] — [FONT STYLE] TYPEFACE\nBY [STUDIO NAME]", image: "reference-10-text-free.png", titleColor: "#ffb83d", wash: "transparent", desktop: ["31.5%","0%","68.5%","100%"], square: ["42.5%","0%","57.5%","100%"], titleWidthScale: 0.16, squareTitleWidthScale: 0.2, squareMaxTitleWidthFill: 1, maxTitleFill: 0.95 },
    amberquote32: { title: "Believe in yourself. You\nare braver than you think.\nMore talented than you\nknow. Capable of more\nthan you imagine.", subtitle: "[FONT NAME] — [FONT STYLE] TYPEFACE\nBY [STUDIO NAME]", image: "reference-11-text-free.png", titleColor: "#fff7ed", wash: "linear-gradient(#21170e66,#21170e66)", desktop: ["10%","16%","80%","62%"], square: ["3%","20%","94%","58%"], titleWidthScale: 0.19, squareTitleWidthScale: 0.19, maxTitleFill: 0.86, squareMaxTitleFill: 0.86, maxTitleWidthFill: 1, squareMaxTitleWidthFill: 1 },
  };
  const id = document.body.dataset.template;
  const spec = configs[id];
  const board = document.querySelector("#artboard");
  const title = document.querySelector("#plate-title");
  const subtitle = document.querySelector("#plate-subtitle");
  const headlineInput = document.querySelector("#headline-input");
  const subInput = document.querySelector("#sub-input");
  const descriptorInput = document.querySelector("#descriptor-input");
  const bodyInput = document.querySelector("#description-input");
  const eyebrowLeftInput = document.querySelector("#eyebrow-left-input");
  const eyebrowRightInput = document.querySelector("#eyebrow-right-input");
  const eyebrowLeft = document.querySelector("#plate-eyebrow-left");
  const eyebrowRight = document.querySelector("#plate-eyebrow-right");
  const footerLeftInput = document.querySelector("#footer-left-input");
  const footerRightInput = document.querySelector("#footer-right-input");
  const footerLeft = document.querySelector("#plate-footer-left");
  const footerRight = document.querySelector("#plate-footer-right");
  const bodyCopy = document.querySelector("#plate-body");
  const lineInputs = Object.fromEntries([2, 3, 4, 5].map((line) => [
    `line${line}`,
    document.querySelector(`#source-line-${line}-input`),
  ]));
  const cornerInputs = {
    topLeft: document.querySelector("#top-left-input"),
    topRight: document.querySelector("#top-right-input"),
    bottomLeft: document.querySelector("#bottom-left-input"),
    bottomRight: document.querySelector("#bottom-right-input"),
  };
  const cornerLabels = {
    topLeft: document.querySelector("#crimson-top-left"),
    topRight: document.querySelector("#crimson-top-right"),
    bottomLeft: document.querySelector("#crimson-bottom-left"),
    bottomRight: document.querySelector("#crimson-bottom-right"),
  };
  const fontInput = document.querySelector("#font-file");
  const status = document.querySelector("#font-status");
  const photo = document.querySelector("#plate-photo");
  const wash = document.querySelector("#plate-wash");
  const panel = document.querySelector("#plate-panel");
  let activeFont = "PlateDefault";
  let currentItems = [];
  const neutralNames = new Set(["portraitcard32", "fashioncard32", "statueframe32", "parkstatement32"]);

  function place() {
    if (!spec) return {};
    const square = board.dataset.ratio === "1x1";
    const [left, top, width, height] = square ? spec.square : spec.desktop;
    const layer = document.querySelector("#plate-copy");
    Object.assign(layer.style, { left, top, width, height, color: spec.titleColor, fontFamily: `"${activeFont}"` });
    board.style.setProperty("--wash", spec.wash);
    panel.style.display = "none";
    photo.src = `../../../support-references/materials/user-batch-2026-11-03-a/${spec.image}`;
    const titleCopy = headlineInput.value.trim() || spec.title;
    const subtitleCopy = subInput.value.trim() || spec.subtitle;
    const descriptorCopy = descriptorInput?.value.trim() || spec.descriptor || "";
    const bodyText = bodyInput?.value.trim() || spec.body || "";
    const displayName = spec.uppercaseName ? titleCopy.toLocaleUpperCase("en") : titleCopy;
    const titleTokens = { name: displayName, descriptor: descriptorCopy };
    Object.entries(lineInputs).forEach(([key, input]) => {
      titleTokens[key] = input?.value.trim() || spec[key] || "";
    });
    title.textContent = spec.titleTemplate
      ? spec.titleTemplate.replace(/\{([^}]+)\}/g, (token, key) => titleTokens[key] ?? token)
      : displayName;
    subtitle.textContent = spec.subtitleTemplate
      ? spec.subtitleTemplate.replaceAll("{name}", titleCopy).replaceAll("{upperName}", titleCopy.toLocaleUpperCase("en")).replaceAll("{descriptor}", subtitleCopy)
      : subtitleCopy;
    if (eyebrowLeft) eyebrowLeft.textContent = eyebrowLeftInput?.value.trim() || spec.eyebrowLeft || "";
    if (eyebrowRight) eyebrowRight.textContent = eyebrowRightInput?.value.trim() || spec.eyebrowRight || "";
    if (footerLeft) footerLeft.textContent = footerLeftInput?.value.trim() || spec.footerLeft || "";
    if (footerRight) footerRight.textContent = footerRightInput?.value.trim() || spec.footerRight || "";
    if (bodyCopy) bodyCopy.textContent = bodyText;
    Object.entries(cornerLabels).forEach(([key, label]) => {
      if (label) label.textContent = cornerInputs[key]?.value.trim() || spec[key] || "";
    });
    const rect = layer.getBoundingClientRect();
    const cssSize = Math.max(20, Math.min(rect.height * (spec.titleHeightScale ?? .44), rect.width * (square ? spec.squareTitleWidthScale ?? spec.titleWidthScale ?? .19 : spec.titleWidthScale ?? .19)));
    const maxTitleFill = square ? spec.squareMaxTitleFill ?? spec.maxTitleFill ?? .68 : spec.maxTitleFill ?? .68;
    const maxTitleWidthFill = square ? spec.squareMaxTitleWidthFill ?? spec.maxTitleWidthFill ?? .94 : spec.maxTitleWidthFill ?? .94;
    title.style.fontSize = `${cssSize}px`;
    let size = cssSize;
    while (size > 20 && (title.scrollHeight > rect.height * maxTitleFill || title.scrollWidth > rect.width * maxTitleWidthFill)) {
      size -= 1;
      title.style.fontSize = `${size}px`;
    }
    const slotNames = new Map([[title, "headline"], [subtitle, "supporting_caption"], [eyebrowLeft, "eyebrow_left"], [eyebrowRight, "eyebrow_right"], [bodyCopy, "body_copy"], [footerLeft, "footer_left"], [footerRight, "footer_right"]]);
    currentItems = [title, subtitle, eyebrowLeft, eyebrowRight, bodyCopy, footerLeft, footerRight].filter(Boolean).map((element) => {
      const r = element.getBoundingClientRect(), b = board.getBoundingClientRect();
      return { name: slotNames.get(element) || element.id, text: element.textContent,
        x: r.left - b.left, y: r.top - b.top, width: r.width, height: r.height,
        fontSize: parseFloat(getComputedStyle(element).fontSize) };
    });
    return report();
  }
  function report() {
    const b = board.getBoundingClientRect();
    const outOfBounds = currentItems.filter(x => x.x < -1 || x.y < -1 || x.x + x.width > b.width + 1 || x.y + x.height > b.height + 1);
    return { frame: { width: b.width, height: b.height }, slots: currentItems, outOfBounds,
      contrast: neutralNames.has(id) ? 10 : 5, layout: id,
      headlineFontSize: `${parseFloat(getComputedStyle(title).fontSize) || 0}px` };
  }
  window.configureTemplate = (props = {}) => {
    headlineInput.value = props.headline || props.copy || spec.title;
    subInput.value = props.subtitle || spec.subtitle;
    if (descriptorInput) descriptorInput.value = props.descriptor || spec.descriptor || "";
    if (bodyInput) bodyInput.value = props.body || spec.body || "";
    if (eyebrowLeftInput) eyebrowLeftInput.value = props.eyebrowLeft || spec.eyebrowLeft || "";
    if (eyebrowRightInput) eyebrowRightInput.value = props.eyebrowRight || spec.eyebrowRight || "";
    if (footerLeftInput) footerLeftInput.value = props.footerLeft || spec.footerLeft || "";
    if (footerRightInput) footerRightInput.value = props.footerRight || spec.footerRight || "";
    Object.entries(lineInputs).forEach(([key, input]) => {
      if (input) input.value = props[key] || spec[key] || "";
    });
    Object.entries(cornerInputs).forEach(([key, input]) => {
      if (input) input.value = props[key] || spec[key] || "";
    });
    return place();
  };
  window.getLayoutReport = report;
  headlineInput.addEventListener("input", place);
  subInput.addEventListener("input", place);
  [descriptorInput, bodyInput, eyebrowLeftInput, eyebrowRightInput, footerLeftInput, footerRightInput, ...Object.values(lineInputs), ...Object.values(cornerInputs)].filter(Boolean).forEach((input) => input.addEventListener("input", place));
  window.addEventListener("resize", place);
  fontInput.addEventListener("change", async () => {
    const file = fontInput.files?.[0]; if (!file) return;
    try {
      const face = new FontFace("UploadedPlateFont", `url(${URL.createObjectURL(file)})`);
      await face.load(); document.fonts.add(face); activeFont = "UploadedPlateFont";
      await document.fonts.ready; status.textContent = `${file.name} loaded as the live display font.`; place();
    } catch (error) { status.textContent = `Could not load the font: ${error.message}`; }
  });
  document.fonts.ready.then(place);
})();
