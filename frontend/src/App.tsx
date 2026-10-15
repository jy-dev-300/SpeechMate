import { useRef, useState } from "react";
import { submitAttempt } from "./api";
import type { AttemptResult } from "./types";

const DEFAULT_PHRASE = "I really like working remotely.";

export default function App() {
  const [expectedText, setExpectedText] = useState(DEFAULT_PHRASE);
  const [observedText, setObservedText] = useState("I really like working remotely.");
  const [recording, setRecording] = useState(false);
  const [audio, setAudio] = useState<Blob | null>(null);
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const recorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);

  async function toggleRecording() {
    if (recording) {
      recorderRef.current?.stop();
      return;
    }
    try {
      // Microphone access begins only after the learner presses the record button.
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      chunksRef.current = [];
      recorder.ondataavailable = (event) => chunksRef.current.push(event.data);
      recorder.onstop = () => {
        setAudio(new Blob(chunksRef.current, { type: recorder.mimeType }));
        stream.getTracks().forEach((track) => track.stop());
        setRecording(false);
      };
      recorderRef.current = recorder;
      recorder.start();
      setRecording(true);
      setError(null);
    } catch {
      setError("Microphone access was unavailable. You can still run the text-backed demo.");
    }
  }

  async function analyze() {
    setLoading(true);
    setError(null);
    try {
      setResult(await submitAttempt({ expectedText, observedText, audio }));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const strongestWeakness = result?.learner_profile[0];

  return (
    <main>
      <nav aria-label="Primary navigation">
        <a className="brand" href="#top" aria-label="SpeechMate home">
          <span className="brandMark">s</span> speechmate
        </a>
        <span className="sessionPill">Practice session</span>
      </nav>

      <section className="hero" id="top">
        <div className="eyebrow"><span /> Today’s focus · clear consonants</div>
        <h1>Say it with<br /><em>confidence.</em></h1>
        <p>One thoughtful phrase at a time. SpeechMate remembers the sounds worth practicing.</p>
      </section>

      <section className="practiceGrid" aria-label="Pronunciation practice">
        <article className="practiceCard">
          <div className="cardHeader">
            <span className="step">01</span>
            <div><small>Your phrase</small><h2>Read this aloud</h2></div>
          </div>
          <textarea
            aria-label="Practice phrase"
            value={expectedText}
            onChange={(event) => setExpectedText(event.target.value)}
          />
          <div className="phraseMeta"><span>EN · Everyday speech</span><span>{expectedText.split(/\s+/).length} words</span></div>
        </article>

        <article className={`recordCard ${recording ? "isRecording" : ""}`}>
          <span className="step light">02</span>
          <button className="recordButton" onClick={toggleRecording} aria-pressed={recording}>
            <span className="micIcon">{recording ? "■" : "●"}</span>
            <strong>{recording ? "Finish recording" : audio ? "Record again" : "Start recording"}</strong>
            <small>{recording ? "We’re listening…" : audio ? "Recording ready" : "Tap when you’re ready"}</small>
          </button>
          <div className="wave" aria-hidden="true">
            {[18, 30, 22, 44, 31, 54, 38, 24, 46, 28, 18, 35, 20].map((height, index) => (
              <i key={index} style={{ height }} />
            ))}
          </div>
        </article>
      </section>

      <section className="analysisPanel">
        <div>
          <label htmlFor="observed">Offline demo transcript</label>
          <input id="observed" value={observedText} onChange={(event) => setObservedText(event.target.value)} />
          <small>Change “really” to “leally” to simulate an /r/ → /l/ recognition.</small>
        </div>
        <button className="analyzeButton" onClick={analyze} disabled={loading || !expectedText.trim()}>
          {loading ? "Listening closely…" : "Analyze my speech"}<span>→</span>
        </button>
      </section>

      {error && <p className="error" role="alert">{error}</p>}

      {result && (
        <section className="results" aria-live="polite">
          <div className="resultIntro">
            <span className="eyebrow"><span /> Your feedback</span>
            <h2>{result.observations.length ? "A few sounds to shape." : "Nicely matched."}</h2>
            <p>We heard “{result.transcript}” using {result.asr_provider}.</p>
          </div>
          <div className="feedbackList">
            {result.observations.length === 0 && <div className="feedback good">No confident mismatches were detected.</div>}
            {result.observations.map((item, index) => (
              <div className="feedback" key={`${item.word}-${index}`}>
                <span className="phoneme">/{item.expected_symbol ?? item.observed_symbol}/</span>
                <div><strong>{item.word}</strong><p>{item.explanation}</p></div>
                <span className="confidence">{Math.round(item.confidence * 100)}%</span>
              </div>
            ))}
          </div>
          {strongestWeakness && (
            <aside className="coachNote">
              <small>Practice memory</small>
              <p>{strongestWeakness.recommended_prompt}</p>
              <span>{strongestWeakness.distinct_sessions} sessions · {strongestWeakness.error_count} signals</span>
            </aside>
          )}
        </section>
      )}

      <footer><span>SpeechMate</span><p>Private by design · Audio is used only for your analysis.</p></footer>
    </main>
  );
}
