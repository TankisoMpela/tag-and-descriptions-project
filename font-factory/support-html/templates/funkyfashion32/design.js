(function () {
  const defaults = {
    headlineOne: "Funky",
    headlineTwo: "Fashion",
    week: "Fashion\nWeek",
    paragraph: "To be fashionable is to rub elbows with every new clothing and accessory item that hits the Market. It can be daunting trying to do such a thing. Not to Mention it is so dull and time-consuming a thing to keep up with all the latest styles.",
    signature: "Sarah\nSchwartz",
    website: "www.funkyfashion.com",
    scale: 1,
    tracking: -0.045,
  };
  const design = {
    id: "funkyfashion32",
    title: "Funky Fashion",
    labelFace: "FunkyLabel",
    defaults,
    contrastException: {
      minimum: 2.5,
      rationale: "The reference uses warm cream type over punch-pink paper, supported by offset dark printer shadows.",
    },
    controls: [
      { key: "headlineOne", label: "Headline, first line", type: "text", value: defaults.headlineOne },
      { key: "headlineTwo", label: "Headline, second line", type: "text", value: defaults.headlineTwo },
      { key: "week", label: "Top-right label", type: "text", value: defaults.week },
      { key: "paragraph", label: "Right-side copy", type: "text", value: defaults.paragraph },
      { key: "signature", label: "Lower-left name", type: "text", value: defaults.signature },
      { key: "website", label: "Web address", type: "text", value: defaults.website },
      { key: "scale", label: "Display scale", min: 0.82, max: 1.12, step: 0.01 },
      { key: "tracking", label: "Headline spacing", min: -0.10, max: 0.01, step: 0.005 },
    ],
    render(board, state) {
      const props = state.props || {};
      design.warnings = props.warnings || [];
      board.replaceChildren();
      const square = board.dataset.ratio === "1x1";
      board.style.setProperty("--display-face", "SupportDisplay, Arial, sans-serif");
      board.style.setProperty("--label-face", design.labelFace || "FunkyLabel");

      const create = (name, className, text) => {
        const element = document.createElement("div");
        element.className = className;
        element.dataset.layoutItem = name;
        if (text !== undefined) element.textContent = text;
        board.append(element);
        return element;
      };
      const circle = create("funky-orange-portrait-disc", "funky-circle");
      circle.setAttribute("aria-hidden", "true");
      const portrait = create("funky-circular-fashion-portrait", "funky-portrait");
      const image = document.createElement("img");
      image.src = "../../../support-references/materials/T26289_01_orange-fashion-cutout.png";
      image.alt = "";
      portrait.append(image);

      const headline = (key, fallback, name, className, top, width, height) => {
        const element = create(name, "funky-headline " + className, props[key] ?? state[key] ?? fallback);
        const tracking = square ? .01 : Number(state.tracking);
        element.dataset.displayItem = "true";
        element.style.top = (square ? (name === "funky-headline-first-line" ? 6.5 : 22.5) : top) + "%";
        element.style.left = "4.6%";
        window.SupportLayout.fitLine(element, {
          width: board.clientWidth * width,
          height: board.clientHeight * (square ? .16 : height),
          maxSize: board.clientHeight * (square ? .24 : .34) * state.scale,
          minSize: board.clientHeight * (square ? .055 : .075),
          tracking,
          inkAware: true,
        });
        element.style.letterSpacing = tracking + "em";
        return element;
      };
      headline("headlineOne", defaults.headlineOne, "funky-headline-first-line", "funky-title-one", 7.4, .44, .18);
      const second = headline("headlineTwo", defaults.headlineTwo, "funky-headline-second-line", "funky-title-two", 24.3, .42, .20);
      second.style.left = "4.7%";

      const weekValue = String(props.week ?? state.week ?? defaults.week).trim();
      const splitLines = weekValue.split(/\s*\n\s*|\s*\/\s*/).filter(Boolean);
      const words = splitLines.length > 1 ? splitLines : weekValue.split(/\s+/).filter(Boolean);
      const splitAt = Math.ceil(words.length / 2);
      const weekLines = [words.slice(0, splitAt).join(" "), words.slice(splitAt).join(" ")].filter(Boolean);
      weekLines.forEach((text, index) => {
        const line = create("funky-fashion-week-line-" + (index + 1), "funky-side-line funky-side-line-" + (index ? "two" : "one"), text);
        const tracking = square ? .01 : Number(state.tracking);
        window.SupportLayout.fitLine(line, {
          width: board.clientWidth * .185,
          height: board.clientHeight * .072,
          maxSize: board.clientHeight * .083 * state.scale,
          minSize: board.clientHeight * .04,
          tracking,
          inkAware: true,
        });
        line.style.letterSpacing = tracking + "em";
      });
      const dots = create("funky-dotted-annotation", "funky-dots");
      dots.setAttribute("aria-hidden", "true");
      const arrow = create("funky-pointing-arrow", "funky-arrow");
      arrow.innerHTML = '<svg viewBox="0 0 150 80" aria-hidden="true"><path d="M5 40h119M94 8l34 32-34 32" fill="none" stroke="#17131a" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>';
      const bolt = create("funky-lightning-sticker", "funky-bolt");
      bolt.innerHTML = '<svg viewBox="0 0 160 300" aria-hidden="true"><path d="M92 12 22 126 70 126 46 274 145 96 94 99Z" fill="#5a2bb0"/><path d="M86 15 19 124 65 124 45 266 136 94 89 98Z" fill="#16a7e4"/><path d="M80 17 15 121 61 121 43 257 127 93 84 97Z" fill="#17131a"/><path d="M75 21 16 119 59 119 41 247 118 91 80 94Z" fill="#ffe22b" stroke="#17131a" stroke-width="4" stroke-linejoin="round"/></svg>';
      for (const [name, className] of [["funky-lightning-spark-top", "funky-spark-one"], ["funky-lightning-spark-bottom", "funky-spark-two"]]) {
        const spark = create(name, "funky-spark " + className);
        spark.innerHTML = '<svg viewBox="0 0 100 100" aria-hidden="true"><path d="M50 0 60 39 100 50 60 61 50 100 40 61 0 50 40 39Z" fill="currentColor"/></svg>';
      }
      const sticker = create("funky-smiley-sticker", "funky-sticker");
      sticker.innerHTML = '<svg viewBox="0 0 260 300" role="img" aria-label="Layered yellow smiley sticker"><path d="M129 18C171 18 192 31 202 54c31 6 41 30 37 58l-5 98c-2 40-29 62-67 67-49 7-104-10-123-42-12-20-6-43 5-57-13-32-16-88 3-119C68 31 94 18 129 18Z" transform="translate(15 17)" fill="#5632a9" stroke="#5632a9" stroke-width="18" stroke-linejoin="round"/><path d="M129 18C171 18 192 31 202 54c31 6 41 30 37 58l-5 98c-2 40-29 62-67 67-49 7-104-10-123-42-12-20-6-43 5-57-13-32-16-88 3-119C68 31 94 18 129 18Z" transform="translate(8 10)" fill="#12a8e2" stroke="#12a8e2" stroke-width="17" stroke-linejoin="round"/><path d="M129 18C171 18 192 31 202 54c31 6 41 30 37 58l-5 98c-2 40-29 62-67 67-49 7-104-10-123-42-12-20-6-43 5-57-13-32-16-88 3-119C68 31 94 18 129 18Z" transform="translate(3 5)" fill="#e93994" stroke="#e93994" stroke-width="16" stroke-linejoin="round"/><path d="M129 18C171 18 192 31 202 54c31 6 41 30 37 58l-5 98c-2 40-29 62-67 67-49 7-104-10-123-42-12-20-6-43 5-57-13-32-16-88 3-119C68 31 94 18 129 18Z" fill="#fff9ed" stroke="#fff9ed" stroke-width="20" stroke-linejoin="round"/><path d="M129 18C171 18 192 31 202 54c31 6 41 30 37 58l-5 98c-2 40-29 62-67 67-49 7-104-10-123-42-12-20-6-43 5-57-13-32-16-88 3-119C68 31 94 18 129 18Z" fill="#ffdf18" stroke="#22135b" stroke-width="9" stroke-linejoin="round"/><ellipse cx="91" cy="105" rx="10" ry="20" fill="#26146a"/><ellipse cx="157" cy="103" rx="10" ry="20" fill="#26146a"/><path d="M73 146c4 33 23 43 47 26 9-7 17-8 25 1 22 24 49 7 50-22" fill="none" stroke="#26146a" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></svg>';

      const paragraph = create("funky-fashion-description", "funky-copy", props.paragraph ?? state.paragraph ?? defaults.paragraph);
      const signature = create("funky-designer-signature", "funky-signature", props.signature ?? state.signature ?? defaults.signature);
      const website = create("funky-web-address", "funky-website", props.website ?? state.website ?? defaults.website);
      [paragraph, signature, website].forEach((element) => element.setAttribute("spellcheck", "false"));
      if (square) {
        const fitBlock = (element, minSize, maxSize) => {
          let low = minSize;
          let high = maxSize;
          let best = 0;
          for (let attempt = 0; attempt < 18; attempt += 1) {
            const size = (low + high) / 2;
            element.style.fontSize = `${size}px`;
            if (element.scrollHeight <= element.clientHeight + 1 && element.scrollWidth <= element.clientWidth + 1) {
              best = size;
              low = size;
            } else high = size;
          }
          element.style.fontSize = `${best || minSize}px`;
          if (!best) element.dataset.fitFailure = "minimum-size-exceeds-safe-area";
          return best;
        };
        fitBlock(paragraph, board.clientHeight * .015, board.clientHeight * .031);
        window.SupportLayout.fitLine(signature, {
          width: board.clientWidth * .34, height: board.clientHeight * .08,
          maxSize: board.clientHeight * .05, minSize: board.clientHeight * .025,
          tracking: .01, inkAware: true,
        });
        window.SupportLayout.fitLine(website, {
          width: board.clientWidth * .40, height: board.clientHeight * .04,
          maxSize: board.clientHeight * .027, minSize: board.clientHeight * .016,
          tracking: .01, inkAware: true,
        });
      }
    },
    getContrast() { return window.SupportLayout.contrast("#fff2d8", "#eb637a"); },
    getWarnings() { return design.warnings || []; },
  };
  window.FunkyFashion32 = design;
})();
