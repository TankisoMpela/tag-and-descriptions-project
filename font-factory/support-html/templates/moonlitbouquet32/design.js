window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "moonlitbouquet32",
  "title": "Moonlit Bouquet Poster",
  "skin": "ink",
  "layout": "floral",
  "paper": "#080808",
  "ink": "#f0e8d9",
  "accent": "#f28713",
  "muted": "#7e7a72",
  "grain": 0.16,
  "defaults": {
    "headline": "Moonlight",
    "line2": "Woven Dreams",
    "descriptor": "Evermore",
    "overline": "A Bohemian Letter Study",
    "footer": "Edition · 03",
    "scale": 0.98,
    "tracking": -0.035
  },
  "elements": [
    {
      "type": "image",
      "asset": "rose-engraving",
      "x": 0,
      "y": 0.075,
      "w": 0.42,
      "h": 0.89,
      "opacity": 0.26,
      "blend": "screen",
      "filter": "grayscale(1)"
    },
    {
      "type": "image",
      "asset": "rose-engraving",
      "x": 0.58,
      "y": 0.075,
      "w": 0.42,
      "h": 0.89,
      "opacity": 0.26,
      "blend": "screen",
      "filter": "grayscale(1) scaleX(-1)"
    },
    {
      "type": "text",
      "key": "overline",
      "x": 0.055,
      "y": 0.075,
      "w": 0.4,
      "h": 0.045,
      "max": 13,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.1,
      "display": false,
      "align": "flex-start",
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.72,
      "y": 0.075,
      "w": 0.22,
      "h": 0.045,
      "max": 13,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.1,
      "display": false,
      "align": "flex-end",
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.08,
      "y": 0.16,
      "w": 0.84,
      "h": 0.22,
      "max": 240,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.055,
      "y": 0.385,
      "w": 0.89,
      "h": 0.25,
      "max": 245,
      "kind": "display",
      "color": "var(--br-accent)",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.1,
      "y": 0.655,
      "w": 0.8,
      "h": 0.24,
      "max": 238,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    }
  ],
  "literalKeys": []
}
);
