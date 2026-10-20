window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "flowerpair32",
  "title": "Flower And Monogram Pair",
  "skin": "cream",
  "layout": "doublecard",
  "paper": "#e8e1d3",
  "contrastPaper": "#171615",
  "ink": "#f2ead9",
  "accent": "#b14939",
  "muted": "#726b5c",
  "grain": 0.08,
  "defaults": {
    "headline": "Flower\nBloom",
    "line2": "Collaboration With The Type Foundry",
    "descriptor": "Blooming Season",
    "overline": "Botanical Pairings",
    "footer": "Spring Study · 02",
    "scale": 1,
    "tracking": -0.025
  },
  "elements": [
    {
      "type": "panel",
      "x": 0.07,
      "y": 0.09,
      "w": 0.42,
      "h": 0.82,
      "tone": "ink",
      "radius": "28px",
      "border": true
    },
    {
      "type": "panel",
      "x": 0.51,
      "y": 0.09,
      "w": 0.42,
      "h": 0.82,
      "tone": "ink",
      "radius": "28px",
      "border": true
    },
    {
      "type": "frame",
      "x": 0.135,
      "y": 0.44,
      "w": 0.32,
      "h": 0.29,
      "borderColor": "rgba(242,234,217,.88)",
      "z": 3
    },
    {
      "type": "image",
      "asset": "flowerpair-bloom",
      "x": 0.12,
      "y": 0.435,
      "w": 0.36,
      "h": 0.30,
      "opacity": 1,
      "fit": "contain",
      "objectPosition": "center",
      "z": 4
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.1,
      "y": 0.16,
      "w": 0.36,
      "h": 0.27,
      "max": 170,
      "kind": "display",
      "multiline": true,
      "fitWidth": 0.97,
      "fitHeight": 0.94
    },
    {
      "type": "text",
      "key": "overline",
      "x": 0.12,
      "y": 0.115,
      "w": 0.32,
      "h": 0.045,
      "max": 12,
      "kind": "label",
      "color": "var(--br-accent)",
      "tracking": 0.14,
      "display": false,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.12,
      "y": 0.78,
      "w": 0.32,
      "h": 0.04,
      "max": 12,
      "kind": "label",
      "color": "var(--br-ink)",
      "tracking": 0.04,
      "display": false,
      "fitHeight": 0.9
    },
    {
      "type": "initial",
      "x": 0.56,
      "y": 0.19,
      "w": 0.32,
      "h": 0.48,
      "key": "headline",
      "size": 520
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.55,
      "y": 0.81,
      "w": 0.34,
      "h": 0.05,
      "max": 16,
      "kind": "label",
      "color": "var(--br-ink)",
      "tracking": 0.05,
      "display": false,
      "fitHeight": 0.9
    },
  ],
  "literalKeys": []
}
);
