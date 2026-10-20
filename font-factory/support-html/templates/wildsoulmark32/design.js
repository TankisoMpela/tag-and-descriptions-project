window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "wildsoulmark32",
  "title": "Wild Soul Mark",
  "skin": "orange",
  "layout": "wordmark",
  "paper": "#080808",
  "ink": "#f3d9aa",
  "accent": "#f28d12",
  "muted": "#7d766a",
  "grain": 0.12,
  "defaults": {
    "headline": "Wild Soul",
    "line2": "A Mark In Flower",
    "descriptor": "A Singular Word With Character",
    "overline": "An Ornament In Ink",
    "footer": "Studio Edition · 05",
    "scale": 1.02,
    "tracking": -0.055
  },
  "elements": [
    {
      "type": "image",
      "asset": "rose-engraving",
      "x": 0.16,
      "y": 0.14,
      "w": 0.68,
      "h": 0.65,
      "opacity": 0.25,
      "blend": "screen",
      "filter": "grayscale(1)"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.09,
      "y": 0.34,
      "w": 0.82,
      "h": 0.3,
      "max": 260,
      "kind": "display",
      "color": "var(--br-accent)",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.15,
      "y": 0.83,
      "w": 0.7,
      "h": 0.045,
      "max": 15,
      "kind": "label",
      "color": "var(--br-ink)",
      "tracking": 0.14,
      "display": false,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.25,
      "y": 0.91,
      "w": 0.5,
      "h": 0.035,
      "max": 12,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.13,
      "display": false,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "text": "A Mark In Flower",
      "x": 0.28,
      "y": 0.875,
      "w": 0.44,
      "h": 0.035,
      "max": 12,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.11,
      "display": false
    }
  ],
  "literalKeys": []
}
);
