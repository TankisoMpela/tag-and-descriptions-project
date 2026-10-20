window.ReferenceTemplate = window.BlackletterReferenceFactory.create({
  "id": "bettersunday32",
  "title": "Better Sunday Date Pair",
  "skin": "cream",
  "layout": "doublecard",
  "paper": "#171615",
  "ink": "#f4eddd",
  "accent": "#a89976",
  "muted": "#aaa08f",
  "grain": 0.08,
  "defaults": {
    "headline": "Better",
    "line2": "Sunday",
    "descriptor": "Date",
    "overline": "Pairing No. 07",
    "footer": "Weekend Edition",
    "scale": 1,
    "tracking": -0.03
  },
  "elements": [
    {
      "type": "panel",
      "x": 0.075,
      "y": 0.085,
      "w": 0.4,
      "h": 0.83,
      "tone": "cream",
      "radius": "30px",
      "border": true
    },
    {
      "type": "panel",
      "x": 0.525,
      "y": 0.085,
      "w": 0.4,
      "h": 0.83,
      "tone": "cream",
      "radius": "30px",
      "border": true
    },
    {
      "type": "initial",
      "x": 0.095,
      "y": 0.13,
      "w": 0.36,
      "h": 0.7,
      "key": "headline",
      "size": 620,
      "squareSize": 500,
      "color": "#171615"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.56,
      "y": 0.13,
      "w": 0.34,
      "h": 0.2,
      "max": 160,
      "kind": "display",
      "color": "#171615",
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.56,
      "y": 0.38,
      "w": 0.34,
      "h": 0.2,
      "max": 160,
      "kind": "display",
      "color": "#171615",
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.56,
      "y": 0.63,
      "w": 0.34,
      "h": 0.2,
      "max": 160,
      "kind": "display",
      "color": "#171615",
      "fitHeight": 0.9
    }
  ],
  "literalKeys": []
});
