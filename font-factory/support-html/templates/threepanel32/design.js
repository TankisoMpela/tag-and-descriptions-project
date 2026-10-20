window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "threepanel32",
  "title": "Botanical Three Panel",
  "skin": "cream",
  "layout": "triptych",
  "paper": "#f1e6d8",
  "ink": "#f2ead8",
  "accent": "#8f512c",
  "muted": "#a79c8b",
  "grain": 0.18,
  "defaults": {
    "headline": "Thinker",
    "line2": "History",
    "descriptor": "A Floral Letter Study",
    "overline": "Garden Notes",
    "footer": "Blooming Season",
    "scale": 1.02,
    "tracking": -0.04
  },
  "elements": [
    {
      "type": "panel",
      "x": 0.06,
      "y": 0.075,
      "w": 0.16,
      "h": 0.85,
      "tone": "ink",
      "radius": "20px",
      "border": true
    },
    {
      "type": "panel",
      "x": 0.78,
      "y": 0.075,
      "w": 0.16,
      "h": 0.85,
      "tone": "ink",
      "radius": "20px",
      "border": true
    },
    {
      "type": "panel",
      "x": 0.265,
      "y": 0.075,
      "w": 0.47,
      "h": 0.85,
      "tone": "ink",
      "radius": "0",
      "border": true
    },
    {
      "type": "frame",
      "x": 0.285,
      "y": 0.095,
      "w": 0.43,
      "h": 0.76,
      "z": 8,
      "borderColor": "rgba(242,234,216,.88)"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.295,
      "y": 0.11,
      "w": 0.41,
      "h": 0.17,
      "max": 176,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.92
    },
    {
      "type": "image",
      "asset": "rose-engraving",
      "x": 0.295,
      "y": 0.285,
      "w": 0.41,
      "h": 0.36,
      "opacity": 0.94,
      "fit": "cover"
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.295,
      "y": 0.65,
      "w": 0.41,
      "h": 0.17,
      "max": 176,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.92
    },
    {
      "type": "text",
      "key": "overline",
      "x": 0.06,
      "y": 0.11,
      "w": 0.16,
      "h": 0.78,
      "max": 150,
      "kind": "display",
      "color": "#f2ead8",
      "fitWidth": 0.96,
      "fitHeight": 0.94,
      "rotate": 90
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.78,
      "y": 0.11,
      "w": 0.16,
      "h": 0.78,
      "max": 150,
      "kind": "display",
      "color": "#f2ead8",
      "fitWidth": 0.96,
      "fitHeight": 0.94,
      "rotate": 90
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.29,
      "y": 0.875,
      "w": 0.42,
      "h": 0.045,
      "max": 13,
      "kind": "label",
      "color": "var(--br-accent)",
      "tracking": 0.09,
      "display": false,
      "fitHeight": 0.9
    }
  ],
  "literalKeys": [],
  "contrastPaper": "#191817"
}
);
