(function () {
  const backgroundUrl = "../../../support-references/materials/reference-batch-2026-10-26-e/sexyshout-user-photo.png";
  const rows = [
    { key: "lineOne", top: .015, squareTop: .045, width: .78, squareWidth: .88, max: .45, squareMax: .43 },
    { key: "lineTwo", top: .365, squareTop: .505, width: .88, squareWidth: .90, max: .49, squareMax: .48 },
  ];

  function createSexyShout() {
    const defaults = {
      lineOne: "Sexy",
      lineTwo: "Shout",
      displayScale: 1,
      useItalicSibling: false,
    };
    const design = {
      id: "sexyshout32",
      title: "Sexy Shout",
      literalKeys: rows.map((row) => row.key),
      defaults,
      controls: [
        { key: "lineOne", type: "text", label: "Upper word" },
        { key: "lineTwo", type: "text", label: "Lower word" },
        { key: "displayScale", label: "Display scale", min: .82, max: 1.12, step: .01 },
      ],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        const scale = Number(state.displayScale ?? 1);
        const familyItalic = Boolean(
          state.useItalicSibling &&
          window.SupportFamilyAvailable?.includes("SupportFamily1"),
        );
        board.classList.add("user-reference-sexyshout");
        board.classList.toggle("ss-square", square);
        board.replaceChildren();

        const photo = document.createElement("img");
        photo.className = "ss-photo";
        photo.src = backgroundUrl;
        photo.alt = "";
        photo.setAttribute("aria-hidden", "true");
        photo.draggable = false;
        board.append(photo);

        const fitted = rows.map((spec, index) => {
          const line = document.createElement("div");
          line.className = "ss-line";
          if (familyItalic) line.classList.add("ss-family-italic");
          line.dataset.layoutItem = `sexyshout32-${spec.key}`;
          line.dataset.displayItem = "true";
          line.textContent = String(state[spec.key] ?? defaults[spec.key]);
          line.style.top = `${(square ? spec.squareTop : spec.top) * 100}%`;
          const width = square ? spec.squareWidth : spec.width;
          line.style.width = `${width * 100}%`;
          line.style.left = `${((1 - width) / 2) * 100}%`;
          board.append(line);
          return window.SupportLayout.fitLine(line, {
            width: board.clientWidth * width,
            height: board.clientHeight * (index === 0 ? (square ? .46 : .49) : (square ? .46 : .59)),
            maxSize: board.clientHeight * (square ? spec.squareMax : spec.max) * scale,
            minSize: 34,
            tracking: -.025,
          });
        });

        design.headlineFontSize = `${Math.max(...fitted)}px`;
        design.warnings = board.querySelectorAll(".ss-line[data-fit-failure]").length
          ? ["One or more words cannot fit its safe area at the minimum type size."]
          : [];
      },
      getContrast() {
        return window.SupportLayout.contrast("#fffdf9", "#515151");
      },
      getWarnings() {
        return design.warnings;
      },
    };
    return design;
  }

  function bindItalicFamily() {
    const input = document.getElementById("italic-file");
    const status = document.getElementById("italic-status");
    let face = null;
    let objectUrl = "";
    input?.addEventListener("change", async () => {
      const file = input.files?.[0];
      if (!file) return;
      if (status) status.textContent = `Loading ${file.name} as the optional real Italic family member…`;
      if (face) document.fonts.delete(face);
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      objectUrl = URL.createObjectURL(file);
      try {
        face = new FontFace("SupportFamily1", `url("${objectUrl}")`);
        await face.load();
        document.fonts.add(face);
        window.SupportFamilyAvailable = [...new Set([
          ...(window.SupportFamilyAvailable || []), "SupportFamily1",
        ])];
        await document.fonts.ready;
        window.configureTemplate({ useItalicSibling: true });
        if (status) status.textContent = `Loaded ${file.name}; the words use that actual family member.`;
      } catch (_error) {
        window.configureTemplate({ useItalicSibling: false });
        if (status) status.textContent = `Could not load ${file.name}. Choose an actual Italic file from the same family.`;
      }
    });
  }

  window.UserReferenceBatchK = {
    ids: ["sexyshout32"],
    create(id) {
      if (id === "sexyshout32") return createSexyShout();
      throw new Error(`Unknown reference template: ${id}`);
    },
    bindItalicFamily,
  };
})();
