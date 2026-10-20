(() => {
  const palettes = {
    maidega: { bg: "#101d42", bg2: "#192c5a", paper: "#f4efdf", panel: "#e9e1cf", ink: "#f8f2e7", darkInk: "#171d31", accent: "#e98661", accent2: "#edc777", muted: "#c7c7ca" },
    maidegaPaper: { bg: "#e9e1cf", bg2: "#f1ead9", paper: "#f9f4e8", panel: "#d9d1be", ink: "#192033", darkInk: "#192033", accent: "#a45132", accent2: "#65703e", muted: "#5f5c53" },
    esviga: { bg: "#122d27", bg2: "#1c473a", paper: "#eee5cd", panel: "#e7dcc2", ink: "#f5edda", darkInk: "#16322b", accent: "#b8563d", accent2: "#d1ae63", muted: "#c7c2b0" },
    esvigaPaper: { bg: "#e9dfc8", bg2: "#f2e9d6", paper: "#fff6e6", panel: "#dbd0b8", ink: "#203b33", darkInk: "#203b33", accent: "#a84434", accent2: "#bd8d3d", muted: "#5c6055" },
    sports: { bg: "#12213d", bg2: "#1a3154", paper: "#f5f0e1", panel: "#e9e2d0", ink: "#fff8e8", darkInk: "#14213b", accent: "#f07855", accent2: "#82c8d3", muted: "#c2c9d1" },
    sportsPaper: { bg: "#eee9db", bg2: "#f7f2e6", paper: "#fffaf0", panel: "#ddd7c8", ink: "#1c2636", darkInk: "#1c2636", accent: "#d24c3d", accent2: "#ba8b36", muted: "#626975" },
    script: { bg: "#132532", bg2: "#1d3544", paper: "#f3ead7", panel: "#e5dbc8", ink: "#fff8e8", darkInk: "#1b2d39", accent: "#e5b65e", accent2: "#8cb9ad", muted: "#c3c8c2" },
    scriptPaper: { bg: "#ebe4d3", bg2: "#f6efdf", paper: "#fff8ea", panel: "#dcd2bd", ink: "#263b40", darkInk: "#263b40", accent: "#a45b3c", accent2: "#6d7d52", muted: "#69675e" },
    coffee: { bg: "#302019", bg2: "#4c2c1f", paper: "#f0e0c0", panel: "#e7d3ab", ink: "#fff0cf", darkInk: "#39261c", accent: "#c96b3f", accent2: "#d3a64b", muted: "#d0bda0" },
    coffeePaper: { bg: "#e9e5d8", bg2: "#f4f0e6", paper: "#f8f4e8", panel: "#e4dccb", ink: "#43272a", darkInk: "#3e2827", accent: "#197b78", accent2: "#946548", muted: "#655b54" },
    invest: { bg: "#173d32", bg2: "#285846", paper: "#f3efdc", panel: "#e7e2cc", ink: "#fdf8e7", darkInk: "#173b32", accent: "#dc783e", accent2: "#d6bd6d", muted: "#c8d0b8" },
    investPaper: { bg: "#f0eee3", bg2: "#f7f5eb", paper: "#fbf8ec", panel: "#e5e3d4", ink: "#1e6449", darkInk: "#1e6449", accent: "#17684b", accent2: "#b1c894", muted: "#526b5e" },
    punk: { bg: "#f5f1ea", bg2: "#fffdf8", paper: "#fffdf8", panel: "#e8e2d8", ink: "#181716", darkInk: "#181716", accent: "#df2023", accent2: "#181716", muted: "#595550" },
    star: { bg: "#155c40", bg2: "#0d573b", paper: "#fff8e6", panel: "#155c40", ink: "#fff8e6", darkInk: "#143f31", accent: "#f59a19", accent2: "#365dc4", muted: "#fff0cc" },
    neon: { bg: "#f3f328", bg2: "#ebed18", paper: "#fffca5", panel: "#f526a8", ink: "#291347", darkInk: "#291347", accent: "#e91e9a", accent2: "#641ac5", muted: "#4d2674" },
    sportsChrome: { bg: "#e0e4ea", bg2: "#c6ccd4", paper: "#f0f4f8", panel: "#c6ccd4", ink: "#1a1e24", darkInk: "#1a1e24", accent: "#961824", accent2: "#124a82", muted: "#535960" },
    sportsBib: { bg: "#eee8d9", bg2: "#f8f3e8", paper: "#fffaf0", panel: "#ddd2bc", ink: "#1b2b43", darkInk: "#1b2b43", accent: "#b52a3a", accent2: "#be8734", muted: "#59616a" },
    sportsMidnight: { bg: "#0e1a3e", bg2: "#1c2e60", paper: "#e9eef8", panel: "#d1daec", ink: "#f1f4fc", darkInk: "#0d1736", accent: "#f28858", accent2: "#74c2e2", muted: "#aab7d4" },
    blackletterGilded: { bg: "#0e1a3e", bg2: "#1c2e60", paper: "#e9eef8", panel: "#d1daec", ink: "#f1f4fc", darkInk: "#0d1736", accent: "#f28858", accent2: "#74c2e2", muted: "#aab7d4" },
    blackletterEmber: { bg: "#3a0e22", bg2: "#661834", paper: "#fff0f2", panel: "#f6dce2", ink: "#fff4f6", darkInk: "#300a1c", accent: "#ff7a8c", accent2: "#ffce5c", muted: "#d4a7b0" },
    manuscriptMoss: { bg: "#0c2e22", bg2: "#18523a", paper: "#eefaea", panel: "#d6ecd4", ink: "#f0fcee", darkInk: "#0a281e", accent: "#7ee08c", accent2: "#f8c23c", muted: "#b9d5c0" },
    scriptGraphite: { bg: "#f3f4f6", bg2: "#d8dce4", paper: "#f7f9fc", panel: "#d8dce4", ink: "#1e222a", darkInk: "#1e222a", accent: "#a82832", accent2: "#165c8e", muted: "#646b75" },
    tangerineDark: { bg: "#742a0a", bg2: "#ac4610", paper: "#fff6e8", panel: "#fadcba", ink: "#fff6e8", darkInk: "#602006", accent: "#ffd65a", accent2: "#60cede", muted: "#f4c9a2" },
    marigoldPaper: { bg: "#f7eed8", bg2: "#ebd9b5", paper: "#fff8e9", panel: "#ebd9b5", ink: "#162a2c", darkInk: "#162a2c", accent: "#b2540a", accent2: "#a82c2a", muted: "#596563" },
    olivePaper: { bg: "#f1eee0", bg2: "#e0dbc6", paper: "#f6f3e6", panel: "#e0dbc6", ink: "#202214", darkInk: "#202214", accent: "#80600e", accent2: "#3a602c", muted: "#5a5b4c" },
    asphaltNight: { bg: "#181a1f", bg2: "#292d34", paper: "#e9ecf0", panel: "#cdd2d8", ink: "#f3f6f9", darkInk: "#14161b", accent: "#f5cc19", accent2: "#58c4e8", muted: "#aeb4bd" },
    scriptStudy: { bg: "#f3eddf", bg2: "#dce5ec", paper: "#fff8eb", panel: "#e5d8c2", ink: "#1c304b", darkInk: "#1a2e49", accent: "#bd2f48", accent2: "#087f82", muted: "#4c5c6b" },
    studioContrast: { bg: "#122537", bg2: "#1a394b", paper: "#fff4df", panel: "#efe3cf", ink: "#fff8e9", darkInk: "#102a38", accent: "#fa765e", accent2: "#58c6bd", muted: "#c4d3d8" },
    scriptGuide: { bg: "#f1e1c4", bg2: "#e4cc9f", paper: "#fff4df", panel: "#d7c29d", ink: "#1b3041", darkInk: "#192f45", accent: "#c83e36", accent2: "#167a76", muted: "#52636c" },
    broadsideInk: { bg: "#111c31", bg2: "#1a2d4a", paper: "#fff5e5", panel: "#e8d8c2", ink: "#fff7eb", darkInk: "#111a2b", accent: "#ff7865", accent2: "#ffd166", muted: "#c2cad8" },
    mosaicContrast: { bg: "#14253d", bg2: "#203958", paper: "#fff3dc", panel: "#e7d6ba", ink: "#fff6e8", darkInk: "#16243a", accent: "#ff795e", accent2: "#f3c552", muted: "#c4cfda" },
  };
  const el = (key, text, box, role = "display", size = 80, extra = {}) => {
    const options = { ...extra };
    if (options.box === true) { options.hasBox = true; delete options.box; }
    return { key, text, box, role, size, ...options };
  };
  const specs = {
    hero: { title: "Hero Wordmark", font: "maidega", palette: "sportsMidnight", defaults: { name: "Maidega", line: "A New Typographic Study", word: "Whiskey" }, elements: [
      el("meta", "Type Specimen", [8.2, 8.2, 48, 2.5], "meta", 21, { align: "left" }), el("formats", "5 OpenType Features", [55, 11.2, 36.8, 2.4], "meta", 19, { align: "right" }),
      el("name", "{{name}}", [4, 28, 92, 18.5], "paper", 300, { fill: true }), el("word", "{{word}}", [4, 47.7, 92, 19.5], "accent", 300, { fill: true }),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    set: { title: "Character Set", font: "maidega", palette: "tangerineDark", defaults: { name: "Maidega", line: "The Art Of A Beautiful Letter", word: "Aa" }, elements: [
      el("meta", "Character Set", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }),
      el("glyphA", "Aa", [25.25, 24.9, 49.5, 26], "paper", 526, { fill: true, leading: 0.5, allowOverflow: true }), el("glyphB", "Bb Cc", [8.2, 51.57, 83.6, 19], "accent", 373, { fill: true, leading: 0.5, allowOverflow: true }),
      el("glyphC", "Dd Ee Ff", [7.5, 70.7, 77, 14], "paper", 242, { fill: true, leading: 0.56, allowOverflow: true }),
      el("footer", "26 Upper · 26 Lower · {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    wall: { title: "Type Wall", font: "maidega", palette: "blackletterGilded", defaults: { name: "Maidega", line: "A New\nTypographic Study", word: "0123456789" }, elements: [
      el("meta", "Type Wall", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }), el("line1", "{{line1}}", [8.2, 19.8, 83.6, 17], "paper", 310, { fill: true }),
      el("figures", "{{word}}", [8.2, 38, 83.6, 10], "accent", 150, { fill: true }), el("line2", "{{line2}}", [8.2, 51, 83.6, 12], "paper", 170, { fill: true }),
      el("marks", "& @ ? ! % * ( )", [8.2, 68, 83.6, 12], "accent2", 130, { fill: true }),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    phrase: { title: "Quiet Phrase", font: "maidega", palette: "marigoldPaper", defaults: { name: "Maidega", line: "A New Typographic\nStudy", word: "" }, elements: [
      el("meta", "Set In The Wild", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }),
      el("line1", "{{line1}}", [8.2, 32.5, 83.6, 6.7], "darkInk", 130, { fill: true, leading: 0.7 }), el("line2", "{{line2}}", [12, 39.2, 76, 25.5], "accent", 280),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    full_stack: { title: "Full Character Stack", font: "maidega", palette: "olivePaper", defaults: { name: "Maidega", line: "Invitation Suite · Editorial · Packaging", word: "" }, elements: [
      el("meta", "Regular / Ligature", [8.2, 4, 42, 2.8], "meta", 20, { align: "left" }), el("formats", "OTF / TTF / WOFF", [57, 4, 34.8, 2.8], "meta", 20, { align: "right" }),
      el("name", "{{name}}", [8.2, 7.5, 83.6, 18], "darkInk", 250, { fill: true }), el("sub", "{{line}}", [8.2, 26.2, 83.6, 3], "label", 24, { fill: true }),
      el("caption", "A New Typographic Study", [8.2, 30.7, 83.6, 3], "muted", 23),
      el("section", "Full Character Set", [8.2, 35.7, 42, 2.5], "meta", 20, { align: "left" }), el("count", "26 Upper · 26 Lower", [52, 35.7, 39.8, 2.5], "meta", 20, { align: "right" }),
      el("glyph1", "ABCDEFGHIJ", [20, 39.2, 60, 8.2], "darkInk", 108, { fill: true }), el("glyph2", "KLMNOPQRST", [20, 48.3, 60, 8.2], "accent", 108, { fill: true }),
      el("glyph3", "UVWXYZ", [20, 57.4, 60, 8.2], "accent2", 108, { fill: true }), el("glyph4", "abcdefghij", [20, 66.5, 60, 8.2], "accent2", 108, { fill: true }),
      el("glyph5", "klmnopqrst", [20, 75.6, 60, 8.2], "darkInk", 108, { fill: true }), el("glyph6", "uvwxyz", [20, 84.7, 60, 8.2], "accent", 108, { fill: true }),
    ] },
    studio_cover: { title: "Studio Cover", font: "maidega", palette: "studioContrast", defaults: { name: "Maidega", line: "A New Typographic\nStudy", word: "Aa Bb Cc" }, elements: [
      el("meta", "Type Foundry · Vol. 01", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }), el("name", "{{name}}", [8.2, 15, 83.6, 15], "paper", 245, { fill: true }),
      el("band", "", [9.5, 39, 81, 17.5], "accent", 1, { box: true }),
      el("line1", "{{line1}}", [13, 40.5, 74, 7], "darkInk", 108, { fill: true }), el("line2", "{{line2}}", [13, 47.5, 74, 7], "darkInk", 126),
      el("card1", "Aa", [8.2, 60, 26.2, 17.7], "darkInk", 190, { box: true, overlap: true }), el("card2", "Bb", [36.9, 60, 26.2, 17.7], "darkInk", 190, { box: true, overlap: true }), el("card3", "Cc", [65.6, 60, 26.2, 17.7], "darkInk", 190, { box: true, overlap: true }),
      el("cap1", "Upper And Lower", [8.2, 74, 26.2, 2.2], "muted", 20, { overlap: true }), el("cap2", "Open Shapes", [36.9, 74, 26.2, 2.2], "muted", 20, { overlap: true }), el("cap3", "Character Study", [65.6, 74, 26.2, 2.2], "muted", 20, { overlap: true }),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    specimen_mosaic: { title: "Specimen Mosaic", font: "maidega", palette: "mosaicContrast", defaults: { name: "Maidega", line: "Letter Index", word: "Aa Bb" }, elements: [
      el("meta", "Letter Index", [8.4, 8.5, 83.2, 2.5], "meta", 21, { align: "left" }), el("name", "{{name}}", [8.4, 12.3, 83.2, 9], "wordmark", 118),
      el("tile1", "Aa Bb", [8.4, 24, 40.7, 14.8], "accent", 104, { box: true, overlap: true }), el("tile2", "Cc Dd", [50.9, 24, 40.7, 14.8], "specimen", 104, { box: true, overlap: true }),
      el("tile3", "Ee Ff", [8.4, 40, 40.7, 14.8], "accent2", 104, { box: true, overlap: true }), el("tile4", "Gg Hh", [50.9, 40, 40.7, 14.8], "specimen", 104, { box: true, overlap: true }),
      el("tile5", "Ii Jj", [8.4, 56, 40.7, 14.8], "accent", 104, { box: true, overlap: true }), el("tile6", "Kk Ll", [50.9, 56, 40.7, 14.8], "specimen", 104, { box: true, overlap: true }),
      el("cap1", "01 · Form", [8.4, 35, 40.7, 2.4], "muted", 18, { overlap: true }), el("cap2", "02 · Rhythm", [50.9, 35, 40.7, 2.4], "muted", 18, { overlap: true }),
      el("cap3", "03 · Contrast", [8.4, 51, 40.7, 2.4], "muted", 18, { overlap: true }), el("cap4", "04 · Structure", [50.9, 51, 40.7, 2.4], "muted", 18, { overlap: true }),
      el("cap5", "05 · Texture", [8.4, 67, 40.7, 2.4], "muted", 18, { overlap: true }), el("cap6", "06 · Voice", [50.9, 67, 40.7, 2.4], "muted", 18, { overlap: true }),
      el("tile7", "0123456789", [8.4, 72.5, 40.7, 8.2], "accent2", 76, { box: true }), el("tile8", "& @ ? ! % *", [50.9, 72.5, 40.7, 8.2], "specimen", 78, { box: true }),
      el("cap7", "07 · Figures", [8.4, 81.1, 40.7, 2.3], "muted", 18), el("cap8", "08 · Marks", [50.9, 81.1, 40.7, 2.3], "muted", 18),
      el("footer", "Letter Index {{name}}", [8.4, 86, 83.2, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.4, 89.2, 83.2, 2.5], "muted", 22, { align: "left" }),
    ] },
    initials: { title: "Illuminated Initial", font: "esviga", palette: "marigoldPaper", defaults: { name: "Esviga", line: "Words With\nAn Older\nSoul", word: "W" }, elements: [
      el("meta", "Illuminated Initial", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }), el("initial", "{{word}}", [14, 16.4, 38, 31.2], "accent", 450, { box: true, fill: true, leading: 0.75, scaleY: 1.28 }),
      el("name", "{{name}}", [63.5, 13.2, 28.3, 9], "darkInk", 104, { align: "left", valign: "top", fill: true }),
      el("line1", "{{line1}}", [8.2, 48, 83.6, 9.7], "darkInk", 265, { fill: true, leading: 0.5 }), el("line2", "{{line2}}", [8.2, 60, 83.6, 10], "accent", 260, { fill: true, leading: 0.52 }),
      el("line3", "{{line3}}", [8.2, 72.2, 83.6, 11], "darkInk", 285, { fill: true, leading: 0.55 }), el("side", "2 OpenType Features", [95.5, 48, 2.3, 21], "muted", 18),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22),
    ] },
    knotband: { title: "Letterform Pairs", font: "esviga", palette: "olivePaper", defaults: { name: "Esviga", line: "26 Upper · 26 Lower", word: "" }, elements: [
      el("meta", "Interlaced Set", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }),
      el("glyph1", "Aa", [8.2, 18.5, 83.6, 24], "darkInk", 600, { leading: 0.58 }), el("glyph2", "Bb Cc", [10.5, 44, 79, 20], "accent", 480, { fill: true, leading: 0.6 }),
      el("glyph3", "Dd Ee Ff", [10.5, 65.3, 79, 14.5], "darkInk", 360, { fill: true, leading: 0.54 }), el("side", "2 OpenType Features", [95.5, 48, 2.3, 21], "muted", 18),
      el("footer", "26 Upper · 26 Lower · {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }),
      el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    scriptorium: { title: "Scribe's Specimen", font: "esviga", palette: "tangerineDark", defaults: { name: "Esviga", line: "Words With\nAn Older\nSoul", word: "0123456789" }, elements: [
      el("meta", "Scriptorium", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }),
      el("line1", "{{line1}}", [14, 14.1, 72, 9], "paper", 134, { fill: true }), el("figures", "{{word}}", [14, 24, 72, 9], "accent", 142, { fill: true }),
      el("line2", "{{line2}}", [14, 34, 72, 10], "paper", 132, { fill: true }), el("marks", "& @ ? ! % * ( )", [14, 45.4, 72, 10], "accent2", 126, { fill: true }),
      el("line3", "{{line3}}", [14, 60.5, 72, 21.5], "paper", 280, { fill: true }),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    folio: { title: "Manuscript Folio", font: "esviga", palette: "marigoldPaper", defaults: { name: "Esviga", line: "Words With An\nOlder Soul", word: "" }, elements: [
      el("meta", "Rubricated", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }),
      el("line1a", "{{line1a}}", [10, 35.2, 34, 10], "accent2", 150, { fill: true, leading: 0.75, align: "left" }), el("line1b", "{{line1b}}", [44, 35.2, 47, 10], "darkInk", 150, { fill: true, leading: 0.75, align: "left" }),
      el("line2", "{{line2}}", [10, 48.8, 82, 13], "accent", 170, { fill: true, leading: 0.95, valign: "top" }), el("side", "2 OpenType Features", [95.5, 48, 2.3, 21], "muted", 18),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    carol: { title: "Alternates Carol", font: "esviga", palette: "blackletterGilded", defaults: { name: "Esviga", line: "Words With An Older Soul", word: "ABCDEFGHI\nJKLMNOPQR\nSTUVWXYZ\nabcdefghi\njklmnopqr\nstuvwxyz" }, elements: [
      el("meta", "aalt ss01", [8.2, 4, 42, 2.8], "meta", 20, { align: "left" }), el("formats", "(OTF / TTF / WOFF)", [57, 4, 34.8, 2.8], "meta", 20, { align: "right" }),
      el("name", "{{name}}", [8, 6.8, 84, 25], "wordmark", 300, { fill: true, valign: "top" }),
      el("tag", "251-Glyph Display", [18, 32.8, 64, 2.2], "label", 30), el("line", "{{line}}", [18, 35.2, 64, 2.4], "muted", 22),
      el("section", "Full Character Set", [8.2, 39, 42, 2.1], "meta", 20, { align: "left" }), el("count", "26 Upper · 26 Lower", [52, 39, 39.8, 2.1], "meta", 20, { align: "right" }),
      el("glyphs1", "ABCDEFGHI", [22, 42.2, 56, 7.2], "specimen", 108, { fill: true }), el("glyphs2", "JKLMNOPQR", [22, 49.6, 56, 7.2], "accent", 108, { fill: true }),
      el("glyphs3", "STUVWXYZ", [22, 57, 56, 7.2], "accent", 108, { fill: true }), el("glyphs4", "abcdefghi", [22, 64.4, 56, 7.2], "accent2", 108, { fill: true }),
      el("glyphs5", "jklmnopqr", [22, 71.8, 56, 7.2], "specimen", 108, { fill: true }), el("glyphs6", "stuvwxyz", [22, 79.2, 56, 7.2], "accent", 108, { fill: true }),
      el("footer", "Esviga · Full Character Set", [8.2, 88.5, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Uppercase · Lowercase · Alternates", [8.2, 92, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    illuminated_broadside: { title: "Illuminated Broadside", font: "esviga", palette: "broadsideInk", defaults: { name: "Esviga", line: "Words With\nAn Older\nSoul", word: "Aa Bb Cc Dd Ee Ff" }, elements: [
      el("meta", "The Scriptorium · Broadside", [8.4, 8.5, 83.2, 2.5], "meta", 21), el("frame", "", [10, 13.4, 80, 69.4], "frame", 10, { box: true }),
      el("name", "{{name}}", [13.8, 16.8, 72.4, 7.8], "specimen", 102),
      el("line1", "{{line1}}", [19, 26.8, 62, 8.7], "paper", 136, { fill: true, leading: 0.88 }),
      el("line2", "{{line2}}", [22.5, 36, 55, 8.7], "accent", 152, { fill: true, leading: 0.88 }),
      el("line3", "{{line3}}", [32.5, 45.2, 35, 10], "paper", 168, { fill: true, leading: 0.82 }),
      el("glyphs", "{{word}}", [13.8, 57.7, 72.4, 5.8], "specimen", 66),
      el("glyphs2", "abcdefghij · 0123456789", [13.8, 66.4, 72.4, 5.5], "accent2", 54),
      el("footer", "Printed In The Scriptorium {{name}}", [8.4, 86, 83.2, 3.2], "footer", 30),
      el("footSub", "Invitation Suite · Editorial · Packaging", [8.4, 89.2, 83.2, 2.5], "muted", 22),
    ] },
    scribe_gallery: { title: "Scribe Gallery", font: "esviga", palette: "manuscriptMoss", defaults: { name: "Esviga", line: "Words With An\nOlder Soul", word: "Aa Bb Cc Dd Ee Ff" }, elements: [
      el("meta", "Scribe's Working Page", [8.4, 8.1, 83.2, 2.5], "meta", 21), el("sheet", "", [8.4, 13.1, 83.2, 69.4], "frame", 10, { box: true }),
      el("initial", "E", [9.8, 17.25, 26, 28.5], "paper", 450, { leading: 0.88 }), el("name", "{{name}}", [11.2, 47.3, 25.8, 7.3], "accent2", 32),
      el("line1", "{{line1}}", [39.8, 18, 49, 5.5], "paper", 100, { fill: true, leading: 0.76 }), el("line2", "{{line2}}", [39.8, 21.8, 49, 8], "paper", 100, { fill: true, leading: 0.82, overlap: true }),
      el("glyphs", "{{word}}", [39.8, 34.5, 49, 8.5], "paper", 85), el("figures", "0123456789", [39.8, 46, 49, 7.5], "accent2", 82),
      el("marks", "& · ? ! @", [39.8, 56.3, 49, 7.5], "paper", 76), el("lowercase", "abcdefghij", [39.8, 66.3, 49, 7.5], "accent2", 74),
      el("caption", "Uppercase · Lowercase · Figures · Marks", [39.8, 75.2, 49, 3.5], "muted", 19),
      el("footer", "Scribe's Specimen {{name}}", [8.4, 86, 83.2, 3.2], "footer", 30), el("footSub", "Invitation Suite · Editorial · Packaging", [8.4, 89.2, 83.2, 2.5], "muted", 22),
    ] },
    crest: { title: "Club Crest", font: "sports", palette: "sportsMidnight", defaults: { name: "Opengsa", line: "Built For\nThe Final\nMinute", word: "United" }, elements: [
      el("meta", "Club Crest", [8, 8, 84, 3], "meta", 20, { align: "left" }),
      el("shield", "C", [31, 11, 38, 24], "accent", 280, { box: true }),
      el("word", "{{word}}", [19.6, 30.8, 60.8, 5.8], "darkInk", 94, { box: true, overlap: true }),
      el("line1", "{{line1}}", [8, 42, 84, 12], "paper", 190, { fill: true }),
      el("line2", "{{line2}}", [8, 54, 84, 12], "accent", 190, { fill: true }),
      el("line3", "{{line3}}", [8, 66, 84, 12], "paper", 190, { fill: true }),
      el("side", "1 OpenType Features", [94, 47, 3, 20], "muted", 14),
      el("footer", "Set In {{name}}", [8, 86, 84, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8, 89.2, 84, 2.5], "muted", 22, { align: "left" }),
    ] },
    bib: { title: "Race Number", font: "sports", palette: "sportsBib", defaults: { name: "Opengsa", line: "Built For\nThe Final\nMinute", word: "0123" }, elements: [
      el("meta", "Race Number", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }), el("frame", "", [12.4, 12.9, 75.2, 33.3], "frame", 10, { box: true }),
      el("number", "{{word}}", [15.7, 18.8, 68, 14.6], "accent", 312, { fill: true }), el("label", "Invitation Suite · Editorial · Packaging", [15.7, 35.3, 68, 3.2], "muted", 25),
      el("line1", "{{line1}}", [8.2, 49.5, 83.6, 10], "darkInk", 185, { fill: true }), el("line2", "{{line2}}", [8.2, 60.2, 83.6, 10], "accent", 178, { fill: true }),
      el("line3", "{{line3}}", [8.2, 70.7, 83.6, 11], "darkInk", 230, { fill: true }), el("side", "1 Opentype Features", [95.5, 48, 2.3, 21], "muted", 18),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }),
      el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    lane: { title: "Start List", font: "sports", palette: "manuscriptMoss", defaults: { name: "Opengsa", line: "Built For The Final Minute", word: "" }, elements: [
      el("meta", "Start List", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }), el("line", "{{line}}", [8.2, 13, 83.6, 4.5], "paper", 46, { fill: true }),
      el("row1", "ABCDEFGHIJ", [8.2, 19, 83.6, 10], "paper", 154, { fill: true }), el("row2", "KLMNOPQR", [8.2, 30, 83.6, 10], "accent", 160, { fill: true }),
      el("row3", "STUVWXYZ", [8.2, 41, 83.6, 10], "paper", 160, { fill: true }), el("row4", "ABCDEFGH", [8.2, 52, 83.6, 10], "accent", 160, { fill: true }),
      el("row5", "IJKLMNOP", [8.2, 63, 83.6, 10], "paper", 160, { fill: true }), el("row6", "QRSTUVWXYZ", [8.2, 74, 83.6, 10], "accent", 145, { fill: true }),
      el("footer", "26 Caps · {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22),
    ] },
    finish: { title: "Photo Finish", font: "sports", palette: "asphaltNight", defaults: { name: "Opengsa", line: "Built For The Final Minute", word: "" }, elements: [
      el("meta", "Photo Finish", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }),
      el("line1", "Built For", [8.2, 20, 83.6, 9], "paper", 145, { fill: true }), el("line2", "The", [8.2, 30, 83.6, 12], "accent", 220),
      el("line3", "Final", [8.2, 43, 83.6, 12], "paper", 205), el("line4", "Minute", [8.2, 56, 83.6, 12], "accent2", 195, { fill: true }),
      el("chevrons", "×      ›      ×", [8.2, 69, 83.6, 7], "accent2", 75),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    timer: { title: "Race Timer", font: "sports", palette: "olivePaper", defaults: { name: "Opengsa", line: "26 Upper · 10 Figures", word: "" }, elements: [
      el("meta", "93 Glyphs", [8.2, 4, 42, 2.8], "meta", 20, { align: "left" }), el("formats", "OTF / TTF / WOFF", [57, 4, 34.8, 2.8], "meta", 20, { align: "right" }),
      el("name", "{{name}}", [8.2, 8, 83.6, 15], "darkInk", 235, { fill: true }), el("line", "93-Glyph Display", [8.2, 24, 83.6, 2.5], "label", 24, { track: 0.2 }),
      el("section", "Full Character Set", [8.2, 29.2, 42, 2.5], "meta", 19, { align: "left" }), el("count", "26 Caps · 10 Figures", [52, 29.2, 39.8, 2.5], "meta", 19, { align: "right" }),
      el("row1", "ABCDEFGHIJ", [8.2, 34, 83.6, 6.1], "darkInk", 86, { fill: true }), el("row2", "KLMNOPQRST", [8.2, 40.4, 83.6, 6.1], "accent", 86, { fill: true }),
      el("row3", "UVWXYZ", [8.2, 46.8, 83.6, 6.1], "accent2", 86, { fill: true }), el("row4", "012345", [8.2, 55, 83.6, 6.1], "darkInk", 86, { fill: true }),
      el("row5", "6789", [8.2, 61.4, 83.6, 6.1], "accent", 86, { fill: true }), el("row6", "& @ ? ! %", [8.2, 69.6, 83.6, 6.1], "accent2", 86, { fill: true }),
      el("row7", "* ( )", [8.2, 76, 83.6, 6.1], "darkInk", 86, { fill: true }),
      el("footer", "26 Caps · 10 Figures · {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30), el("footSub", "Athletic Display Specimen", [8.2, 89.2, 83.6, 2.5], "muted", 22),
    ] },
    guide: { title: "The Quiet Art", font: "script", palette: "scriptGuide", defaults: { name: "Regality", line: "The Quiet Art\nOf Writing\nBeautifully", word: "Amore" }, elements: [
      el("meta", "Penman's Band", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }), el("word", "{{word}}", [8.2, 17, 83.6, 31], "darkInk", 410, { fill: true }),
      el("line1", "{{line1}}", [8.2, 51, 83.6, 10], "darkInk", 120, { fill: true }), el("line2", "{{line2}}", [8.2, 63, 83.6, 10], "accent", 126, { fill: true }), el("line3", "{{line3}}", [8.2, 75, 83.6, 10], "accent2", 132, { fill: true }),
      el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }), el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    trace: { title: "Trace Through", font: "script", palette: "blackletterEmber", defaults: { name: "Regality", line: "The Quiet Art\nOf Writing\nBeautifully", word: "Amore" }, elements: [
      el("meta", "Trace-Through", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }), el("word", "{{word}}", [8.2, 18, 83.6, 23], "paper", 360, { fill: true }),
      el("line1", "{{line1}}", [8.2, 44.5, 83.6, 10], "paper", 124, { fill: true }), el("line2", "{{line2}}", [8.2, 56.5, 83.6, 10], "accent", 130, { fill: true }),
      el("line3", "{{line3}}", [8.2, 68.5, 83.6, 10], "paper", 130, { fill: true }), el("footer", "Set In {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30, { align: "left" }),
      el("footSub", "Invitation Suite · Editorial · Packaging", [8.2, 89.2, 83.6, 2.5], "muted", 22, { align: "left" }),
    ] },
    letter_study: { title: "Letter Study", font: "script", palette: "scriptStudy", defaults: { name: "Regality", line: "The Quiet Art\nOf Writing\nBeautifully", word: "Amore" }, elements: [
      el("meta", "Pen Study · No. 01", [8.2, 8.2, 83.6, 2.5], "meta", 21, { align: "left" }),
      el("line1", "{{line1}}", [9.5, 18, 81, 14.5], "darkInk", 125, { fill: true }), el("line2", "{{line2}}", [9.5, 34.5, 81, 14.5], "accent", 140, { fill: true }),
      el("line3", "{{line3}}", [9.5, 51, 81, 14.5], "accent2", 145, { fill: true }),
      el("word", "{{word}}", [30, 68.5, 58, 10], "accent", 138), el("glyphs", "Aa Bb Cc · 0123456789", [13.5, 79.4, 73, 3.8], "darkInk", 40),
      el("footer", "A Handwritten Specimen · {{name}}", [8.2, 86, 83.6, 3.2], "footer", 30),
      el("footSub", "Calligraphic Display", [8.2, 89.2, 83.6, 2.5], "muted", 22),
    ] },
    coffee_roaster: { title: "Coffee Roaster Label", font: "maidega", palette: "coffeePaper", defaults: { name: "The Morrow", line: "Make Room\nFor Coffee", word: "Roasters", kicker: "Small Batch · Since 1987", secondary: "Good Mornings, Made Slowly" }, elements: [
      el("meta", "Small Batch · Since 1987", [9, 4, 82, 3], "meta", 18), el("badge", "The Morrow Roasters", [19, 15.5, 62, 4], "accent2", 25),
      el("name", "{{name}}", [8, 20, 84, 13.5], "wordmark", 150), el("line", "{{line}}", [9, 34, 82, 22], "accent", 155, { leading: 1.02 }),
      el("word", "{{word}}", [15, 56.5, 70, 4.5], "accent2", 42), el("secondary", "{{secondary}}", [11, 62, 78, 4], "muted", 24),
      el("facts", "Maker Espresso V.01\nOrigin — Ethiopia Africa\nVarietal — Heirloom\nProcess — Washed\nTasting Notes — Cocoa · Orange", [10, 68, 80, 15.5], "darkInk", 24, { box: true, leading: 1.24, align: "left" }),
      el("footer", "Roasted With Care", [9, 86, 82, 3.5], "footer", 27), el("footSub", "{{fontName}} Font", [9, 92, 82, 2.5], "muted", 20),
    ] },
    invest_poster: { title: "Bet On Your Future", font: "maidega", palette: "investPaper", defaults: { name: "Bet On\nYour Own\nFuture", line: "Make Your Next Move Count", word: "Small Steps", kicker: "A Little Progress Every Day", secondary: "Big Changes" }, elements: [
      el("meta", "A Little Progress Every Day", [8, 4, 84, 3], "meta", 17), el("line", "{{name}}", [7, 8, 86, 31], "wordmark", 116, { leading: 0.91 }),
      el("mascot", "", [24, 39, 52, 31], "accent", 1), el("word", "{{word}}", [8, 77, 40, 4], "accent", 45), el("secondary", "{{secondary}}", [52, 77, 40, 4], "accent", 45),
      el("footer", "{{line}}", [8, 83, 84, 5], "footer", 28), el("footSub", "Choose What Comes Next", [8, 91, 84, 3], "muted", 21),
    ] },
    punk_manifesto: { title: "Take Your Space Back", font: "sports", palette: "punk", defaults: { name: "Take\nYour\nSpace\nBack", line: "A Small Revolution In Type", word: "Noise", kicker: "A Manifesto For The Unquiet" }, elements: [
      el("line", "{{name}}", [4, 5, 92, 82], "accent", 270, { leading: 0.93 }),
      el("footer", "{{fontName}} Font · {{line}}", [8, 88, 84, 4], "footer", 28), el("footSub", "Keep Making Room For Yourself", [8, 93, 84, 3], "muted", 20),
    ] },
    green_starburst: { title: "Start With One Idea", font: "sports", palette: "star", defaults: { name: "Start\nWith\nOne\nIdea", line: "Great Things Grow From Small Seeds", word: "Keep Going", kicker: "A Bright Idea For Today", secondary: "" }, elements: [
      el("line", "{{name}}", [5, 8, 90, 71], "wordmark", 242, { leading: 1.02, valign: "top" }),
      el("starwords", "{{word}}", [8, 80.5, 84, 4], "paper", 40), el("secondary", "{{line}}", [8, 85, 84, 4], "paper", 32),
      el("footer", "Make A Brighter Tomorrow", [8, 90.5, 84, 3.5], "footer", 30), el("footSub", "One Step At A Time", [8, 94.5, 84, 3], "muted", 25),
    ] },
    neon_overprint: { title: "Make Good Things Happen", font: "sports", palette: "neon", defaults: { name: "Make\nGood\nThings\nHappen", line: "Keep Going, Even Slowly", word: "Together", kicker: "A Note To Your Future Self", secondary: "" }, elements: [
      el("line", "{{name}}", [5, 8, 90, 59], "wordmark", 210, { leading: 0.95, valign: "top" }), el("word", "{{word}}", [10, 69.5, 80, 7.5], "script", 100),
      el("secondary", "{{line}}", [8, 78.5, 84, 4.5], "wordmark", 44), el("footer", "{{fontName}} Font", [8, 89.5, 84, 3.2], "footer", 28),
    ] },
  };

  function titleCase(value) {
    const text = String(value ?? "");
    if (/^(?:[A-Z0-9 &?!.,·-]+)$/u.test(text) && /[a-z]/u.test(text)) return text;
    return text.replace(/\p{L}+(?:['’]\p{L}+)*/gu, (word) => {
      const first = word.slice(0, 1).toLocaleUpperCase("en");
      const rest = word.slice(1);
      return first + (word === word.toLocaleUpperCase("en") ? rest.toLocaleLowerCase("en") : rest);
    });
  }
  const replaceTokens = (text, props) => String(text ?? "").replace(/\{\{(name|fontName|line[123]?[a-z]?|word|kicker|secondary)\}\}/gu, (_, key) => props[key] ?? "");
  function productionCopy(id, item, text, props) {
    if (!props.production) return text;
    if (/^\d+ OpenType Features?$/iu.test(text)) return "Letterform Details";
    if (/^\d+-Glyph Display$/u.test(text)) return "Character Study";
    if (/^\d+ Glyphs$/u.test(text)) return "Character Study";
    if (/\b\d+\s+(?:Glyphs?|Upper|Lower|Caps?|Figures?)\b/iu.test(text)) return "Character Study";
    if (["OTF / TTF / WOFF", "(OTF / TTF / WOFF)", "Regular / Ligature", "aalt ss01"].includes(text)) return "Letterform Specimen";
    if (text.includes("Full Character Set")) {
      const genericText = text.replaceAll("Full Character Set", "Character Study");
      const specimenFont = specimenFontNames[id];
      return specimenFont ? genericText.replaceAll(specimenFont, props.fontName) : genericText;
    }
    if (["Uppercase · Lowercase · Alternates", "Regular · Lowercase · Marks", "Upper And Lower", "Open Shapes"].includes(text)) return "Character Study";
    if (id === "studio_cover" && item.key === "meta") return "Type Specimen · Vol. 01";
    if (id === "carol" && item.key === "footSub") return "Letterforms · Figures · Marks";
    if (id === "scribe_gallery" && item.key === "caption") return "Letterform Study";
    if (id === "timer" && item.key === "footSub") return "Race Number Study";
    if (id === "coffee_roaster") {
      if (item.key === "meta") return "Coffee Packaging Specimen";
      if (item.key === "badge") return "Lettering For Roasters";
      if (item.key === "facts") return "Font Specimen\nLetterforms\nCharacter Study\nType In Use\nDisplay Copy";
      if (item.key === "footer") return "Coffee Packaging Specimen";
    }
    const specimenFont = specimenFontNames[id];
    if (specimenFont && text.includes(specimenFont)) return text.replaceAll(specimenFont, props.fontName);
    return text;
  }
  const specimenFontNames = {
    hero: "Maidega", set: "Maidega", wall: "Maidega", full_stack: "Maidega",
    studio_cover: "Maidega", specimen_mosaic: "Maidega",
    initials: "Esviga", knotband: "Esviga", scriptorium: "Esviga",
    carol: "Esviga", illuminated_broadside: "Esviga", scribe_gallery: "Esviga",
    crest: "Opengsa", bib: "Opengsa", lane: "Opengsa", finish: "Opengsa", timer: "Opengsa",
    guide: "Regality", trace: "Regality", letter_study: "Regality",
  };
  function decoration(id) {
    const footerRule = specs[id].elements.some((item) => item.key === "footer") && !["guide", "trace"].includes(id)
      ? `<path d="M84 1284H180" stroke="var(--accent)" stroke-width="3" opacity=".92"/>` : "";
    const paperRules = ["phrase", "initials", "folio"].includes(id)
      ? `<defs><pattern id="pinPaperRules" width="1000" height="14" patternUnits="userSpaceOnUse"><path d="M0 13.5H1000" stroke="var(--muted)" stroke-width="1" opacity=".12"/></pattern></defs><rect width="1000" height="1500" fill="url(#pinPaperRules)"/>` : "";
    const shared = `<svg class="pin-art-svg" viewBox="0 0 1000 1500" preserveAspectRatio="none" aria-hidden="true">${paperRules}${footerRule}`;
    const shapes = {
      hero: `<g fill="none" stroke="var(--accent)" stroke-width="2.2" opacity=".26" font-family="PinMaidega,serif" font-size="1600"><text x="-360" y="1280">M</text><text x="300" y="1280">M</text><text x="900" y="1280">M</text></g><path d="M38 1062H192" stroke="var(--accent)" stroke-width="4"/>`,
      set: `<path d="M80 160H920" stroke="var(--muted)" stroke-width="1.2" opacity=".5"/><g fill="none" stroke="var(--paper)" stroke-width="5" opacity=".8"><path d="M195 244a55 55 0 0 1 110 0M210 244a40 40 0 0 1 80 0M225 244a25 25 0 0 1 50 0"/></g><g fill="var(--accent)" opacity=".9"><circle cx="477" cy="220" r="7"/><circle cx="495" cy="211" r="6"/><circle cx="515" cy="205" r="5"/><circle cx="535" cy="210" r="4"/><circle cx="553" cy="220" r="3"/></g><path d="M780 220l8-18 8 18 18 8-18 8-8 18-8-18-18-8Z" fill="var(--paper)"/><g fill="none" stroke="var(--accent)" stroke-width="1.5" opacity=".12"><circle cx="720" cy="1085" r="95"/><circle cx="720" cy="1085" r="155"/><circle cx="720" cy="1085" r="215"/><circle cx="720" cy="1085" r="275"/></g>`,
      wall: `<path d="M82 164H918" stroke="var(--muted)" stroke-width="1.4" opacity=".55"/><g fill="var(--accent)" opacity=".18"><circle cx="180" cy="720" r="3"/><circle cx="830" cy="840" r="3"/><circle cx="270" cy="1050" r="3"/><circle cx="720" cy="1190" r="3"/></g>`,
      phrase: `<g stroke-linecap="round" stroke-linejoin="round"><g stroke="var(--darkInk)" stroke-width="11"><circle cx="516" cy="328" r="57" fill="var(--darkInk)"/><path d="M516 216V238M516 418V440M404 328H426M606 328H628M436 248l16 16m128 128 16 16m0-160-16 16M452 392l-16 16"/></g><path d="M216 278l6-24 6 24 24 6-24 6-6 24-6-24-24-6Z" fill="var(--accent)"/><path d="M812 370l5-20 5 20 20 5-20 5-5 20-5-20-20-5Z" fill="var(--darkInk)"/><path d="M282 416c-21-28 8-54 32-33 20 18 2 44-16 36-12-5-9-19 2-20" fill="var(--accent)"/><path d="M254 1090q47-38 94 0-47 38-94 0Z" fill="none" stroke="var(--accent)" stroke-width="9"/><circle cx="301" cy="1090" r="12" fill="var(--accent)"/><g fill="var(--accent2)"><circle cx="488" cy="1078" r="18"/><circle cx="537" cy="1058" r="14"/><circle cx="578" cy="1050" r="11"/><circle cx="617" cy="1062" r="7"/><circle cx="648" cy="1080" r="5"/></g><path d="M824 1156c-44-52 14-98 60-50 23 24 2 60-25 47-15-8-8-28 9-25" fill="var(--accent2)"/></g><path d="M408 950H592" stroke="var(--accent)" stroke-width="3"/>`,
      full_stack: `<path d="M82 522H918" stroke="var(--muted)" stroke-width="1" opacity=".72"/><path d="M500 516l7 6-7 6-7-6Z" fill="var(--accent2)"/>`,
      studio_cover: `<g stroke="var(--accent2)" stroke-width="1.5" opacity=".16"><path d="M140 1290L0 150M140 1290L0 320M140 1290L110 200M140 1290L260 150M140 1290L430 150M140 1290L600 150M140 1290L770 150M140 1290L940 150"/></g><path d="M82 164H918" stroke="var(--muted)" stroke-width="1.3" opacity=".5"/>`,
      specimen_mosaic: `<path d="M84 348H916" stroke="var(--accent2)" stroke-width="1.4" opacity=".64"/><path d="M84 354H916" stroke="var(--accent)" stroke-width="1" opacity=".32"/><g stroke="var(--accent)" stroke-width="1" opacity=".14"><path d="M84 1082H916M84 1128H916M84 1174H916M84 1220H916M84 1266H916"/><path d="M84 1082V1266M222 1082V1266M360 1082V1266M498 1082V1266M636 1082V1266M774 1082V1266M916 1082V1266"/></g>`,
      initials: `<rect x="82" y="190" width="486" height="486" fill="none" stroke="var(--darkInk)" stroke-width="7"/><rect x="94" y="202" width="462" height="462" fill="none" stroke="var(--accent)" stroke-width="2"/><g fill="var(--accent)"><path d="M116 228q18-34 24 0 9-32 23 0l-23 18Z"/><path d="M500 228q18-34 24 0 9-32 23 0l-23 18Z"/><path d="M116 640q18-34 24 0 9-32 23 0l-23 18Z"/><path d="M500 640q18-34 24 0 9-32 23 0l-23 18Z"/></g><g fill="none" stroke="var(--accent2)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" opacity=".8"><path d="M722 612c-35-39-21-75 11-105 30-29 31-62-1-91-31-28-15-64 15-83 26-16 28-42 8-62"/><path d="M822 610c34-30 37-68 11-96-23-25-18-53 8-72 20-15 21-43 5-66"/></g><g fill="var(--accent2)" opacity=".86"><path d="M727 510c-31-24-53-12-51 6 3 18 30 25 51-6Zm9-81c33-19 52-4 44 14-7 16-35 18-44-14Zm69 70c-30-19-50-5-43 12 8 18 32 20 43-12Zm45-76c28-20 48-7 42 10-6 17-33 21-42-10Z"/></g>`,
      knotband: `<g fill="none" stroke-linecap="round" stroke-linejoin="round"><path d="M92 218c40-45 80 45 120 0s80 45 120 0 80 45 120 0 80 45 120 0 80 45 120 0 80 45 120 0 80 45 120 0" stroke="var(--darkInk)" stroke-width="24"/><path d="M92 218c40 45 80-45 120 0s80-45 120 0 80-45 120 0 80-45 120 0 80-45 120 0 80-45 120 0 80-45 120 0" stroke="var(--darkInk)" stroke-width="24"/><path d="M92 218c40-45 80 45 120 0s80 45 120 0 80 45 120 0 80 45 120 0 80 45 120 0 80 45 120 0 80 45 120 0" stroke="var(--paper)" stroke-width="9"/><path d="M92 218c40 45 80-45 120 0s80-45 120 0 80-45 120 0 80-45 120 0 80-45 120 0 80-45 120 0 80-45 120 0" stroke="var(--paper)" stroke-width="9"/></g><rect x="72" y="274" width="856" height="960" fill="none" stroke="var(--muted)" stroke-width="1.4" opacity=".78"/><rect x="82" y="284" width="836" height="940" fill="none" stroke="var(--accent)" stroke-width="1" opacity=".58"/><circle cx="115" cy="274" r="27" fill="none" stroke="var(--accent)" stroke-width="2"/>`,
      scriptorium: `<rect x="70" y="194" width="860" height="1060" fill="none" stroke="var(--paper)" stroke-width="1.6"/><rect x="80" y="204" width="840" height="1040" fill="none" stroke="var(--accent2)" stroke-width="1" opacity=".78"/><g stroke="var(--paper)" stroke-width="1" opacity=".10"><path d="M82 300H918M82 400H918M82 500H918M82 600H918M82 700H918M82 800H918M82 900H918M82 1000H918M82 1100H918M82 1200H918"/></g><g fill="var(--accent)"><circle cx="70" cy="194" r="4"/><circle cx="930" cy="194" r="4"/><circle cx="70" cy="1254" r="4"/><circle cx="930" cy="1254" r="4"/></g><circle cx="862" cy="1188" r="46" fill="none" stroke="var(--accent)" stroke-width="4"/><circle cx="862" cy="1188" r="31" fill="none" stroke="var(--accent)" stroke-width="2"/>`,
      folio: `<path d="M82 164H918" stroke="var(--muted)" stroke-width="1.2" opacity=".6"/><g fill="var(--darkInk)"><path d="M183 330v-34c-4-26-18-47-35-68-16-20-11-43 8-46 25-3 37 21 28 51 15-28 30-43 48-34 18 9 9 30-11 45-20 15-34 37-38 67v19Z"/><path d="M817 330v-34c4-26 18-47 35-68 16-20 11-43-8-46-25-3-37 21-28 51-15-28-30-43-48-34-18 9-9 30 11 45 20 15 34 37 38 67v19Z"/></g><g fill="none" stroke="var(--accent)" stroke-width="5" opacity=".9"><circle cx="500" cy="250" r="62"/><circle cx="500" cy="250" r="38"/><circle cx="500" cy="250" r="14"/></g><path d="M408 1092H592" stroke="var(--accent)" stroke-width="3"/><g fill="var(--accent)"><path d="M500 1073l9 19-9 19-9-19Z"/><circle cx="500" cy="1092" r="6"/></g><g fill="none" stroke="var(--accent2)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"><path d="M200 1238c-12-35 20-46 28-22 5 16-18 23-21 8m21 14c12-35-20-46-28-22m600 22c12-35-20-46-28-22-5 16 18 23 21 8m-21 14c-12-35 20-46 28-22"/></g><g fill="none" stroke="var(--accent2)" stroke-width="4"><circle cx="500" cy="1190" r="48"/><circle cx="500" cy="1190" r="30"/><circle cx="500" cy="1190" r="12"/></g>`,
      carol: `<g stroke="var(--accent2)" stroke-width="1.6" opacity=".18"><path d="M140 1290L0 120M140 1290L0 220M140 1290L0 330M140 1290L10 450M140 1290L65 570M140 1290L145 650M140 1290L240 660M140 1290L360 660M140 1290L500 660M140 1290L660 660M140 1290L840 660M140 1290L1000 660"/></g><path d="M82 566H918" stroke="var(--muted)" stroke-width="1.5" opacity=".66"/><circle cx="500" cy="566" r="6" fill="none" stroke="var(--accent)" stroke-width="2"/><circle cx="500" cy="566" r="3" fill="none" stroke="var(--accent)" stroke-width="1.5"/>`,
      illuminated_broadside: `<path d="M82 164H918" stroke="var(--muted)" stroke-width="1.2" opacity=".58"/><rect x="100" y="200" width="800" height="832" fill="none" stroke="var(--ink)" stroke-width="2" opacity=".84"/><rect x="112" y="212" width="776" height="806" fill="none" stroke="var(--accent)" stroke-width="1.2" opacity=".78"/><path d="M154 388H846" stroke="var(--accent)" stroke-width="2" opacity=".78"/><g fill="none" stroke="var(--accent)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" opacity=".9"><path d="M128 244c22-18 32 7 14 19-11 7-19 1-14-7m0 7c-7 12 5 20 15 8m-15-8c-15-4-17 11-5 14m-9-17l-5-9m24 27l6 9M872 244c-22-18-32 7-14 19 11 7 19 1 14-7m0 7c7 12-5 20-15 8m15-8c15-4 17 11 5 14m9-17l5-9m-24 27l-6 9M128 1006c22 18 32-7 14-19-11-7-19-1-14 7m0-7c-7-12 5-20 15-8m-15 8c-15 4-17-11-5-14m-9 17l-5 9m24-27l6-9M872 1006c-22 18-32-7-14-19 11-7 19-1 14 7m0-7c7-12-5-20-15-8m15 8c15 4 17-11 5-14m9 17l5 9m-24-27l-6-9"/></g><g fill="none" stroke="var(--accent)" stroke-width="2.4" opacity=".95"><circle cx="480" cy="858" r="17"/><circle cx="500" cy="858" r="17"/><circle cx="490" cy="842" r="17"/><circle cx="490" cy="858" r="7"/></g>`,
      scribe_gallery: `<rect x="84" y="196" width="832" height="922" rx="12" fill="var(--paper)" fill-opacity=".22" stroke="var(--accent)" stroke-width="1.5" opacity=".96"/><path d="M370 242V1088" stroke="var(--ink)" stroke-width="1.2" opacity=".4"/><path d="M398 492H886" stroke="var(--accent)" stroke-width="1.4" opacity=".7"/><g fill="none" stroke="var(--accent)" stroke-width="5" stroke-linecap="round" stroke-linejoin="round" opacity=".82"><path d="M174 905c-18-42 25-66 45-39 13 18-9 34-21 20-8-9 2-20 11-13m-29 48c-12-22-34-16-31 1 2 12 18 10 17 0m46 3c16-23 38-17 33 1-3 12-17 10-17 0m-53 24c-4-20-27-22-29-5-1 12 15 14 18 4m58 1c9-19 31-17 31 0 0 12-15 14-18 4m-52 25c4-18-14-29-24-17-7 9 4 19 13 14m55 3c-3-18 14-28 24-15 7 9-3 18-13 13m-48 26c16-15 35-5 28 9-5 10-19 6-17-4m35 4c-15-14-5-32 9-26 10 5 6 17-3 16"/></g>`,
      crest: `<path d="M82 164H918" stroke="var(--muted)" stroke-width="1.4" opacity=".68"/><path d="M296 192H704L718 266L701 444L500 566L299 444L282 266Z" fill="none" stroke="var(--paper)" stroke-width="7"/><path d="M309 205H691L704 270L688 436L500 550L312 436L296 270Z" fill="none" stroke="var(--muted)" stroke-width="2" opacity=".84"/><circle cx="418" cy="222" r="4.5" fill="var(--accent)"/><circle cx="500" cy="222" r="4.5" fill="var(--accent)"/><circle cx="582" cy="222" r="4.5" fill="var(--accent)"/><g fill="none" stroke="var(--paper)" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"><path d="M98 270l28 35-28 35m38-70 28 35-28 35m38-70 28 35-28 35"/><path d="M902 270l-28 35 28 35m-38-70-28 35 28 35m-38-70-28 35 28 35" stroke="var(--accent)"/></g><rect x="196" y="466" width="608" height="86" fill="var(--accent)"/>`,
      bib: `<g stroke="var(--ink)" stroke-width="1" opacity=".09"><path d="M0 22H1000M0 68H1000M0 114H1000M0 160H1000M0 206H1000M0 252H1000M0 298H1000M0 344H1000M0 390H1000M0 436H1000M0 482H1000M0 528H1000M0 574H1000M0 620H1000M0 666H1000M0 712H1000M0 758H1000M0 804H1000M0 850H1000M0 896H1000M0 942H1000M0 988H1000M0 1034H1000M0 1080H1000M0 1126H1000M0 1172H1000M0 1218H1000M0 1264H1000M0 1310H1000M0 1356H1000M0 1402H1000M0 1448H1000"/></g><rect x="124" y="194" width="752" height="500" fill="none" stroke="var(--ink)" stroke-width="1.5" opacity=".72"/><rect x="132" y="202" width="736" height="484" fill="none" stroke="var(--ink)" stroke-width="1" opacity=".42"/><g fill="var(--accent)"><circle cx="124" cy="194" r="3.5"/><circle cx="876" cy="194" r="3.5"/><circle cx="124" cy="694" r="3.5"/><circle cx="876" cy="694" r="3.5"/></g><g stroke="var(--accent2)" stroke-width="1" opacity=".13"><path d="M84 910H916M84 956H916M84 1002H916M84 1048H916M84 1094H916M84 1140H916M84 1186H916"/><path d="M84 910V1220M222 910V1220M360 910V1220M498 910V1220M636 910V1220M774 910V1220M916 910V1220"/></g>`,
      lane: `<g stroke="var(--paper)" stroke-width="2" opacity=".2"><path d="M82 435H918M82 600H918M82 765H918M82 930H918M82 1095H918M82 1260H918"/></g>`,
      finish: `<path d="M82 1196H918" stroke="var(--accent2)" stroke-width="2" opacity=".46"/>`,
      timer: `<g fill="var(--accent2)" opacity=".2">${Array.from({length: 16}, (_, r) => Array.from({length: 12}, (_, c) => `<circle cx="${90+c*72}" cy="${570+r*38}" r="2.1"/>`).join("")).join("")}</g><path d="M82 514H918" stroke="var(--muted)" stroke-width="1.2" opacity=".55"/>`,
      guide: `<g stroke="var(--muted)" stroke-width="1" opacity=".28"><path d="M82 270H918M82 316H918M82 362H918M82 408H918M82 454H918M82 500H918M82 546H918M82 592H918M82 638H918M82 684H918M82 730H918M82 776H918M82 822H918M82 868H918M82 914H918M82 960H918M82 1006H918M82 1052H918M82 1098H918M82 1144H918M82 1190H918M82 1236H918"/></g><path d="M82 160H918M82 1264H180" stroke="var(--accent)" stroke-width="2" opacity=".6"/>`,
      trace: `<path d="M82 164H918M82 1264H180" stroke="var(--accent)" stroke-width="1.4" opacity=".62"/><path d="M200 1178l7 16 16 7-16 7-7 16-7-16-16-7 16-7ZM800 1178l7 16 16 7-16 7-7 16-7-16-16-7 16-7Z" fill="none" stroke="var(--accent2)" stroke-width="3"/>`,
      letter_study: `<g stroke="var(--muted)" stroke-width="1" opacity=".18"><path d="M110 250H930M110 296H930M110 342H930M110 388H930M110 434H930M110 480H930M110 526H930M110 572H930M110 618H930M110 664H930M110 710H930M110 756H930M110 802H930M110 848H930M110 894H930M110 940H930M110 986H930M110 1032H930M110 1078H930M110 1124H930M110 1170H930M110 1216H930M110 1262H930"/><path d="M130 222V1300" stroke="var(--accent)" stroke-width="1.4" opacity=".72"/></g><g fill="none" stroke="var(--accent2)" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M254 241c22-23 49-4 32 14-9 9-23 3-16-6 4-5 11-2 8 3m-9 3c-4 17-26 17-29 1m35-14c18-8 28 7 17 16m-55-2l-11 4m65-24l8-8M746 241c-22-23-49-4-32 14 9 9 23 3 16-6-4-5-11-2-8 3m9 3c4 17 26 17 29 1m-35-14c-18-8-28 7-17 16m55-2l11 4m-65-24l-8-8"/></g><g fill="none" stroke="var(--accent)" stroke-width="1.8"><path d="M490 1238l10-18 10 18-10 18Z"/><path d="M500 1224v28m-14-14h28"/></g>`,
      coffee_roaster: `<rect x="72" y="188" width="856" height="1090" fill="none" stroke="var(--accent2)" stroke-width="4"/><rect x="88" y="204" width="824" height="1058" fill="none" stroke="var(--accent)" stroke-width="1.5"/>`,
      invest_poster: `<g fill="none" stroke="var(--accent)" stroke-width="11" stroke-linecap="round" stroke-linejoin="round"><path d="M345 560c-88 2-133 57-146 130l-72 78c-22 25-4 55 26 43l102-55M655 560c89 0 135 55 148 130l53 43c26 21 52-3 37-31l-69-77"/><path d="M380 980l-23 75c-13 40-45 52-92 53-51 1-76 25-47 48 51 39 187 26 224-16l57-63m121-97 28 75c15 40 49 52 94 53 52 1 77 25 48 48-51 39-189 26-227-16l-62-63"/></g><path d="M315 555Q500 510 685 555V925Q500 1035 315 925Z" fill="var(--paper)" stroke="var(--accent)" stroke-width="14"/><ellipse cx="500" cy="555" rx="185" ry="64" fill="var(--paper)" stroke="var(--accent)" stroke-width="14"/><ellipse cx="500" cy="560" rx="145" ry="43" fill="none" stroke="var(--accent)" stroke-width="9"/><path d="M323 630h354M323 850h354" stroke="var(--accent)" stroke-width="13"/><path d="M357 644h286M357 837h286" stroke="var(--accent2)" stroke-width="6"/><ellipse cx="455" cy="725" rx="23" ry="42" fill="var(--accent)"/><ellipse cx="545" cy="725" rx="23" ry="42" fill="var(--accent)"/><path d="M474 785q26 25 52 0" fill="none" stroke="var(--accent)" stroke-width="8"/><path d="M400 620h28m144 0h28M402 870h28m140 0h28" stroke="var(--accent)" stroke-width="8"/><path d="M752 523l18-40 18 40 40 18-40 18-18 40-18-40-40-18Z" fill="none" stroke="var(--accent)" stroke-width="9"/><path d="M228 790l13-28 13 28 28 13-28 13-13 28-13-28-28-13Z" fill="none" stroke="var(--accent)" stroke-width="8"/>`,
      punk_manifesto: ``,
      green_starburst: `<path d="M10 34L244 10L365 72L550 5L691 61L970 16L990 255L923 407L989 632L923 819L989 1058L962 1458L725 1491L530 1432L345 1492L153 1439L15 1484L9 1190L64 1000L7 795L64 580L9 365Z" fill="var(--panel)"/><path d="M601 0L676 203L896 52L820 286L999 365L781 433L935 685L683 552L576 903L481 584L240 705L407 447L204 357L438 276L327 75L570 215Z" fill="var(--accent)"/><path d="M333 554L433 825L625 720L550 951L724 1021L535 1097L652 1316L430 1196L339 1492L249 1204L48 1440L141 1156L0 1164L113 950L0 826L202 871Z" fill="var(--accent2)"/>`,
      neon_overprint: `<path d="M500 118L577 350L821 240L694 462L930 564L692 640L852 881L601 753L500 1030L397 757L145 881L308 639L70 564L306 462L180 240L423 350Z" fill="var(--accent)"/>`,
    };
    shapes.scribe_gallery = `<rect x="84" y="196" width="832" height="1041" rx="12" fill="var(--paper)" fill-opacity=".22" stroke="var(--accent2)" stroke-width="1.8" opacity=".98"/><path d="M370 242V1222" stroke="var(--paper)" stroke-width="1.2" opacity=".32"/><path d="M398 492H886" stroke="var(--accent2)" stroke-width="1.6" opacity=".82"/><g fill="var(--accent2)" stroke="var(--accent2)" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" opacity=".95"><path d="M145 1168C195 1135 253 1090 330 1032" fill="none" stroke-width="4"/><path d="M185 1142C160 1120 165 1099 195 1102C201 1117 198 1132 185 1142Z"/><path d="M212 1121C210 1094 230 1082 251 1098C247 1114 232 1124 212 1121Z"/><path d="M241 1099C236 1072 253 1055 278 1067C275 1085 260 1098 241 1099Z"/><path d="M277 1072C279 1047 299 1036 318 1054C311 1070 296 1077 277 1072Z"/><path d="M181 1150C168 1170 148 1174 136 1157C146 1143 163 1140 181 1150Z"/></g>`;
    shapes.illuminated_broadside = `<path d="M82 164H918" stroke="var(--muted)" stroke-width="1.2" opacity=".72"/><rect x="100" y="200" width="800" height="1042" fill="none" stroke="var(--ink)" stroke-width="2.4" opacity=".96"/><rect x="112" y="212" width="776" height="1018" fill="none" stroke="var(--accent)" stroke-width="1.8" opacity=".9"/><path d="M154 388H846" stroke="var(--accent)" stroke-width="2.4" opacity=".9"/><g fill="none" stroke="var(--accent)" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" opacity=".96"><path d="M128 244c22-18 32 7 14 19-11 7-19 1-14-7m0 7c-7 12 5 20 15 8m-15-8c-15-4-17 11-5 14m-9-17l-5-9m24 27l6 9M872 244c-22-18-32 7-14 19 11 7 19 1 14-7m0 7c7 12-5 20-15 8m15-8c15-4 17 11 5 14m9-17l5-9m-24 27l-6 9M128 1212c22 18 32-7 14-19-11-7-19-1-14 7m0-7c-7-12 5-20 15-8m-15 8c-15 4-17 11-5 14m-9-17l-5 9m24-27l6 9M872 1212c-22 18-32-7-14-19 11-7 19-1 14 7m0-7c7-12-5-20-15-8m15 8c15-4 17 11 5 14m9-17l5 9m-24 27l-6-9"/></g><g fill="none" stroke="var(--accent2)" stroke-width="2.6" opacity=".96"><path d="M500 1112l18 18-18 18-18-18Z"/><circle cx="500" cy="1130" r="23"/><circle cx="500" cy="1130" r="7"/></g>`;
    return shared + (shapes[id] || "") + `</svg>`;
  }
  function overlayDecoration(id) {
    if (id === "coffee_roaster") return `<svg viewBox="0 0 1000 1500" preserveAspectRatio="none" aria-hidden="true"><g fill="var(--accent2)" stroke="var(--accent)" stroke-width="3"><g transform="translate(794 1047) rotate(30)"><ellipse rx="30" ry="44"/><path d="M-2-37C11-19-12 1 2 19c7 9 8 15 4 20" fill="none" stroke="var(--paper)" stroke-width="5"/></g><g transform="translate(858 1102) rotate(-22)"><ellipse rx="25" ry="37"/><path d="M-1-31C11-16-10 0 2 15c6 8 7 12 4 17" fill="none" stroke="var(--paper)" stroke-width="4"/></g><g transform="translate(780 1168) rotate(-40)"><ellipse rx="21" ry="31"/><path d="M-1-26C8-13-8 0 2 12c5 7 5 10 3 14" fill="none" stroke="var(--paper)" stroke-width="4"/></g><circle cx="852" cy="1184" r="4" fill="var(--accent)" stroke="none"/></g></svg>`;
    if (id !== "punk_manifesto") return "";
    return `<svg viewBox="0 0 1000 1500" preserveAspectRatio="none" aria-hidden="true"><g fill="var(--paper)" stroke="#161514" stroke-width="12" stroke-linejoin="round" stroke-linecap="round"><path d="M203 520c-32-38 21-100 68-63l441 359c39 32 52 77 16 112l-43 42c-37 36-84 20-75-23l10-45-406-331c-15-12-20-26-11-39Z"/><path d="M676 896l-148-120 24-31 160 130"/><path d="M206 510l48-56 34 31-43 57"/></g><g fill="var(--paper)" stroke="#161514" stroke-width="9"><path d="M758 956l19-46 19 46 46 19-46 19-19 46-19-46-46-19Z"/><path d="M580 1022l15-35 15 35 35 15-35 15-15 35-15-35-35-15Z"/></g><circle cx="728" cy="925" r="27" fill="var(--paper)" stroke="#161514" stroke-width="12"/></svg>`;
  }
  function renderTemplate(id, values = {}) {
    const spec = specs[id];
    if (!spec) throw new Error(`Unknown pin template: ${id}`);
    const board = document.getElementById("artboard");
    const props = { ...spec.defaults, ...values };
    props.fontName = titleCase(props.fontName || specimenFontNames[id] || "");
    for (const key of ["name", "line", "word", "kicker", "secondary"]) {
      if (props[key] !== undefined && !(key === "word" && /(?:[A-Z]{8,}|[a-z]{8,}|\d{6,})/u.test(props[key]))) props[key] = titleCase(props[key]);
    }
    const lineParts = String(props.line ?? "").split(/\r?\n/u);
    for (let index = 0; index < 3; index += 1) props[`line${index + 1}`] = lineParts[index] ?? "";
    if (id === "folio") {
      const [first, ...rest] = String(props.line1 ?? "").split(/\s+/u);
      props.line1a = first ?? "";
      props.line1b = rest.join(" ");
    }
    board.replaceChildren();
    board.className = `pin-board template--${id} font--${spec.font}`;
    board.dataset.liveFont = document.body.dataset.uploadedFont || "";
    board.style.setProperty("--bg", palettes[spec.palette].bg);
    if (document.body.dataset.uploadedFont) board.style.setProperty("--display-face", document.body.dataset.uploadedFont);
    board.style.setProperty("--bg2", palettes[spec.palette].bg2);
    for (const [key, value] of Object.entries(palettes[spec.palette])) board.style.setProperty(`--${key}`, value);
    const art = document.createElement("div");
    art.className = "pin-art";
    art.innerHTML = decoration(id);
    board.append(art);
    const overlayMarkup = overlayDecoration(id);
    if (overlayMarkup) {
      const overlay = document.createElement("div");
      overlay.className = "pin-overlay";
      overlay.innerHTML = overlayMarkup;
      board.append(overlay);
    }
    const nodes = [];
    for (const item of spec.elements) {
      const element = document.createElement("div");
      const scriptInkSafe = spec.font === "script" && item.fill;
      element.className = `pin-item role--${item.role}${item.hasBox ? " has-box" : ""}${item.overlap ? " overlap-intent" : ""}${item.align ? ` align--${item.align}` : ""}${scriptInkSafe ? " script-ink-safe" : ""}`;
      if (item.allowOverflow || scriptInkSafe) element.style.overflow = "visible";
      element.dataset.layoutItem = item.key;
      const [x, rawY, w, h] = item.box;
      const footerShift = item.key === "footer" && rawY === 86 && h === 3.2 ? 2.5 : item.key === "footSub" && rawY === 89.2 && h === 2.5 ? 2.9 : 0;
      const y = rawY + footerShift;
      const fittedStartSize = item.key.toLowerCase().includes("footer") ? Math.max(38.5, item.size) : item.key.toLowerCase().includes("footsub") ? Math.max(25.5, item.size) : item.size;
      Object.assign(element.style, { left: `${x}%`, top: `${y}%`, width: `${w}%`, height: `${h}%`, fontSize: `${fittedStartSize / 10}cqw`, lineHeight: item.leading || 1.02 });
      element.style.setProperty("--slot-size", `${fittedStartSize / 10}cqw`);
      if (item.track !== undefined) element.style.letterSpacing = `${item.track / 10}cqw`;
      if (item.align) element.style.textAlign = item.align;
      if (item.valign === "top") element.style.alignItems = "start";
      else if (item.valign === "bottom") element.style.alignItems = "end";
      const displayText = productionCopy(id, item, replaceTokens(item.text, props), props);
      if (item.fill) {
        element.classList.add("has-fill");
        const content = document.createElement("span");
        content.className = "pin-content pin-content--fill";
        content.textContent = displayText;
        element.append(content);
      } else element.textContent = displayText;
      if (item.hasBox) element.style.setProperty("--box-tone", item.role === "darkInk" ? "var(--accent)" : "var(--panel)");
      if (item.role === "darkInk") element.style.color = "var(--darkInk)";
      board.append(element);
      nodes.push({ element, item: { ...item, size: fittedStartSize } });
    }
    board.append(art);
    for (const node of nodes) fitText(node.element, node.item);
    board.dataset.palette = spec.palette;
    board.dataset.template = id;
    return { props, report: getLayoutReport() };
  }
  function fitText(element, item) {
    let size = item.size / 10;
    const min = Math.max(1.5, size * 0.66);
    element.style.fontSize = `${size}cqw`;
    for (let index = 0; index < 34; index += 1) {
      const widthFits = element.scrollWidth <= element.clientWidth + 1;
      if (widthFits && (item.allowOverflow || element.scrollHeight <= element.clientHeight + 1)) break;
      size *= 0.96;
      if (size < min) break;
      element.style.fontSize = `${size}cqw`;
    }
    if (item.fill) {
      const content = element.querySelector(".pin-content--fill");
      content.style.transform = "none";
      const range = document.createRange();
      range.selectNodeContents(content);
      const textRect = range.getBoundingClientRect();
      const textWidth = textRect.width;
      const scriptSafety = element.classList.contains("script-ink-safe") ? 0.88 : 1;
      const available = element.clientWidth * scriptSafety - 8;
      const availableHeight = element.clientHeight - 4;
      const scaleY = !item.allowOverflow && textRect.height > 0
        ? Math.min(item.scaleY || 1, availableHeight / textRect.height)
        : item.scaleY || 1;
      if (textWidth > 0 && available > 0) content.style.transform = `scaleX(${Math.max(0.55, Math.min(3.5, available / textWidth))}) scaleY(${scaleY})`;
    }
  }
  function contrastRatio(foreground, background) {
    const rgb = (hex) => hex.replace("#", "").match(/.{2}/g).map((part) => parseInt(part, 16) / 255).map((v) => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
    const luminance = (hex) => { const [r, g, b] = rgb(hex); return 0.2126 * r + 0.7152 * g + 0.0722 * b; };
    const a = luminance(foreground), b = luminance(background);
    return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
  }
  function getLayoutReport() {
    const board = document.getElementById("artboard");
    const boardRect = board.getBoundingClientRect();
    const items = [...board.querySelectorAll("[data-layout-item]")];
    const outOfBounds = [], stackOverlaps = [];
    for (const item of items) {
      const r = item.getBoundingClientRect();
      if (r.left < boardRect.left - 1 || r.top < boardRect.top - 1 || r.right > boardRect.right + 1 || r.bottom > boardRect.bottom + 1) outOfBounds.push(item.dataset.layoutItem);
    }
    for (let i = 0; i < items.length; i += 1) for (let j = i + 1; j < items.length; j += 1) {
      if (items[i].classList.contains("overlap-intent") || items[j].classList.contains("overlap-intent")) continue;
      const a = items[i].getBoundingClientRect(), b = items[j].getBoundingClientRect();
      const overlapX = Math.min(a.right, b.right) - Math.max(a.left, b.left);
      const overlapY = Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top);
      if (overlapX > 1 && overlapY > 1 && items[i].textContent.trim() && items[j].textContent.trim()) stackOverlaps.push(`${items[i].dataset.layoutItem}/${items[j].dataset.layoutItem}`);
    }
    const paperContrast = contrastRatio(getComputedStyle(board).getPropertyValue("--ink").trim(), getComputedStyle(board).getPropertyValue("--bg").trim());
    return { outOfBounds, stackOverlaps, inkOnPaperContrast: Number(paperContrast.toFixed(2)), headlineFontSize: getComputedStyle(board.querySelector(".role--wordmark, .role--display, .role--accent") || board).fontSize };
  }
  function configureTemplate(values = {}) {
    const id = document.getElementById("artboard").dataset.template || document.body.dataset.template;
    return renderTemplate(id, values);
  }
  function start() {
    const id = document.body.dataset.template || new URL(location.href).searchParams.get("template") || "hero";
    document.body.dataset.template = id;
    const spec = specs[id];
    document.getElementById("studio-title").textContent = spec.title;
    document.getElementById("studio-copy").textContent = "Adjust the copy, test your font, and review the composition at full pin scale.";
    const state = { ...spec.defaults };
    const controls = document.getElementById("template-controls");
    for (const key of ["name", "line", "word", "secondary"]) {
      const label = document.createElement("label");
      label.className = "editor-control";
      label.innerHTML = `<span>${({ name: "Main Phrase / Name", line: "Supporting Phrase", word: "Specimen Word", secondary: "Secondary Line" })[key]}</span>`;
      const input = key === "line" || key === "name" && spec.defaults.name?.includes("\n") ? document.createElement("textarea") : document.createElement("input");
      input.value = state[key] ?? "";
      input.addEventListener("input", () => { state[key] = input.value; renderTemplate(id, state); });
      label.append(input); controls.append(label);
    }
    const font = document.getElementById("font-file");
    font.addEventListener("change", async () => {
      const file = font.files?.[0]; if (!file) return;
      const url = URL.createObjectURL(file); const face = new FontFace("PinLive", `url("${url}")`);
      document.getElementById("font-status").textContent = "Loading font…";
      try { await face.load(); document.fonts.add(face); document.body.dataset.uploadedFont = "PinLive"; await document.fonts.ready; renderTemplate(id, state); document.getElementById("font-status").textContent = `Loaded ${file.name}`; }
      catch (error) { document.getElementById("font-status").textContent = `Could not load font: ${error.message}`; }
    });
    window.configureTemplate = (props = {}) => { Object.assign(state, props); return renderTemplate(id, state).report; };
    window.getLayoutReport = getLayoutReport;
    renderTemplate(id, state);
    document.fonts.ready.then(() => renderTemplate(id, state));
  }
  window.PinStudio = { specs, palettes, renderTemplate, getLayoutReport, start };
  document.addEventListener("DOMContentLoaded", start);
})();
