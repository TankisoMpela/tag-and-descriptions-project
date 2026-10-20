window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "legacycrypt32",
  "title": "Legacy And Crypt Display",
  "skin": "ink",
  "layout": "gigposter",
  "paper": "#151413",
  "ink": "#f3ead5",
  "accent": "#d7772a",
  "muted": "#918877",
  "grain": 0.2,
  "defaults": {
    "headline": "Legacy",
    "line2": "Crypt",
    "descriptor": "Slant",
    "overline": "Regular",
    "footer": "No. 03",
    "scale": 1,
    "tracking": -0.04
  },
  "elements": [
    {
      "type": "image",
      "asset": "gargoyle-crest",
      "x": 0.17,
      "y": 0.12,
      "w": 0.66,
      "h": 0.76,
      "opacity": 0.18,
      "blend": "screen",
      "filter": "grayscale(1)"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.055,
      "y": 0.105,
      "w": 0.89,
      "h": 0.27,
      "max": 230,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "text",
      "key": "overline",
      "x": 0.39,
      "y": 0.025,
      "w": 0.22,
      "h": 0.045,
      "max": 30,
      "min": 20,
      "kind": "display",
      "color": "var(--br-accent)",
      "tracking": -0.025,
      "fitWidth": 0.98,
      "fitHeight": 0.92
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.08,
      "y": 0.47,
      "w": 0.84,
      "h": 0.30,
      "max": 285,
      "kind": "display",
      "italic": true,
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "badge",
      "key": "footer",
      "x": 0.055,
      "y": 0.865,
      "w": 0.15,
      "h": 0.055,
      "max": 20,
      "display": true
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.80,
      "y": 0.78,
      "w": 0.15,
      "h": 0.045,
      "max": 28,
      "min": 20,
      "kind": "display",
      "color": "var(--br-accent)",
      "tracking": -0.025,
      "fitHeight": 0.9
    },
    {
      "type": "badge",
      "text": "2026",
      "x": 0.795,
      "y": 0.865,
      "w": 0.15,
      "h": 0.055,
      "max": 20,
      "display": true
    },
    {
      "type": "text",
      "text": "Combining Classical Shapes With Slanted Energy",
      "x": 0.2,
      "y": 0.93,
      "w": 0.6,
      "h": 0.03,
      "max": 12,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.08,
      "display": false,
      "fitHeight": 0.9
    }
  ],
  "literalKeys": []
}
);
