import {loadFont} from "@remotion/fonts";
import {
  CalculateMetadataFunction,
  Composition,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {useLayoutEffect, useRef, useState} from "react";
import {DEFAULT_SHOWCASE, ShowcaseProps} from "./showcase";

const fontFamily = "ShowcaseFont";

loadFont({
  family: fontFamily,
  url: staticFile("fonts/ShowcaseFont.woff2"),
});

const calculateMetadata: CalculateMetadataFunction<ShowcaseProps> = ({props}) => ({
  durationInFrames: props.segments.reduce(
    (total, segment) => total + Math.round(segment.seconds * 30),
    0,
  ),
  width: props.width ?? 1920,
  height: props.height ?? 1080,
});

export const MyComposition = () => {
  return (
    <Composition
      id="MyComp"
      component={MyComponent}
      defaultProps={DEFAULT_SHOWCASE}
      durationInFrames={300}
      fps={30}
      width={1920}
      height={1080}
      calculateMetadata={calculateMetadata}
    />
  );
};

export const MyComponent: React.FC<ShowcaseProps> = (props) => {
  const {segments} = props;
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const textRef = useRef<HTMLDivElement>(null);
  const textAreaRef = useRef<HTMLDivElement>(null);
  const [fitScale, setFitScale] = useState(1);
  let elapsedFrames = 0;
  let activeSegment = segments[segments.length - 1];
  let activeStart = 0;

  for (const segment of segments) {
    const segmentFrames = Math.round(segment.seconds * fps);
    if (frame < elapsedFrames + segmentFrames) {
      activeSegment = segment;
      activeStart = elapsedFrames;
      break;
    }
    elapsedFrames += segmentFrames;
  }

  const typedCharacters = Math.min(
    activeSegment.text.length,
    Math.floor(((frame - activeStart) / fps) * activeSegment.charactersPerSecond),
  );

  useLayoutEffect(() => {
    const text = textRef.current;
    const textArea = textAreaRef.current;
    if (!text || !textArea) return;

    const availableHeight = textArea.clientHeight * 0.92;
    const availableWidth = text.clientWidth;
    const scale = Math.min(
      1,
      availableHeight / Math.max(text.scrollHeight, 1),
      availableWidth / Math.max(text.scrollWidth, 1),
    );
    setFitScale((current) => (Math.abs(current - scale) < 0.001 ? current : scale));
  }, [activeSegment.text, activeSegment.fontSize, typedCharacters]);

  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        position: "relative",
        overflow: "hidden",
        backgroundColor: props.backgroundColor || "#111111",
      }}
    >
      <div
        ref={textAreaRef}
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: "100%",
          height: "100%",
          padding: 28,
          boxSizing: "border-box",
          color: props.textColor || "#f4f0e8",
          fontFamily,
        }}
      >
        <div
          ref={textRef}
          style={{
            width: "94%",
            fontSize: activeSegment.fontSize,
            lineHeight: 0.9,
            textAlign: "center",
            textTransform: "none",
            whiteSpace: "pre-line",
            overflowWrap: "anywhere",
            wordBreak: "break-word",
            transform: `scale(${fitScale})`,
            transformOrigin: "center center",
          }}
        >
          {activeSegment.text.slice(0, typedCharacters)}
        </div>
      </div>
    </div>
  );
};
