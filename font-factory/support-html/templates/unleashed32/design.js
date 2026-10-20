window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "unleashed32",
  "title": "Unleashed Infernal Poster",
  "skin": "ink",
  "layout": "gigposter",
  "paper": "#141312",
  "ink": "#f2e8d1",
  "accent": "#eb4d18",
  "muted": "#9c9180",
  "grain": 0.19,
  "defaults": {
    "headline": "Unleashed",
    "line2": "Infernal",
    "descriptor": "A Fierce Display Of Shadow And Fire",
    "overline": "A New Chapter",
    "footer": "Poster Study · 07",
    "scale": 0.96,
    "tracking": -0.045
  },
  "elements": [
    {
      "type": "text",
      "key": "headline",
      "x": 0.055,
      "y": 0.045,
      "w": 0.89,
      "h": 0.26,
      "max": 270,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "image",
      "asset": "wolf-wings",
      "x": 0.08,
      "y": 0.2,
      "w": 0.84,
      "h": 0.57,
      "opacity": 0.9,
      "blend": "screen",
      "filter": "grayscale(1) sepia(1) saturate(5) hue-rotate(330deg)"
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.055,
      "y": 0.61,
      "w": 0.89,
      "h": 0.27,
      "max": 270,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.62,
      "y": 0.91,
      "w": 0.3,
      "h": 0.035,
      "max": 12,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.11,
      "display": false,
      "align": "flex-end",
      "fitHeight": 0.9
    }
  ],
  "literalKeys": []
}
);
