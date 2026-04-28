# Can Sarvam's Stack Power a WhatsApp CRM for Indian SMBs?

*Atharva Patkhedkar | April 10, 2026*

---

## The Problem

Indian manufacturing SMBs run their sales on WhatsApp. A sales rep at a pipes and bolts distributor in Ahmedabad gets 40+ messages a day in Hinglish, Gujarati, Marathi. Price enquiries, order confirmations, payment updates, complaints. Manual CRM entry takes 2 hours daily. Nobody does it. There is no order pipeline visibility.

I wanted to know if Sarvam's stack could power an agent that reads these messages and suggests CRM actions automatically.

---

## What I Built

A 3-layer pipeline:

1. **TTS (Bulbul v2)** -- synthesize voice from test messages to simulate voice notes
2. **ASR (Saarika v2.5)** -- transcribe audio back to text
3. **Intent Classification (sarvam-m)** -- classify against 9 intents covering every common SMB sales interaction: New Enquiry, Order Confirmation, Payment Update, Complaint, Delivery Follow-up, Price Negotiation, Deal Creation, New Contact, Out of Scope

I built a 20-message eval dataset across Hindi, Gujarati and Marathi. Mixed scripts: Devanagari, native Gujarati script, and Romanized (Hinglish, Gujarati-Roman, Marathi-Roman). The messages were designed to stress-test the failure modes I expected: product codes, amounts, code-switching, ambiguous confirmations.

---

## Results

Text classification accuracy: 20/20 (100%)
ASR + classification accuracy: 18/20 (90%)

The language model understands Indian SMB context well. Feed it a raw WhatsApp message in any of these languages and it correctly identifies intent with high confidence. That was a strong result and honestly better than I expected.

The ASR layer is where things got complicated.

---

## What Broke

### Product codes do not survive ASR

Input: *"Bhai, M12 anchor bolts chahiye, 500 pcs, rate batao?"*
ASR output: *"ओआईई 12 एंकर बोल्ट्स चाहे 500 रेट बेटर।"*

M12 became 12. The prefix that tells you whether it is an M12, M8, M16 or M20 was dropped. This happened in 4 of 20 messages. Every message with an alphanumeric product code had the code truncated or distorted.

For a manufacturing CRM this is a critical failure. Product codes are the primary transaction identifier. If they do not survive ASR, the CRM action is wrong regardless of intent.

### Currency amounts break in a specific way

Input: *"भाऊ, उद्या पेमेंट करतो, ₹18,000 आहे ना?"*
ASR output: *"भाव उद्या पेमेंट करतो. झिरो झिरो झिरो आहे ना?"*

18,000 became "zero zero zero." The rupee symbol combined with comma-formatted numbers completely broke Saarika's numeral handling. This appeared in both Marathi payment messages I tested.

What surprised me here: intent classification still worked. The model correctly identified it as a Payment Update even with "zero zero zero" in the transcript. But the amount field was unrecoverable. A payment update with a corrupted amount is worse than no update at all.

### Romanized text has high WER but intent still survives

Romanized Hindi messages consistently showed WER of 0.9 or higher. "Haan haan, sab theek hai" became "फैन हन सब दिखाए." The transcript is in Devanagari, the input was Roman script, token overlap is near zero.

But in 16 of 18 ASR tests, intent classification still passed despite the high WER. sarvam-m is robust enough to recover intent from a badly transcribed transcript. The one failure was a personal out-of-scope message that got classified as New Enquiry after ASR garbled it. That is a dangerous false positive: a personal message triggering a CRM action.

---

## The Metric Problem

Standard ASR evaluation measures WER. That is fine for transcription quality. It is the wrong metric for a WhatsApp CRM agent.

WER tells you how garbled the transcript is. It does not tell you whether the CRM action will be correct.

What actually needs to be measured:

**Entity-level accuracy**
- Product code preservation: does M12 come out as M12?
- Amount extraction: does 18,000 come out as 18000?
- Unit preservation: does "500 pcs" survive as a discrete quantity?

**Intent accuracy under ASR degradation**
- Text-only intent accuracy as the ceiling
- ASR + intent accuracy as the production number
- The delta between the two is the ASR degradation cost

**False positive rate on high-stakes intents**
- Order Confirmation and Payment Update have the highest cost if misclassified
- These need to be tracked separately, not averaged into overall accuracy

**Cross-script robustness**
- Native script ASR significantly outperformed Romanized input
- Gujarati native script WER: 0.14. Devanagari WER: 0.17. All Romanized: 0.9+
- The pipeline should encourage native script input where possible

---

## Honest Assessment

Sarvam's language model understands India's B2B sales context better than I expected. The intent taxonomy held up completely in text. That is the hard part and it is largely solved.

The ASR failures are specific and fixable. They are not random noise. Alphanumeric entities, currency formatting, Romanized input: these are structural failure modes you can build targeted eval suites around and measure systematically.

For a WhatsApp CRM to work in production, entity preservation matters as much as intent accuracy. The difference between "intent is correct" and "amount is correct" is the difference between a useful CRM update and a corrupted one.

---
