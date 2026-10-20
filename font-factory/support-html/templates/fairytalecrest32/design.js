window.ReferenceTemplate = window.BlackletterReferenceFactory.create({
  "id": "fairytalecrest32",
  "title": "Fairytale Crest Display",
  "skin": "orange",
  "layout": "floral",
  "paper": "#080808",
  "ink": "#f5d9a2",
  "accent": "#f28d12",
  "muted": "#8d8679",
  "grain": 0.12,
  "defaults": {
    "headline": "Fairytale",
    "line2": "Multilingual Support",
    "descriptor": "A Letterform Study",
    "overline": "The",
    "footer": "Chapter 01 · 2026",
    "scale": 0.95,
    "tracking": -0.045
  },
  "elements": [
    {
      "type": "image",
      "asset": "rose-engraving",
      "x": 0.22,
      "y": 0.11,
      "w": 0.56,
      "h": 0.75,
      "opacity": 0.18,
      "blend": "screen",
      "filter": "grayscale(1)"
    },
    {
      "type": "text",
      "key": "overline",
      "x": 0.245,
      "y": 0.16,
      "w": 0.19,
      "h": 0.15,
      "max": 82,
      "kind": "display",
      "color": "var(--br-accent)"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.06,
      "y": 0.26,
      "w": 0.88,
      "h": 0.43,
      "max": 330,
      "kind": "display",
      "color": "var(--br-accent)"
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.53,
      "y": 0.695,
      "w": 0.39,
      "h": 0.05,
      "max": 17,
      "kind": "label",
      "color": "#f2ead7",
      "tracking": 0.12
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.53,
      "y": 0.75,
      "w": 0.39,
      "h": 0.04,
      "max": 13,
      "kind": "label",
      "color": "#e5dcc6",
      "tracking": 0.1,
      "display": false,
      "align": "flex-start",
      "textAlign": "left"
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.31,
      "y": 0.895,
      "w": 0.38,
      "h": 0.035,
      "max": 12,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.14,
      "display": false,
      "align": "center"
    }
  ],
  "literalKeys": []
});
