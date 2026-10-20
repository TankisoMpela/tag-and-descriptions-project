(function () {
  const design = {
    id: "storyteller32",
    title: "Storyteller",
    defaults: { scale: 1 },
    controls: [
      { key: "scale", label: "Editorial type scale", min: 0.82, max: 1.12, step: 0.01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");

      const lines = [
        { name: "story-title-1", className: "story-title-1", size: 83, text: '<span>Typography</span>' },
        { name: "story-title-2", className: "story-title-2", size: 75, text: '<span>Is </span><span class="red">The</span><span> Silent</span>' },
        { name: "story-title-3", className: "story-title-3", size: 76, text: '<span class="red">Story</span><span> Teller</span>' },
        { name: "story-title-4", className: "story-title-4", size: 79, text: '<span>Of </span><span class="red">Design</span><span>.</span>' },
      ];
      const titleRows = [];
      for (const spec of lines) {
        const line = document.createElement("div");
        line.className = `story-line ${spec.className}`;
        line.dataset.layoutItem = spec.name;
        line.dataset.displayItem = "true";
        line.innerHTML = spec.text;
        board.append(line);
        titleRows.push(line);
      }
      window.SupportLayout.fitStack(titleRows, {
        name: "story-title",
        board,
        left: .037,
        top: .025,
        width: .605,
        height: .435,
        gap: .024,
        maxSize: board.clientHeight * .112 * Number(props.scale ?? state.scale ?? 1),
        minSize: 24,
        tracking: -.035,
      });

      const hands = document.createElement("img");
      hands.className = "story-hands";
      hands.src = "../../../support-references/materials/T28576_05_hands-strip.png";
      hands.alt = "";
      hands.dataset.layoutItem = "story-hands-strip";
      board.append(hands);

      const copy = [
        { name: "story-copy-1", className: "story-copy-1", size: 45, html: 'Its <span class="red">Curves</span> And Lines' },
        { name: "story-copy-2", className: "story-copy-2", size: 46, html: 'Shape <span class="red">Meaning</span>' },
        { name: "story-copy-3", className: "story-copy-3", size: 47, html: '<span class="red">Before</span> Words' },
        { name: "story-copy-4", className: "story-copy-4", size: 48, html: 'Are <span class="red">Read</span>.' },
      ];
      const copyRows = [];
      for (const spec of copy) {
        const line = document.createElement("div");
        line.className = `story-line story-copy ${spec.className}`;
        line.dataset.layoutItem = spec.name;
        line.dataset.displayItem = "true";
        line.innerHTML = spec.html;
        board.append(line);
        copyRows.push(line);
      }
      window.SupportLayout.fitStack(copyRows, {
        name: "story-copy",
        board,
        left: .037,
        top: .625,
        width: .605,
        height: .315,
        gap: .022,
        maxSize: board.clientHeight * .072 * Number(props.scale ?? state.scale ?? 1),
        minSize: 20,
        tracking: -.025,
      });

      const portrait = document.createElement("img");
      portrait.className = "story-portrait";
      portrait.src = "../../../support-references/materials/T28576_05_artist-illustration.png";
      portrait.alt = "";
      portrait.dataset.layoutItem = "story-artist-illustration";
      board.append(portrait);

      const burst = document.createElementNS("http://www.w3.org/2000/svg", "svg");
      burst.setAttribute("viewBox", "0 0 120 160");
      burst.setAttribute("aria-hidden", "true");
      burst.classList.add("story-burst");
      burst.innerHTML = '<g fill="#ed1c2e"><path d="M65 160 62 83 72 82Z"/><path d="M70 151 76 88 83 91Z"/><path d="M80 153 89 101 96 105Z"/><path d="M91 158 103 112 109 117Z"/><path d="M49 153 50 91 57 90Z"/><path d="M35 158 40 105 47 106Z"/><path d="M22 158 31 118 37 120Z"/><path d="M9 157 22 132 27 136Z"/></g>';
      board.append(burst);

      const furniture = document.createElement("div");
      furniture.className = "story-furniture";
      furniture.dataset.layoutItem = "story-edition-mark";
      furniture.textContent = "Editorial Study  /  05";
      board.append(furniture);
    },
    getContrast() { return window.SupportLayout.contrast("#151515", "#fffefa"); },
    getWarnings() { return design.warnings || []; },
  };
  window.Storyteller32 = design;
})();
