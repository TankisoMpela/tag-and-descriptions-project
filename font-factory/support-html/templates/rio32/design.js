(function () {
  function titleCase(value) {
    return String(value ?? "").split(/(\s+)/u).map((part) => {
      if (!part || /^\s+$/u.test(part)) return part;
      const match = part.match(/^([^\p{L}\p{N}]*)([\p{L}\p{N}])([\s\S]*)$/u);
      if (!match) return part;
      return match[1] + match[2].toLocaleUpperCase("en") + match[3].toLocaleLowerCase("en");
    }).join("");
  }

  const design = {
    id: "rio32",
    title: "Rio At Dusk",
    defaults: {
      titleThe: "The",
      titleCity: "Janeiro",
      subtitle: "The Weekend Holiday Trip",
      booking: "Book Now",
      footer: "Happiness Consists Of Living Each Day As If It Were The First Day\nOf Your Honeymoon And The Last Day Of Your Vacation\nTrust Your Holiday Plans With Us",
      imageScale: 1,
      imageX: 50,
      imageY: 50,
      titleScale: 1,
      subtitleScale: 1,
      footerScale: 1,
      cream: "#f6efdc",
      shadow: "#241c19",
      warnings: [],
    },
    controls: [
      { key: "titleThe", label: "Title Lead", type: "text" },
      { key: "titleCity", label: "Destination", type: "text" },
      { key: "subtitle", label: "Subtitle", type: "text" },
      { key: "booking", label: "Booking Button", type: "text" },
      { key: "footer", label: "Closing Copy", type: "textarea", rows: 3 },
      { key: "titleScale", label: "Destination Scale", min: .84, max: 1.12, step: .01 },
      { key: "subtitleScale", label: "Subtitle Scale", min: .82, max: 1.12, step: .01 },
      { key: "imageScale", label: "Panorama Zoom", min: 1, max: 1.18, step: .01 },
      { key: "imageX", label: "Panorama Horizontal Position", min: 0, max: 100, step: 1 },
      { key: "imageY", label: "Panorama Vertical Position", min: 0, max: 100, step: 1 },
      { key: "footerScale", label: "Closing Copy Scale", min: .8, max: 1.2, step: .01 },
    ],
    render(board, state) {
      const props = state.props || state;
      design.warnings = props.warnings || [];
      board.replaceChildren();
      board.style.setProperty("--rio-cream", props.cream ?? state.cream ?? "#f6efdc");
      board.style.setProperty("--rio-shadow", props.shadow ?? state.shadow ?? "#241c19");
      design.currentCream = props.cream ?? state.cream ?? "#f6efdc";
      design.currentShadow = props.shadow ?? state.shadow ?? "#241c19";
      board.style.setProperty("--rio-photo-scale", String(props.imageScale ?? state.imageScale ?? 1));
      board.style.setProperty("--rio-photo-x", `${Number(props.imageX ?? state.imageX ?? 50)}%`);
      board.style.setProperty("--rio-photo-y", `${Number(props.imageY ?? state.imageY ?? 50)}%`);
      board.style.setProperty("--rio-label-face", design.labelFace
        ? `"${design.labelFace}"`
        : "RioLabel, sans-serif");

      const addText = (parent, className, text, itemName, display = false) => {
        const element = document.createElement("span");
        element.className = className;
        element.textContent = text;
        element.dataset.layoutItem = itemName;
        if (display) element.dataset.displayItem = "true";
        parent.append(element);
        return element;
      };

      const brand = document.createElement("div");
      brand.className = "rio-brand";
      brand.dataset.layoutItem = "travel-mark";
      addText(brand, "", "Rio", "brand-city");
      addText(brand, "", "Travel", "brand-type");
      board.append(brand);

      const navigation = document.createElement("nav");
      navigation.className = "rio-navigation";
      navigation.setAttribute("aria-label", "Main navigation");
      navigation.dataset.layoutItem = "navigation";
      ["Home", "Catalog", "Contact"].forEach((label, index) => {
        const item = addText(navigation, "", label, `navigation-${index + 1}`);
        item.setAttribute("aria-label", label);
      });
      board.append(navigation);

      const titleLead = titleCase(props.titleThe ?? state.titleThe ?? "The");
      const city = titleCase(props.titleCity ?? state.titleCity ?? "Janeiro");
      const titleLeadRow = document.createElement("div");
      titleLeadRow.className = "rio-title-the";
      titleLeadRow.dataset.layoutItem = "title-lead-row";
      const leadText = addText(titleLeadRow, "rio-display-line", titleLead,
        "title-lead", true);
      board.append(titleLeadRow);

      const titleCityRow = document.createElement("div");
      titleCityRow.className = "rio-title-city";
      titleCityRow.dataset.layoutItem = "destination-row";
      const cityText = addText(titleCityRow, "rio-display-line rio-display-line--city",
        city, "destination-title", true);
      board.append(titleCityRow);

      const subtitle = addText(board, "rio-subtitle",
        titleCase(props.subtitle ?? state.subtitle ?? "The Weekend Holiday Trip"),
        "destination-subtitle");
      const button = addText(board, "rio-booking",
        titleCase(props.booking ?? state.booking ?? "Book Now"), "booking-button");
      button.setAttribute("role", "button");
      button.setAttribute("aria-label", button.textContent);

      const footerText = String(props.footer ?? state.footer ?? design.defaults.footer)
        .split(/\n/u).map(titleCase).filter(Boolean);
      const footer = document.createElement("div");
      footer.className = "rio-footer";
      footer.dataset.layoutItem = "closing-copy";
      const footerLines = footerText.slice(0, 3).map((line, index) =>
        addText(footer, "rio-footer-line", line, `closing-line-${index + 1}`));
      board.append(footer);

      const titleScale = Number(props.titleScale ?? state.titleScale ?? 1);
      const subtitleScale = Number(props.subtitleScale ?? state.subtitleScale ?? 1);
      const footerScale = Number(props.footerScale ?? state.footerScale ?? 1);
      window.SupportLayout.fitLine(leadText, {
        width: board.clientWidth * .22,
        height: board.clientHeight * .09,
        maxSize: board.clientHeight * .082 * titleScale,
        minSize: board.clientHeight * .035,
        tracking: -.02,
        inkAware: true,
      });
      const citySize = window.SupportLayout.fitLine(cityText, {
        width: board.clientWidth * .72,
        height: board.clientHeight * .19,
        maxSize: board.clientHeight * .18 * titleScale,
        minSize: board.clientHeight * .06,
        tracking: -.045,
        inkAware: true,
      });
      cityText.style.fontSize = `${citySize}px`;
      window.SupportLayout.fitLine(subtitle, {
        width: board.clientWidth * .70,
        height: board.clientHeight * .066,
        maxSize: board.clientHeight * .061 * subtitleScale,
        minSize: 10,
        tracking: .035,
        inkAware: true,
      });
      window.SupportLayout.fitLine(button, {
        width: board.clientWidth * .132,
        height: board.clientHeight * .052,
        maxSize: board.clientHeight * .043,
        minSize: 9,
        tracking: .015,
        inkAware: true,
      });
      if (footerLines.length) {
        window.SupportLayout.fitLinesTogether(footerLines, {
          width: board.clientWidth * .84,
          height: board.clientHeight * .026,
          maxSize: board.clientHeight * .0225 * footerScale,
          minSize: 8,
          tracking: .014,
          inkAware: true,
        });
      }
      for (const item of navigation.children) {
        window.SupportLayout.fitLine(item, {
          width: board.clientWidth * .13,
          height: board.clientHeight * .044,
          maxSize: board.clientHeight * .038,
          minSize: 8,
          tracking: .035,
          inkAware: true,
        });
      }
      for (const item of brand.children) {
        window.SupportLayout.fitLine(item, {
          width: board.clientWidth * .14,
          height: board.clientHeight * .052,
          maxSize: board.clientHeight * .05,
          minSize: 8,
          tracking: .08,
          inkAware: true,
        });
      }
      design.headlineFontSize = `${citySize}px`;
    },
    getContrast() {
      return window.SupportLayout.contrast(this.currentCream || "#f6efdc",
        this.currentShadow || "#241c19");
    },
    contrastException: {
      minimum: 4.5,
      rationale: "Cream lettering remains above the darkened panorama for clear reading.",
    },
    getWarnings() { return design.warnings || []; },
  };
  window.Rio32 = design;
})();
