import { useEffect, useState } from "react";
import { researchMessages } from "../lib/loadingMessages";

export default function ProcessingState({ onCancel }) {
  const [index, setIndex] = useState(() =>
    Math.floor(Math.random() * researchMessages.length),
  );
  useEffect(() => {
    const timer = setInterval(
      () => setIndex((value) => (value + 1) % researchMessages.length),
      4200,
    );
    return () => clearInterval(timer);
  }, []);
  return (
    <div className="processing-state" role="status">
      <div className="scan-document" aria-hidden="true">
        <span />
        <span />
        <span />
        <span />
        <div className="scan-beam" />
      </div>
      <div>
        <div className="eyebrow">RESEARCH IN PROGRESS</div>
        <h3>{researchMessages[index]}</h3>
        <p>Retrieving source records and preparing a response.</p>
        <button onClick={onCancel} className="text-button">
          Cancel request
        </button>
      </div>
    </div>
  );
}
