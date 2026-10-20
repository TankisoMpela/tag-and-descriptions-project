window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "checkerword32",
  "title": "Six Tile Word Board",
  "skin": "checker",
  "layout": "checker",
  "paper": "#171615",
  "ink": "#f0e8d7",
  "accent": "#aa744a",
  "muted": "#9c9486",
  "grain": 0.07,
  "defaults": {
    "headline": "Shine",
    "line2": "Hero",
    "descriptor": "Bright",
    "overline": "Repeating Letterforms",
    "footer": "Three Words · Six Panels",
    "scale": 1,
    "tracking": -0.025
  },
  "elements": [
    {
      "type": "tilegrid",
      "x": 0,
      "y": 0,
      "w": 1,
      "h": 1,
      "cols": 3,
      "rows": 2,
      "tiles": [
        {
          "key": "headline",
          "tone": "ink",
          "kind": "initial"
        },
        {
          "key": "headline",
          "tone": "paper",
          "kind": "word",
          "repeat": true
        },
        {
          "key": "descriptor",
          "tone": "ink",
          "kind": "initial"
        },
        {
          "key": "line2",
          "tone": "paper",
          "kind": "word",
          "repeat": true
        },
        {
          "key": "line2",
          "tone": "ink",
          "kind": "initial"
        },
        {
          "key": "descriptor",
          "tone": "paper",
          "kind": "word",
          "repeat": true
        }
      ]
    }
  ],
  "literalKeys": []
}
);
