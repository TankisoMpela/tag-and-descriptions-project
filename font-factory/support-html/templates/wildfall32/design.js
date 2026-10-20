window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "wildfall32",
  "title": "Wildfall Landscape Poster",
  "skin": "photo",
  "layout": "landscape",
  "paper": "#1c211f",
  "ink": "#f4cc69",
  "accent": "#f4cc69",
  "muted": "#d7c29a",
  "grain": 0.1,
  "defaults": {
    "headline": "Mistfall",
    "line2": "Highlands",
    "descriptor": "A Classy Blackletter Typeface",
    "overline": "Marva Design Presents",
    "footer": "2026 · All Rights Reserved",
    "scale": 0.93,
    "tracking": -0.055
  },
  "elements": [
    {
      "type": "image",
      "asset": "highland-waterfall",
      "x": 0,
      "y": 0,
      "w": 1,
      "h": 1,
      "opacity": 1
    },
    {
      "type": "shade",
      "x": 0,
      "y": 0,
      "w": 1,
      "h": 1,
      "opacity": 0.46
    },
    {
      "type": "text",
      "key": "overline",
      "x": 0.3,
      "y": 0.105,
      "w": 0.4,
      "h": 0.055,
      "max": 16,
      "kind": "label",
      "color": "#f7d783",
      "tracking": 0.12,
      "display": false,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.11,
      "y": 0.23,
      "w": 0.78,
      "h": 0.25,
      "max": 235,
      "kind": "display",
      "color": "#f4cc69",
      "fitWidth": 0.98,
      "fitHeight": 0.94
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.11,
      "y": 0.48,
      "w": 0.78,
      "h": 0.25,
      "max": 235,
      "kind": "display",
      "color": "#f4cc69",
      "fitWidth": 0.98,
      "fitHeight": 0.94
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.17,
      "y": 0.78,
      "w": 0.66,
      "h": 0.045,
      "max": 16,
      "kind": "label",
      "color": "#f8ebcd",
      "tracking": 0.13,
      "display": false,
      "fitHeight": 0.92
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.17,
      "y": 0.825,
      "w": 0.66,
      "h": 0.04,
      "max": 14,
      "kind": "label",
      "color": "#eadcb8",
      "tracking": 0.16,
      "display": false,
      "fitHeight": 0.9
    }
  ],
  "literalKeys": []
}
);
