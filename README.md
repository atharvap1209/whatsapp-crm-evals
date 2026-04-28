# Sarvam SMB CRM Eval

**Can Sarvam's stack power a WhatsApp CRM for Indian manufacturing SMBs?**

This is a PM-driven eval, not a benchmark. It tests Sarvam's ASR (Saarika) and LLM (sarvam-m) against a real product problem: classifying Indian SMB WhatsApp messages into CRM intents, across Hindi, Gujarati, and Marathi.

---

## Background

Indian manufacturing SMBs run their sales on WhatsApp. A sales rep receives 40+ messages a day in Hinglish, Gujarati, Marathi -- price enquiries, order confirmations, payment updates, complaints. Manual CRM entry takes 2 hours daily. Nobody does it.

The product concept: an AI agent connected to WhatsApp that reads these messages and suggests CRM actions automatically. The eval tests whether Sarvam's stack can power it.

The intent taxonomy (9 intents) was designed before model selection. The model is evaluated against real SMB sales interactions, not generic sentiment labels.

---

## What This Eval Tests

3-layer pipeline:

```
Voice note (simulated via Bulbul TTS)
        ↓
Saarika v2.5 (ASR) → transcript
        ↓
sarvam-m (LLM) → intent classification
```

Separately, raw text messages are also classified directly to establish a ceiling.

**20 test messages** across:
- Hindi / Hinglish (Roman + Devanagari)
- Gujarati (native script + Roman)
- Marathi (Roman + Devanagari)

**9 intents:** New Contact, New Enquiry, Deal Creation, Price Negotiation, Order Confirmation, Payment Update, Delivery Follow-up, Complaint, Out of Scope

---

## Results (Summary)

| Layer | Accuracy |
|-------|----------|
| Text classification (sarvam-m) | 20/20 (100%) |
| ASR + classification (Saarika + sarvam-m) | 18/20 (90%) |

**3 structural failure modes found:**
1. Product code truncation -- M12 becomes 12, every time
2. Currency formatting hallucination -- ₹18,000 becomes "zero zero zero"
3. High WER on Romanized input (0.9+), but intent mostly survives

Full findings in `findings/sarvam-smb-eval.md`

---

## Setup

### Requirements

- Python 3.9+
- Sarvam API key (get one at [sarvam.ai](https://sarvam.ai))

### Install dependencies

```bash
pip install -r requirements.txt
```

### Set your API key

```bash
cp .env.example .env
# Edit .env and add your Sarvam API key
```

Or export directly:

```bash
export SARVAM_API_KEY=your_key_here
```

---

## Running the Eval

```bash
python eval_runner.py
```

This will:
1. Classify all 20 test messages via raw text (sarvam-m)
2. Generate TTS audio for each message (Bulbul v2)
3. Transcribe audio back to text (Saarika v2.5)
4. Classify the transcripts (sarvam-m)
5. Log pass/fail, WER, and failure modes
6. Save results to `results/eval_results.json`

Runtime: ~5-8 minutes (API calls per message).

---

## File Structure

```
sarvam-smb-eval/
├── README.md
├── requirements.txt
├── .env.example
├── eval_runner.py          # Main eval script
├── test_messages.py        # 20-message dataset + intent taxonomy
├── findings/
│   ├── sarvam-smb-eval.md  # Written findings (post as-is)
│   └── sarvam-smb-eval.xlsx # Results spreadsheet
└── results/
    └── eval_results.json   # Generated on run
```

---

## Extending the Eval

**Add more test messages** in `test_messages.py` -- follow the same dict structure. Adding Tamil (ta-IN) and Telugu (te-IN) is a natural next step.

**Change the intent taxonomy** by editing `INTENT_TAXONOMY` and `CLASSIFICATION_PROMPT` in `eval_runner.py`.

**Add entity extraction metrics** -- the most important next step. Current WER is a poor proxy for CRM accuracy. What matters is whether product codes and amounts survive ASR intact.

---

## Notes on Methodology

The WER computation here is approximate (token overlap, not full dynamic programming edit distance). It is used to flag degradation, not as a primary metric. The primary metrics are intent accuracy at text level and intent accuracy post-ASR.

This eval uses TTS-generated audio as a proxy for real voice notes. Real WhatsApp voice notes will have background noise, faster speech, and more code-switching -- expect ASR performance to be lower in production.

---

*Built April 2026. Models: Saarika v2.5, Bulbul v2, sarvam-m.*
