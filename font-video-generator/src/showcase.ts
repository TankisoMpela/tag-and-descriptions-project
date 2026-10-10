export type ShowcaseSegment = {
  text: string;
  seconds: number;
  fontSize: number;
  charactersPerSecond: number;
};

export type ShowcaseProps = {
  fontName: string;
  segments: ShowcaseSegment[];
  width?: number;
  height?: number;
  backgroundColor?: string;
  textColor?: string;
};

export const DEFAULT_SHOWCASE: ShowcaseProps = {
  fontName: "Overtake",
  segments: [
    {text: "Built bold.", seconds: 7, fontSize: 300, charactersPerSecond: 10},
    {text: "Made to move.", seconds: 7, fontSize: 294, charactersPerSecond: 10},
    {text: "Impact.", seconds: 7, fontSize: 288, charactersPerSecond: 10},
    {text: "Strong shapes lead boldly.", seconds: 7, fontSize: 300, charactersPerSecond: 10},
    {text: "Overtake", seconds: 7, fontSize: 340, charactersPerSecond: 8},
  ],
};
