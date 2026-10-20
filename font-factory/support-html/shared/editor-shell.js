(function () {
  function titleCaseCopy(value) {
    let text = String(value ?? "");
    if (/^(?:ABCDEFGHIJKLM|NOPQRSTUVWXYZ)(?:\n(?:ABCDEFGHIJKLM|NOPQRSTUVWXYZ))*$/u.test(text)) return text;
    const urls = [];
    text = text.replace(/(?:https?:\/\/|www\.)[^\s]+/giu, (url) => {
      const marker = `\uE000${urls.length}\uE001`;
      urls.push(url);
      return marker;
    });
    text = text.replace(/\p{L}+(?:['’]\p{L}+)*/gu, (word) => {
      const initial = word.slice(0, 1).toLocaleUpperCase("en");
      const rest = word.slice(1);
      return initial + (word === word.toLocaleUpperCase("en")
        ? rest.toLocaleLowerCase("en") : rest);
    });
    return text.replace(/\uE000(\d+)\uE001/gu, (_match, index) => urls[Number(index)]);
  }

  function titleCaseValues(values, design) {
    const literalKeys = new Set(design.literalKeys || []);
    if (design.id === "contour32") ["lineOne", "lineTwo"].forEach((key) => literalKeys.add(key));
    if (design.id === "weightfamily32") ["row1", "row2", "row3"].forEach((key) => literalKeys.add(key));
    if (design.id === "mangosboard32") literalKeys.add("glyphs");
    return Object.fromEntries(Object.entries(values).map(([key, value]) => [
      key,
      typeof value === "string" && !literalKeys.has(key)
        ? titleCaseCopy(value) : value,
    ]));
  }

  function start(design) {
    const board = document.getElementById("artboard");
    const controls = document.getElementById("template-controls");
    const fontInput = document.getElementById("font-file");
    const fontStatus = document.getElementById("font-status");
    const warningPanel = document.createElement("div");
    warningPanel.className = "content-warnings";
    warningPanel.setAttribute("role", "status");
    warningPanel.setAttribute("aria-live", "polite");
    controls?.after(warningPanel);
    const ratioControls = document.createElement("div");
    ratioControls.className = "frame-ratio-controls";
    ratioControls.setAttribute("aria-label", "Artboard proportions");
    const ratios = [
      ["3x2", "3:2 Landscape"],
      ["1x1", "1:1 Square"],
    ];
    const buttons = new Map();
    for (const [ratio, label] of ratios) {
      const button = document.createElement("button");
      button.type = "button";
      button.textContent = label;
      button.dataset.ratio = ratio;
      button.setAttribute("aria-pressed", "false");
      button.addEventListener("click", () => setRatio(ratio));
      ratioControls.append(button);
      buttons.set(ratio, button);
    }
    board.closest(".artboard-frame")?.before(ratioControls);
    const defaults = { ...design.defaults };
    for (const control of design.controls || []) {
      if (defaults[control.key] === undefined && typeof control.value === "string") {
        defaults[control.key] = control.value;
      }
    }
    const state = titleCaseValues(defaults, design);

    function syncControls() {
      for (const control of design.controls || []) {
        const element = controls.querySelector(`[name="${control.key}"]`);
        if (element) element.value = state[control.key];
      }
    }

    function render(values = {}) {
      Object.assign(state, values);
      design.render(board, state);
      syncControls();
      const report = window.getLayoutReport();
      warningPanel.replaceChildren();
      for (const message of report.contentWarnings || []) {
        const note = document.createElement("p");
        note.textContent = message;
        warningPanel.append(note);
      }
      return report;
    }

    function setRatio(ratio) {
      if (!ratios.some(([available]) => available === ratio)) return;
      board.dataset.ratio = ratio;
      document.documentElement.dataset.supportRatio = ratio;
      const aspect = ratio === "1x1" ? "1 / 1" : "3 / 2";
      board.style.aspectRatio = aspect;
      const frame = board.closest(".artboard-frame");
      if (frame) frame.style.aspectRatio = aspect;
      for (const [key, button] of buttons) {
        button.setAttribute("aria-pressed", String(key === ratio));
      }
      render();
    }

    for (const control of design.controls || []) {
      const field = document.createElement("label");
      field.className = "editor-control";
      field.htmlFor = `setting-${control.key}`;
      const title = document.createElement("span");
      title.textContent = control.label;
      const input = document.createElement(
        control.type === "textarea" ? "textarea" : "input",
      );
      input.id = `setting-${control.key}`;
      input.name = control.key;
      if (control.type !== "textarea") input.type = control.type || "range";
      if (control.type === "textarea") input.rows = control.rows || 3;
      if (control.min !== undefined) input.min = control.min;
      if (control.max !== undefined) input.max = control.max;
      if (control.step !== undefined) input.step = control.step;
      if (control.type === "color") input.value = control.value;
      input.value = state[control.key] ?? control.value;
      input.addEventListener("input", () => {
        const value = control.type === "color" || control.type === "text" ||
          control.type === "textarea"
          ? input.value
          : Number(input.value);
        render({ [control.key]: value });
      });
      field.append(title, input);
      controls.append(field);
    }

    fontInput?.addEventListener("change", async () => {
      const file = fontInput.files?.[0];
      if (!file) return;
      fontStatus.textContent = "Loading font…";
      const url = URL.createObjectURL(file);
      const face = new FontFace("SupportDisplay", `url("${url}")`);
      try {
        await face.load();
        document.fonts.add(face);
        document.documentElement.style.setProperty("--display-face", "SupportDisplay");
        await document.fonts.ready;
        render();
        fontStatus.textContent = `loaded as the live display font: ${file.name}`;
      } catch (error) {
        fontStatus.textContent = `Could not load ${file.name}: ${error.message}`;
      }
    });

    window.configureTemplate = (values = {}) => render(titleCaseValues(values, design));
    window.setSupportRatio = setRatio;
    window.getLayoutReport = () => window.SupportLayout.boundsReport(board, design);
    document.title = `${design.title} — Support Layout Studio`;
    render();
    setRatio(board.dataset.ratio || document.documentElement.dataset.supportRatio || "3x2");
    let resizeFrame = 0;
    window.addEventListener("resize", () => {
      cancelAnimationFrame(resizeFrame);
      resizeFrame = requestAnimationFrame(() => render());
    }, { passive: true });
  }

  window.SupportEditor = { start };
})();
