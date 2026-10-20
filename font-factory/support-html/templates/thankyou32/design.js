window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "thankyou32",
  "title": "Thank You Skull Poster",
  "skin": "ink",
  "layout": "gigposter",
  "paper": "#161514",
  "ink": "#f3ead7",
  "accent": "#f05a1d",
  "muted": "#a19a8e",
  "grain": 0.18,
  "defaults": {
    "headline": "Thank",
    "line2": "You",
    "descriptor": "Combining Blackletter Influence And Vintage Character\nWith Thanks For Your Support",
    "overline": "With Appreciation",
    "footer": "A Closing Note · 10",
    "scale": 1,
    "tracking": -0.045
  },
  "elements": [
    {
      "type": "image",
      "asset": "thankyou-skull-top",
      "x": 0.735,
      "y": 0.04,
      "w": 0.245,
      "h": 0.25,
      "opacity": 1,
      "fit": "contain"
    },
    {
      "type": "image",
      "asset": "thankyou-skull-bottom",
      "x": 0.05,
      "y": 0.55,
      "w": 0.27,
      "h": 0.29,
      "opacity": 1,
      "fit": "contain"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.09,
      "y": 0.1,
      "w": 0.72,
      "h": 0.29,
      "max": 275,
      "kind": "display",
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.45,
      "y": 0.405,
      "w": 0.44,
      "h": 0.32,
      "max": 280,
      "kind": "display",
      "color": "var(--br-accent)",
      "italic": true,
      "fitWidth": 0.98,
      "fitHeight": 0.95
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.2,
      "y": 0.91,
      "w": 0.6,
      "h": 0.07,
      "max": 11,
      "kind": "label",
      "color": "var(--br-ink)",
      "tracking": 0.08,
      "display": false,
      "multiline": true,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "text": "Regular",
      "x": 0.035,
      "y": 0.925,
      "w": 0.14,
      "h": 0.04,
      "max": 18,
      "kind": "display",
      "color": "var(--br-ink)",
      "tracking": -0.02,
      "display": false,
      "min": 12
    },
    {
      "type": "text",
      "text": "Slant",
      "x": 0.825,
      "y": 0.925,
      "w": 0.14,
      "h": 0.04,
      "max": 18,
      "kind": "display",
      "color": "var(--br-ink)",
      "tracking": -0.02,
      "display": false,
      "min": 12
    },
    {
      "type": "text",
      "text": "Artisan",
      "x": 0.33,
      "y": 0.58,
      "w": 0.105,
      "h": 0.055,
      "max": 34,
      "min": 14,
      "kind": "display",
      "color": "var(--br-accent)",
      "display": false
    }
  ],
  "literalKeys": []
}
);
