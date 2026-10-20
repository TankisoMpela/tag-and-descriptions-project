window.ReferenceTemplate = window.BlackletterReferenceFactory.create(
{
  "id": "instrumentboard32",
  "title": "Letterform Instrument Board",
  "skin": "ink",
  "layout": "instrument",
  "paper": "#101113",
  "ink": "#f1f0ec",
  "accent": "#e1bd45",
  "muted": "#a5a5a0",
  "grain": 0.07,
  "defaults": {
    "headline": "Letterforms",
    "line2": "Type Specimen",
    "descriptor": "Weights · Width · Rhythm",
    "overline": "Specimen Instrument",
    "footer": "Variable Type Study",
    "scale": 0.96,
    "tracking": -0.02
  },
  "elements": [
    {
      "type": "frame",
      "x": 0.045,
      "y": 0.06,
      "w": 0.91,
      "h": 0.88
    },
    {
      "type": "rule",
      "x": 0.045,
      "y": 0.17,
      "w": 0.91,
      "h": 0.002
    },
    {
      "type": "rule",
      "x": 0.045,
      "y": 0.84,
      "w": 0.91,
      "h": 0.002
    },
    {
      "type": "text",
      "key": "overline",
      "x": 0.07,
      "y": 0.085,
      "w": 0.3,
      "h": 0.055,
      "max": 14,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.06,
      "display": false,
      "align": "flex-start"
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.66,
      "y": 0.085,
      "w": 0.27,
      "h": 0.055,
      "max": 14,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.06,
      "display": false,
      "align": "flex-end"
    },
    {
      "type": "dial",
      "x": 0.005,
      "y": 0.32,
      "w": 0.155,
      "h": 0.34,
      "label": "100"
    },
    {
      "type": "dial",
      "x": 0.84,
      "y": 0.32,
      "w": 0.155,
      "h": 0.34,
      "label": "800"
    },
    {
      "type": "text",
      "key": "headline",
      "x": 0.17,
      "y": 0.23,
      "w": 0.66,
      "h": 0.2,
      "max": 238,
      "kind": "display",
      "fitWidth": 0.96,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "line2",
      "x": 0.17,
      "y": 0.46,
      "w": 0.66,
      "h": 0.2,
      "max": 238,
      "kind": "display",
      "fitWidth": 0.96,
      "fitHeight": 0.9
    },
    {
      "type": "rule",
      "x": 0.16,
      "y": 0.735,
      "w": 0.68,
      "h": 0.002,
      "color": "#e1bd45"
    },
    {
      "type": "text",
      "key": "descriptor",
      "x": 0.32,
      "y": 0.755,
      "w": 0.36,
      "h": 0.045,
      "max": 16,
      "kind": "label",
      "color": "var(--br-accent)",
      "tracking": 0.14,
      "display": false,
      "fitHeight": 0.9
    },
    {
      "type": "text",
      "key": "footer",
      "x": 0.58,
      "y": 0.865,
      "w": 0.34,
      "h": 0.04,
      "max": 13,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.1,
      "display": false,
      "text": "OpenType & Variable Support",
      "align": "flex-end",
      "textAlign": "right"
    },
    {
      "type": "text",
      "text": "−   I   •   •   •   •   •   •   •   I   +",
      "x": 0.15,
      "y": 0.715,
      "w": 0.7,
      "h": 0.045,
      "max": 24,
      "kind": "label",
      "color": "var(--br-ink)",
      "tracking": 0.04,
      "display": false
    },
    {
      "type": "text",
      "text": "Designed By The Foundry",
      "x": 0.08,
      "y": 0.865,
      "w": 0.34,
      "h": 0.035,
      "max": 12,
      "kind": "label",
      "color": "var(--br-muted)",
      "tracking": 0.06,
      "display": false,
      "textAlign": "left",
      "align": "flex-start"
    }
  ],
  "literalKeys": []
}
);
