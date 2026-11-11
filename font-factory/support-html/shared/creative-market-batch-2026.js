(function () {
  const root = "../../../support-references/materials/creative-market-batch-2026-11-11/";
  const config = {
    bottleoffer32: { title: "Bottle Offer", ref: "13-o.png", subtitle: "A layered ligature specimen" },
    bootzyfear32: { title: "Fear And Failure", ref: "bootzy-clean-tm7-o.png", asset: "bootzy-punk-character-transparent.png", subtitle: "An illustrated phrase poster" },
    bootzyalmost32: { title: "Almost", ref: "bootzy-clean-tm4-o.png", subtitle: "A two-weight word study" },
    bootzygraphic32: { title: "Graphic Design Is Easy", ref: "bootzy-clean-tm12-o.png", subtitle: "A bright editorial statement" },
    bootzybunny32: { title: "Your Love Is Weird", ref: "bootzy-clean-tm8-o.png", asset: "bootzy-rabbit-transparent.png", subtitle: "A hand-drawn character poster" },
    quadfont32: { title: "Four Font Moods", ref: "3-o.png", subtitle: "A four-panel type study" },
    mythicallions32: { title: "Sea Lions", ref: "mythical-romance-font-06-o.png", asset: "mythical-romance-text-free-plate.png", subtitle: "An archival coastal display poster" },
    lifeinblackwhite32: { title: "Life In Black And White", ref: "fantasy-magist-font-05-o.png", asset: "fantasy-magist-text-free-plate.png", subtitle: "A portrait-led serif poster" },
    romanstrips32: { title: "Roman Noir Specimen", ref: "serif-display-font-roman-noirs-04-o.png", asset: "roman-noirs-text-free-plate.png", subtitle: "A ruled editorial specimen sheet" },
    floraltriptych32: { title: "Flowers Are Nature’s Poetry", ref: "fegiran-4-o.png", asset: "fegiran-4-text-free-plate.png", subtitle: "A three-card botanical showcase" },
    homequote32: { title: "Home Is More Than A Place", ref: "fegiran-6-o.png", asset: "fegiran-6-text-free-plate.png", subtitle: "A quiet home and lifestyle poster" },
  };

  function add(board, text, key, className, box, maxSize, options = {}) {
    const el = document.createElement("div");
    el.className = `cmr-copy ${className || ""}`;
    el.dataset.layoutItem = key;
    if (options.display !== false) el.dataset.displayItem = "true";
    const copyMarkup = options.segments
      ? options.segments.map(([letter, color]) => `<span style="color:${color}">${letter}</span>`).join("")
      : null;
    if (options.stretch) {
      el.innerHTML = `<span class="cmr-stretched" style="transform:scaleX(${options.stretch}) skewX(${options.skew ?? -4}deg);transform-origin:${options.align === "left" ? "left center" : options.align === "right" ? "right center" : "center"}">${copyMarkup || text}</span>`;
    } else if (copyMarkup) el.innerHTML = copyMarkup;
    else el.textContent = text;
    Object.assign(el.style, {
      left: `${box.x * 100}%`, top: `${box.y * 100}%`,
      width: `${box.w * 100}%`, height: `${box.h * 100}%`,
      color: options.color || "#111111",
      textAlign: options.align || "center",
      justifyContent: options.align === "left" ? "flex-start" : options.align === "right" ? "flex-end" : "center",
      fontFamily: options.face || "SupportDisplay, Georgia, serif",
      fontWeight: options.weight || "400",
      fontStyle: options.italic ? "italic" : "normal",
    });
    board.append(el);
    if (options.display !== false) {
      window.SupportLayout.fitLine(el, {
        width: board.clientWidth * box.w * .96,
        height: board.clientHeight * box.h * .9,
        maxSize: board.clientHeight * maxSize,
        minSize: Math.max(18, board.clientHeight * maxSize * .36),
        tracking: options.tracking ?? -.025,
      });
    }
    return el;
  }

  function art(board, filename, className) {
    const img = document.createElement("img");
    img.className = className;
    img.src = new URL(root + filename, document.baseURI).href;
    img.alt = "";
    img.draggable = false;
    board.append(img);
    return img;
  }

  function create(id) {
    const info = config[id];
    if (!info) throw new Error(`Unknown Creative Market reference template: ${id}`);
    const design = {
      id,
      title: info.title,
      defaults: {},
      controls: [],
      warnings: [],
      render(board, state) {
        const square = board.dataset.ratio === "1x1";
        board.className = `cmr-artboard cmr-${id}${square ? " is-square" : ""}`;
        board.replaceChildren();
        if (info.asset) {
          const isCutout = id === "bootzyfear32" || id === "bootzybunny32";
          art(board, info.asset, isCutout ? "cmr-illustration" : "cmr-photo-plate");
        }
        const p = state.props || state;
        design.warnings = p.warnings || [];
        const c = (text, key, box, max, opts = {}) => add(board, text, key, "", box, max, opts);
        switch (id) {
          case "bottleoffer32":
            c("EQUIPPED WITH LIGATURES", "bottle-label", {x:.1,y:.075,w:.8,h:.09}, .085, {face:"Arial,sans-serif",weight:"800",italic:true,color:"#feff0b",tracking:-.025});
            c("Bottle", "bottle-word", {x:.12,y:.2,w:.76,h:.39}, square?.30:.45, {weight:"700",italic:true,tracking:-.065,stretch:square?1.02:1.5,segments:[["B","#fd6280"],["o","#fd6280"],["t","#feff0b"],["t","#feff0b"],["l","#fd6280"],["e","#fd6280"]]});
            c("Offer", "offer-word", {x:.11,y:.49,w:.78,h:.42}, square?.31:.43, {weight:"700",italic:true,tracking:-.065,stretch:square?1.02:1.4,segments:[["O","#fd6280"],["f","#feff0b"],["f","#feff0b"],["e","#fd6280"],["r","#fd6280"]]});
            break;
          case "bootzyfear32": {
            c("I live in fear", "fear-line", {x:.045,y:.12,w:.37,h:.16}, .16, {align:"left",weight:"700",tracking:-.055});
            c("I have no beer", "beer-line", {x:.49,y:.055,w:.47,h:.15}, .14, {weight:"700",tracking:-.055});
            c("I sleep", "jail-line-1", {x:.075,y:square?.64:.6,w:.28,h:.095}, .095, {align:"left",weight:"700",tracking:-.045});
            c("in jails", "jail-line-2", {x:.075,y:square?.735:.685,w:.28,h:.095}, .095, {align:"left",weight:"700",tracking:-.045});
            c("and everything fails", "fails-line", {x:.33,y:square?.82:.79,w:.63,h:.13}, .12, {weight:"700",tracking:-.065});
            break;
          }
          case "bootzyalmost32":
            c("Almost", "almost-heavy", {x:.04,y:.09,w:.92,h:.4}, .39, {weight:"700",align:"center",tracking:-.06,stretch:square?1:1.3});
            c("Almost", "almost-light", {x:.04,y:.49,w:.92,h:.4}, .39, {weight:"400",align:"center",tracking:-.055,stretch:square?1:1.3});
            break;
          case "bootzygraphic32":
            c("Graphic", "graphic-line-1", {x:.05,y:.04,w:.9,h:.27}, square?.20:.25, {weight:"700",align:"left",tracking:-.055,stretch:square?1.07:1.24,skew:0});
            c("Design", "graphic-line-2", {x:.19,y:.26,w:.67,h:.27}, square?.20:.25, {weight:"700",align:"left",tracking:-.055,stretch:square?1:1.17,skew:0});
            c("is Easy", "graphic-line-3", {x:.05,y:.48,w:.9,h:.25}, square?.20:.22, {weight:"700",align:"left",tracking:-.055,stretch:square?1:1.3,skew:0});
            c("(with Type Mania)", "graphic-caption", {x:.18,y:.75,w:.77,h:.15}, .14, {weight:"700",align:"left",tracking:-.04,stretch:square?1:1.25,skew:0});
            break;
          case "bootzybunny32":
            c("your love is weird.", "bunny-caption", {x:.08,y:square?.77:.76,w:.84,h:.17}, square?.085:.13, {weight:"700",tracking:-.06});
            break;
          case "quadfont32": {
            const tiles = [
              ["Dark", "quad-dark", {x:0,y:0,w:.5,h:.5}, .23, "#ffffff"],
              ["Bold", "quad-bold-label", {x:.5,y:.025,w:.5,h:.22}, .21, "#162625"],
              ["Font", "quad-bold-font", {x:.5,y:.255,w:.5,h:.22}, .21, "#162625"],
              ["Modern", "quad-modern-label", {x:0,y:.515,w:.5,h:.24}, .22, "#162625"],
              ["Font", "quad-modern-font", {x:0,y:.755,w:.5,h:.22}, .21, "#162625"],
              ["Font", "quad-font", {x:.5,y:.5,w:.5,h:.5}, .26, "#ffffff"],
            ];
            for (const [word, key, box, size, color] of tiles) {
              c(word, key, box, size, {color,weight:"700",tracking:-.035});
            }
            break;
          }
          case "mythicallions32":
            c("Sea Lions", "lions-vertical", {x:.045,y:.14,w:.17,h:.82}, .26, {align:"center",tracking:-.04,color:"#fcf71f"});
            c("By The Sea", "lions-side-coastal", {x:.21,y:.22,w:.15,h:.74}, .20, {align:"center",tracking:-.045,color:"#fcf71f"});
            c("Coastal Art", "lions-side-study", {x:.37,y:.39,w:.11,h:.57}, .18, {align:"center",tracking:-.04,color:"#fcf71f"});
            c("✦", "lions-seal", {x:.265,y:.265,w:.1,h:.15}, .075, {face:"Arial,sans-serif",color:"#fff4b0",weight:"400"});
            const ampersand = c("&", "lions-ampersand", {x:.515,y:0,w:.485,h:1}, .82, {align:"center",weight:"400",color:"#fcf71f",tracking:-.08});
            ampersand.innerHTML = "<span>&</span>";
            ampersand.style.fontSize = square ? "110cqh" : "142cqh";
            add(board, "NEW SERIF FACE", "lions-top-note", "cmr-small-copy", {x:.22,y:.035,w:.29,h:.035}, .045, {display:false,color:"#fff4b0",align:"center",face:"Arial,sans-serif"});
            add(board, "ALTERNATE LIGATURES INCLUDED", "lions-top-note-2", "cmr-small-copy", {x:.22,y:.075,w:.29,h:.035}, .045, {display:false,color:"#fff4b0",align:"center",face:"Arial,sans-serif"});
            add(board, "A QUIET COASTAL\nPORTRAIT OF TWO\nSEA LIONS BY THE\nSHORE.", "lions-caption", "cmr-small-copy", {x:.665,y:.7,w:.29,h:.2}, .045, {display:false,color:"#fff4b0",align:"left",face:"Arial,sans-serif"});
            break;
          case "lifeinblackwhite32":
            c("Life In Black", "life-line-1", {x:.07,y:.29,w:.86,h:.25}, .24, {color:"#f3ecdf",tracking:-.055,stretch:1.18,skew:0});
            c("& White", "life-line-2", {x:.15,y:.53,w:.7,h:.25}, .24, {color:"#f3ecdf",tracking:-.05,stretch:1.18,skew:0});
            c("ELEGANT SERIF TYPEFACE", "life-top-label", {x:.1,y:.035,w:.8,h:.07}, .045, {face:"Arial,sans-serif",color:"#eee8dc",tracking:.14});
            c("ELEGANT SERIF TYPEFACE", "life-bottom-label", {x:.1,y:.89,w:.8,h:.07}, .045, {face:"Arial,sans-serif",color:"#eee8dc",tracking:.14});
            break;
          case "romanstrips32": {
            const rows = [
              ["Velvet29, Ephemeral #Grace;", "Velvet29, <i>Ephemeral</i> #Grace;"],
              ["Silhouette 08 NOVELI &", "<i>Silhouette</i> 08 NOVELI &"],
              ["Whisper? Lustre/Serenade*", "Whisper? <i>Lustre/Serenade</i>*"],
              ["47 Château. KONFALK-19 ©", "47 <i>Château</i>. KONFALK-19 ©"],
              ["Film Festival – Nocturne1937", "Film Festival – <i>Nocturne</i>1937"],
            ];
            rows.forEach(([plain, markup], i) => {
              const row = c(plain, `roman-line-${i+1}`, {x:.035,y:.02+i*.155,w:.93,h:.14}, .115, {tracking:-.035});
              row.innerHTML = markup;
            });
            c("Roman Display · Type Specimen", "roman-caption", {x:.12,y:.84,w:.76,h:.1}, .065, {tracking:-.04});
            break;
          }
          case "floraltriptych32":
            c("Bloom", "flower-left", {x:.105,y:.615,w:.25,h:.115}, .115, {weight:"400",tracking:-.045,stretch:1.35,skew:0});
            add(board, "BLOOMING DAY", "flower-left-label", "cmr-small-copy", {x:.13,y:.735,w:.2,h:.04}, .04, {display:false,color:"#241d16",align:"center",face:"Georgia,serif"});
            const flowerLeftBody = add(board, "A gentle floral study in soft light, color, and form.", "flower-left-body", "cmr-small-copy", {x:.095,y:.78,w:.28,h:.075}, .04, {display:false,color:"#241d16",align:"center",face:"Arial,sans-serif"});
            flowerLeftBody.innerHTML = "A gentle floral study<br>in soft light, color, and<br>form.";
            c("Flowers .", "flower-center-top", {x:.475,y:.11,w:.3,h:.07}, .065, {weight:"400",tracking:-.04,stretch:1.35,skew:0});
            c("are nature’s", "flower-center-middle", {x:.475,y:.175,w:.3,h:.07}, .065, {weight:"400",tracking:-.04,stretch:1.35,skew:0});
            c("poetry", "flower-center-bottom", {x:.475,y:.24,w:.3,h:.07}, .065, {weight:"400",tracking:-.04,stretch:1.35,skew:0});
            const flowerSub = add(board, "a delicate expression of beauty, color, and fragrance", "flower-sub", "cmr-small-copy", {x:.49,y:.35,w:.29,h:.085}, .04, {display:false,color:"#4a4036",align:"center",face:"Georgia,serif"});
            flowerSub.innerHTML = "a delicate expression of<br>beauty, color, and fragrance";
            const rightBloom = c("Bloom", "flower-right", {x:.9,y:.615,w:.1,h:.115}, .115, {display:false,align:"left",weight:"400",tracking:-.045});
            rightBloom.style.fontSize = "11.5cqh";
            rightBloom.style.whiteSpace = "nowrap";
            const rightLabel = add(board, "BLOOMING DAY", "flower-right-label", "cmr-small-copy", {x:.94,y:.735,w:.06,h:.04}, .04, {display:false,color:"#241d16",align:"left",face:"Georgia,serif"});
            rightLabel.style.fontSize = "1.15cqh";
            rightLabel.style.whiteSpace = "nowrap";
            const rightBody = add(board, "A gentle floral study in soft light, color, and form.", "flower-right-body", "cmr-small-copy", {x:.9,y:.78,w:.1,h:.075}, .04, {display:false,color:"#241d16",align:"left",face:"Arial,sans-serif"});
            rightBody.innerHTML = "A gentle floral study<br>in soft light, color, and<br>form.";
            rightBody.style.fontSize = "1.1cqh";
            rightBody.style.whiteSpace = "nowrap";
            break;
          case "homequote32":
            c("01. HOME", "home-heading", {x:.5,y:.085,w:.44,h:.14}, .15, {color:"#f1eab3",align:"right",tracking:-.05,stretch:1.25,skew:0});
            c("Home is more than", "home-quote-1", {x:.085,y:.24,w:.68,h:.1}, .11, {color:"#f1eab3",align:"left",weight:"400",tracking:-.035,stretch:1.14,skew:0});
            const homeQuote2 = c("just a place—it’s where", "home-quote-2", {x:.085,y:.345,w:.76,h:.1}, .11, {color:"#f1eab3",align:"left",weight:"400",tracking:-.035,stretch:1.14,skew:0});
            homeQuote2.innerHTML = "just a place<span class=\"home-dash\">—</span>it’s where";
            c("we find comfort", "home-quote-3", {x:.085,y:.45,w:.64,h:.1}, .11, {color:"#f1eab3",align:"left",weight:"400",tracking:-.035,stretch:1.14,skew:0});
            const homeBody = add(board, "It’s the warm embrace that welcomes us after a long day. The sanctuary where we relax, laugh, and create memories. The walls may change, but the feeling of home remains constant, grounded in the love and experiences shared within it.", "home-body", "cmr-small-copy", {x:.085,y:.55,w:.82,h:.11}, .05, {display:false,color:"#f1eab3",align:"left",face:"Georgia,serif"});
            homeBody.innerHTML = "It’s the warm embrace that welcomes us after a long day. The sanctuary where we relax, laugh, and create memories.<br>The walls may change, but the feeling of home remains constant, grounded in the love and experiences shared within it.";
            break;
        }
        if (["bootzyfear32", "bootzyalmost32", "bootzygraphic32", "bootzybunny32"].includes(id)) {
          const footerLeft = add(board, "TYPE SPECIMEN", "bootzy-footer-left", "cmr-small-copy", {x:.035,y:.955,w:.3,h:.03}, .02, {display:false,color:"#605b58",align:"left",face:"Arial,sans-serif"});
          footerLeft.style.fontSize = "1.15cqh";
          footerLeft.style.letterSpacing = ".1em";
          const footerRight = add(board, "DISPLAY TYPE STUDY", "bootzy-footer-right", "cmr-small-copy", {x:.66,y:.955,w:.305,h:.03}, .02, {display:false,color:"#605b58",align:"right",face:"Arial,sans-serif"});
          footerRight.style.fontSize = "1.15cqh";
          footerRight.style.letterSpacing = ".1em";
        }
      },
      getContrast() {
        if (id === "mythicallions32") return window.SupportLayout.contrast("#111111", "#eee5c9");
        if (id === "lifeinblackwhite32") return window.SupportLayout.contrast("#f3ecdf", "#151515");
        if (id === "homequote32") return window.SupportLayout.contrast("#f1eab3", "#172219");
        return window.SupportLayout.contrast("#111111", "#f7f0e5");
      },
      getWarnings() { return design.warnings || []; },
    };
    return design;
  }

  window.CmReferenceBatch = { create };
})();
