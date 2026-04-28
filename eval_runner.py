"""
Sarvam SMB CRM Eval Runner
--------------------------
Tests Sarvam's ASR (Saarika v2.5) + LLM (sarvam-m) on a 9-intent classification
task built around a real Indian SMB WhatsApp CRM product concept.

Usage:
    python eval_runner.py

Requires SARVAM_API_KEY in .env or environment.
"""

import os
import json
import base64
import time
import requests
from dotenv import load_dotenv
from test_messages import TEST_MESSAGES, INTENT_TAXONOMY

load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

if not SARVAM_API_KEY:
    raise ValueError("SARVAM_API_KEY not set. Copy .env.example to .env and add your key.")

HEADERS = {
    "api-subscription-key": SARVAM_API_KEY,
    "Content-Type": "application/json"
}

CLASSIFICATION_PROMPT = """You are classifying WhatsApp messages sent to an Indian manufacturing/trading SMB sales rep named Arvind.

Classify the message into EXACTLY ONE of these intents:

I-01: New Contact - Unknown number sending a business message
I-02: New Enquiry - Known contact asking about product or price
I-03: Deal Creation - Known contact signaling a NEW opportunity distinct from existing open deals
I-04: Price Negotiation - Known contact discussing price on an open deal
I-05: Order Confirmation - Known contact confirming intent to proceed / place order
I-06: Payment Update - Sharing payment status or commitment timeline
I-07: Delivery Follow-up - Asking about delivery or order status
I-08: Complaint - Reporting a problem with an existing order
I-09: Out of Scope - Personal message, greeting only, spam, unrelated to business

Classification rules:
- A conditional confirmation ("confirm hai but discount chahiye") is I-04, not I-05
- A mild delivery question without dissatisfaction is I-07, not I-08
- Single word greetings with no commercial content are always I-09
- I-03 requires a signal of a NEW, distinct opportunity from a known contact (not just another enquiry)

Message: {message}

Respond in this exact JSON format with no extra text:
{{"intent": "I-XX", "confidence": "high/medium/low", "reasoning": "one sentence"}}"""


# -------------------------
# API helpers
# -------------------------

def classify_intent(text: str) -> dict:
    response = requests.post(
        "https://api.sarvam.ai/v1/chat/completions",
        headers=HEADERS,
        json={
            "model": "sarvam-m",
            "messages": [{"role": "user", "content": CLASSIFICATION_PROMPT.format(message=text)}],
            "temperature": 0.1
        }
    )
    if response.status_code != 200:
        return {"intent": "ERROR", "confidence": "none", "reasoning": response.text[:200]}

    content = response.json()["choices"][0]["message"]["content"]
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return {"intent": "PARSE_ERROR", "confidence": "none", "reasoning": content[:200]}


def text_to_speech(text: str, language_code: str) -> bytes | None:
    response = requests.post(
        "https://api.sarvam.ai/text-to-speech",
        headers=HEADERS,
        json={
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": "anushka",
            "model": "bulbul:v2"
        }
    )
    if response.status_code != 200:
        print(f"    TTS error: {response.text[:150]}")
        return None
    data = response.json()
    if "audios" in data:
        return base64.b64decode(data["audios"][0])
    return None


def speech_to_text(audio_bytes: bytes, language_code: str) -> str | None:
    response = requests.post(
        "https://api.sarvam.ai/speech-to-text",
        headers={"api-subscription-key": SARVAM_API_KEY},
        files={"file": ("audio.wav", audio_bytes, "audio/wav")},
        data={"model": "saarika:v2.5", "language_code": language_code}
    )
    if response.status_code != 200:
        print(f"    ASR error: {response.text[:150]}")
        return None
    return response.json().get("transcript")


def approx_wer(reference: str, hypothesis: str) -> float:
    """
    Approximate WER using token overlap.
    Note: this is a rough proxy -- not full edit-distance WER.
    It is used to flag degradation, not as a primary metric.
    """
    ref_words = set(reference.lower().split())
    hyp_words = set(hypothesis.lower().split())
    if not ref_words:
        return 0.0
    matched = len(ref_words & hyp_words)
    return round(1.0 - matched / len(ref_words), 2)


# -------------------------
# Core eval loop
# -------------------------

def run_eval() -> list:
    results = []

    print("=" * 70)
    print("SARVAM SMB CRM EVAL")
    print("20 messages | hi-IN, gu-IN, mr-IN | 9-intent taxonomy")
    print("Models: Saarika v2.5 (ASR), Bulbul v2 (TTS), sarvam-m (LLM)")
    print("=" * 70)

    product_code_tokens = ["M12", "M16", "M8", "M20", "GI", "1 inch", "2 inch"]

    for msg in TEST_MESSAGES:
        print(f"\n[{msg['id']}] {msg['intent_label']} | {msg['language']} | {msg['script']}")
        print(f"  Text: {msg['text'][:80]}")

        result = {
            "id": msg["id"],
            "language": msg["language"],
            "script": msg["script"],
            "expected_intent": msg["expected_intent"],
            "expected_label": msg["intent_label"],
            "original_text": msg["text"],
            "notes": msg["notes"],
            "asr_transcript": None,
            "asr_wer": None,
            "text_classification": None,
            "asr_classification": None,
            "text_correct": None,
            "asr_correct": None,
            "failure_modes": []
        }

        # Step 1: Classify raw text
        print("  [1/3] Classifying raw text...")
        text_clf = classify_intent(msg["text"])
        result["text_classification"] = text_clf
        result["text_correct"] = text_clf.get("intent") == msg["expected_intent"]
        status = "PASS" if result["text_correct"] else "FAIL"
        print(f"  Text: {text_clf.get('intent')} ({text_clf.get('confidence')}) [{status}]")
        print(f"    Reason: {text_clf.get('reasoning', '')[:100]}")

        if not result["text_correct"]:
            result["failure_modes"].append(
                f"TEXT_MISCLASSIFICATION: got {text_clf.get('intent')}, expected {msg['expected_intent']}"
            )

        # Step 2: TTS
        print("  [2/3] Generating TTS audio...")
        audio = text_to_speech(msg["text"], msg["language"])

        if not audio:
            result["failure_modes"].append("TTS_FAILED")
            results.append(result)
            time.sleep(0.5)
            continue

        # Step 3: ASR
        print("  [3/3] Transcribing with Saarika...")
        transcript = speech_to_text(audio, msg["language"])

        if not transcript:
            result["failure_modes"].append("ASR_FAILED")
            results.append(result)
            time.sleep(0.5)
            continue

        result["asr_transcript"] = transcript
        result["asr_wer"] = approx_wer(msg["text"], transcript)
        print(f"  ASR: {transcript[:100]}")
        print(f"  WER (approx): {result['asr_wer']}")

        # Classify transcript
        asr_clf = classify_intent(transcript)
        result["asr_classification"] = asr_clf
        result["asr_correct"] = asr_clf.get("intent") == msg["expected_intent"]
        asr_status = "PASS" if result["asr_correct"] else "FAIL"
        print(f"  ASR intent: {asr_clf.get('intent')} ({asr_clf.get('confidence')}) [{asr_status}]")

        # Failure mode detection
        if result["asr_wer"] and result["asr_wer"] > 0.4:
            result["failure_modes"].append(f"HIGH_WER: {result['asr_wer']}")

        if result["text_correct"] and not result["asr_correct"]:
            result["failure_modes"].append(
                f"ASR_DEGRADATION: text correct but ASR misclassified as {asr_clf.get('intent')}"
            )

        # Check product code survival
        has_product_code = any(code in msg["text"] for code in product_code_tokens)
        if has_product_code:
            code_survived = any(code in transcript for code in product_code_tokens)
            if not code_survived:
                result["failure_modes"].append("PRODUCT_CODE_LOSS: product code dropped or distorted in ASR")

        if result["failure_modes"]:
            print(f"  Failures: {result['failure_modes']}")

        results.append(result)
        time.sleep(0.5)

    return results


# -------------------------
# Summary + output
# -------------------------

def print_summary(results: list):
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total = len(results)
    text_pass = sum(1 for r in results if r["text_correct"])
    asr_tested = [r for r in results if r["asr_correct"] is not None]
    asr_pass = sum(1 for r in asr_tested if r["asr_correct"])

    print(f"\nText Classification Accuracy : {text_pass}/{total} ({round(100*text_pass/total)}%)")
    if asr_tested:
        print(f"ASR + Classification Accuracy: {asr_pass}/{len(asr_tested)} ({round(100*asr_pass/len(asr_tested))}%)")
        print(f"ASR Degradation Cost         : {text_pass - asr_pass} additional failure(s)")

    print("\nBy language (text classification):")
    for lang in ["hi-IN", "gu-IN", "mr-IN"]:
        lang_r = [r for r in results if r["language"] == lang]
        lang_pass = sum(1 for r in lang_r if r["text_correct"])
        print(f"  {lang}: {lang_pass}/{len(lang_r)}")

    fm_counts: dict[str, int] = {}
    for r in results:
        for fm in r["failure_modes"]:
            key = fm.split(":")[0]
            fm_counts[key] = fm_counts.get(key, 0) + 1

    if fm_counts:
        print("\nFailure mode counts:")
        for fm, count in sorted(fm_counts.items(), key=lambda x: -x[1]):
            print(f"  {fm}: {count}")

    misclassified = [r for r in results if not r["text_correct"]]
    if misclassified:
        print("\nText misclassifications:")
        for r in misclassified:
            clf = r["text_classification"]
            print(f"  [{r['id']}] Expected {r['expected_intent']}, Got {clf.get('intent')}")
            print(f"    Text: {r['original_text'][:80]}")

    asr_degraded = [r for r in results if r["text_correct"] and r["asr_correct"] is False]
    if asr_degraded:
        print("\nASR degradation failures (text passed, ASR failed):")
        for r in asr_degraded:
            print(f"  [{r['id']}] {r['original_text'][:60]}")
            print(f"    ASR: {r.get('asr_transcript', '')[:60]}")


def save_results(results: list):
    os.makedirs("results", exist_ok=True)
    output = {
        "eval_meta": {
            "total_messages": len(results),
            "languages": ["hi-IN", "gu-IN", "mr-IN"],
            "intents_tested": list(INTENT_TAXONOMY.keys()),
            "models": {
                "asr": "saarika:v2.5",
                "tts": "bulbul:v2",
                "llm": "sarvam-m"
            }
        },
        "results": results
    }
    path = "results/eval_results.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\nResults saved to {path}")


if __name__ == "__main__":
    results = run_eval()
    print_summary(results)
    save_results(results)
