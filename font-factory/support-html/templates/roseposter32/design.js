window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "roseposter32",
  "title": "Rose Garden Broadside",
  "skin": "ink",
  "layout": "floral",
  "paper": "#171514",
  "ink": "#f4ead3",
  "accent": "#b88555",
  "muted": "#c8bdab",
  "grain": 0.17,
  "defaults": {
    "headline": "Rose Garden",
    "line2": "A Midnight Bloom",
    "descriptor": "A Study In Ornamental Letterforms",
    "overline": "Night Garden",
    "footer": "No. 01 · 2026",
    "scale": 1.03,
    "tracking": -0.035
  },
  "elements": [
    {
      "type": "text",
      "key": "overline",
      "x": 0.055,
      "y": 0.035,
      "w": 0.26,
      "h": 0.05,
      "max": 13,
      "kind": "label",
      "color": "var(--br-accent)",
      "tracking": 0.17,
      "display": false,
      "fitHeight": 0.9,
      "align": "flex-start"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.19,
      "y": 0.11,
      "w": 0.62,
      "h": 0.19,
      "max": 205,
      "kind": "display",
      "fitHeight": 0.94,
      "fitWidth": 0.98
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.18,
      "y": 0.305,
      "w": 0.64,
      "h": 0.19,
      "max": 205,
      "kind": "display",
      "fitHeight": 0.94,
      "fitWidth": 0.98
    },
    {
      "type": "image",
      "asset": "rose-engraving",
      "x": 0.18,
      "y": 0.55,
      "w": 0.64,
      "h": 0.42,
      "opacity": 0.88
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.27,
      "y": 0.505,
      "w": 0.46,
      "h": 0.045,
      "max": 17,
      "kind": "label",
      "color": "var(--br-ink)",
      "tracking": 0.08,
      "display": false,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.78,
      "y": 0.035,
      "w": 0.165,
      "h": 0.05,
      "max": 13,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.16,
      "display": false,
      "fitHeight": 0.9,
      "align": "flex-start"
    }
  ],
  "literalKeys": []
}
);
