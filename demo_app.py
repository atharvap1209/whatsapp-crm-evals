"""
WhatsApp CRM AI Demo
--------------------
Interactive demo: paste or pick a WhatsApp message,
see how the AI classifies intent and fills a CRM entry.

Usage:
    pip install flask requests python-dotenv
    python demo_app.py
    Open http://localhost:5000
"""

import json
import os

import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template_string, request

from test_messages import INTENT_TAXONOMY, TEST_MESSAGES

load_dotenv()
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY", "")

app = Flask(__name__)

# --------------------------------------------------------------------------- #
# Prompt
# --------------------------------------------------------------------------- #

DEMO_PROMPT = """You are an AI assistant for Indian manufacturing/trading SMBs. Extract CRM data from a WhatsApp message sent to sales rep Arvind.

Intent taxonomy:
I-01: New Contact — Unknown number, first business message
I-02: New Enquiry — Known contact asking about product or price
I-03: Deal Creation — Known contact signaling a NEW distinct opportunity
I-04: Price Negotiation — Known contact, price discussion on open deal
I-05: Order Confirmation — Known contact confirming intent to order
I-06: Payment Update — Payment status or commitment timeline
I-07: Delivery Follow-up — Asking about delivery or order status
I-08: Complaint — Problem with an existing order
I-09: Out of Scope — Personal, greeting-only, spam, unrelated

Classification rules:
- Conditional confirmation ("confirm hai but discount chahiye") → I-04, NOT I-05
- Mild delivery question without dissatisfaction → I-07, NOT I-08
- Single greeting with no commercial content → always I-09
- I-03 needs an explicit signal of a NEW opportunity from a known contact

Message: {message}

Return ONLY valid JSON — no markdown, no extra text:
{{
  "intent": "I-XX",
  "intent_label": "label from taxonomy above",
  "confidence": "high/medium/low",
  "reasoning": "one concise sentence explaining the classification",
  "crm_entry": {{
    "suggested_action": "short action label e.g. Log Enquiry / Create Deal / Confirm Order / Log Payment / File Complaint / No Action",
    "product": "product name and specs, or null",
    "quantity": "quantity with unit, or null",
    "amount": "amount with currency symbol, or null",
    "timeline": "any date, deadline, or timeframe mentioned, or null",
    "key_note": "the single most important thing Arvind needs to act on"
  }},
  "missed": ["CRM fields absent from this message that would normally be captured"]
}}"""

# --------------------------------------------------------------------------- #
# Sarvam helper
# --------------------------------------------------------------------------- #

def analyze_message(text: str) -> dict:
    if not SARVAM_API_KEY:
        return {"error": "SARVAM_API_KEY not set. Add it to your .env file."}

    resp = requests.post(
        "https://api.sarvam.ai/v1/chat/completions",
        headers={
            "api-subscription-key": SARVAM_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "model": "sarvam-m",
            "messages": [{"role": "user", "content": DEMO_PROMPT.format(message=text)}],
            "temperature": 0.1,
        },
        timeout=20,
    )

    if resp.status_code != 200:
        return {"error": f"API error {resp.status_code}: {resp.text[:200]}"}

    content = resp.json()["choices"][0]["message"]["content"]
    try:
        start = content.find("{")
        end = content.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(content[start:end])
    except Exception:
        pass
    return {"error": f"Could not parse model response: {content[:200]}"}


# --------------------------------------------------------------------------- #
# HTML template
# --------------------------------------------------------------------------- #

LANG_DISPLAY = {"hi-IN": "Hindi", "gu-IN": "Gujarati", "mr-IN": "Marathi"}

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>WhatsApp CRM AI — Sarvam Demo</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f0f2f5;
    color: #1a1a2e;
    min-height: 100vh;
  }

  /* ---- Header ---- */
  header {
    background: linear-gradient(135deg, #075E54 0%, #128C7E 100%);
    color: #fff;
    padding: 18px 32px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,0,0,.2);
  }
  header h1 { font-size: 1.25rem; font-weight: 700; letter-spacing: -.3px; }
  header h1 span { opacity: .75; font-weight: 400; }
  .badge-sarvam {
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.3);
    border-radius: 20px;
    padding: 4px 12px;
    font-size: .75rem;
    letter-spacing: .5px;
    text-transform: uppercase;
  }

  /* ---- Layout ---- */
  main {
    max-width: 1080px;
    margin: 32px auto;
    padding: 0 20px;
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 24px;
    align-items: start;
  }
  @media (max-width: 720px) { main { grid-template-columns: 1fr; } }

  /* ---- Card base ---- */
  .card {
    background: #fff;
    border-radius: 16px;
    box-shadow: 0 2px 12px rgba(0,0,0,.08);
    padding: 24px;
  }
  .card-title {
    font-size: .7rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 14px;
  }

  /* ---- Input panel ---- */
  textarea {
    width: 100%;
    border: 1.5px solid #e0e0e0;
    border-radius: 12px;
    padding: 14px 16px;
    font-size: .95rem;
    font-family: inherit;
    resize: vertical;
    min-height: 100px;
    transition: border-color .2s;
    color: #1a1a2e;
    background: #fafafa;
    line-height: 1.5;
  }
  textarea:focus { outline: none; border-color: #25D366; background: #fff; }

  .preset-label {
    font-size: .75rem;
    color: #888;
    margin: 16px 0 8px;
    font-weight: 600;
    letter-spacing: .5px;
    text-transform: uppercase;
  }
  .preset-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 340px;
    overflow-y: auto;
    padding-right: 4px;
  }
  .preset-list::-webkit-scrollbar { width: 4px; }
  .preset-list::-webkit-scrollbar-track { background: #f5f5f5; border-radius: 4px; }
  .preset-list::-webkit-scrollbar-thumb { background: #d0d0d0; border-radius: 4px; }

  .preset-chip {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1.5px solid #efefef;
    background: #fafafa;
    cursor: pointer;
    text-align: left;
    transition: all .15s;
    font-family: inherit;
  }
  .preset-chip:hover { border-color: #25D366; background: #f0fff4; }
  .preset-chip.active { border-color: #25D366; background: #e8fdf0; }

  .chip-meta { flex-shrink: 0; }
  .chip-id {
    font-size: .65rem;
    font-weight: 700;
    color: #555;
    background: #ebebeb;
    border-radius: 4px;
    padding: 1px 5px;
    display: block;
    margin-bottom: 4px;
    text-align: center;
  }
  .chip-lang {
    font-size: .6rem;
    color: #888;
    text-align: center;
    display: block;
  }
  .chip-text {
    font-size: .82rem;
    color: #333;
    line-height: 1.45;
    flex: 1;
  }
  .chip-intent {
    font-size: .65rem;
    padding: 2px 7px;
    border-radius: 20px;
    font-weight: 600;
    flex-shrink: 0;
    align-self: center;
  }

  .btn-analyze {
    margin-top: 16px;
    width: 100%;
    padding: 13px;
    background: #25D366;
    color: #fff;
    border: none;
    border-radius: 12px;
    font-size: 1rem;
    font-weight: 700;
    cursor: pointer;
    transition: background .2s, transform .1s;
    letter-spacing: .3px;
  }
  .btn-analyze:hover { background: #1ebe5d; }
  .btn-analyze:active { transform: scale(.98); }
  .btn-analyze:disabled { background: #a5d6b4; cursor: not-allowed; }

  /* ---- Results panel ---- */
  #results { display: none; }
  #results.show { display: block; }

  .intent-block {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    flex-wrap: wrap;
  }
  .intent-badge {
    font-size: 1rem;
    font-weight: 800;
    padding: 8px 18px;
    border-radius: 30px;
    letter-spacing: -.2px;
  }
  .confidence-badge {
    font-size: .7rem;
    font-weight: 700;
    padding: 4px 10px;
    border-radius: 20px;
    text-transform: uppercase;
    letter-spacing: .5px;
  }
  .conf-high { background: #d1fae5; color: #065f46; }
  .conf-medium { background: #fef3c7; color: #92400e; }
  .conf-low { background: #fee2e2; color: #991b1b; }

  .reasoning-text {
    font-size: .88rem;
    color: #555;
    line-height: 1.6;
    margin-bottom: 20px;
    padding: 12px 14px;
    background: #f8f9fa;
    border-left: 3px solid #25D366;
    border-radius: 0 8px 8px 0;
  }

  .section-title {
    font-size: .68rem;
    font-weight: 700;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #888;
    margin-bottom: 10px;
  }

  .crm-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    margin-bottom: 20px;
  }
  .crm-field {
    background: #f8f9fa;
    border-radius: 10px;
    padding: 10px 12px;
  }
  .crm-field.full { grid-column: 1 / -1; }
  .crm-field label {
    display: block;
    font-size: .65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .8px;
    color: #999;
    margin-bottom: 3px;
  }
  .crm-field .value {
    font-size: .88rem;
    color: #1a1a2e;
    font-weight: 500;
  }
  .crm-field .value.null-val { color: #bbb; font-style: italic; font-weight: 400; }
  .crm-action-value {
    font-weight: 700;
    color: #075E54;
    font-size: .95rem;
  }

  .missed-list {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
  }
  .missed-chip {
    font-size: .78rem;
    padding: 5px 11px;
    border-radius: 20px;
    background: #fff8e1;
    border: 1px solid #ffd54f;
    color: #7c5800;
    font-weight: 500;
  }
  .no-missed {
    font-size: .85rem;
    color: #22c55e;
    font-weight: 600;
  }

  /* ---- Loading ---- */
  #loading { display: none; text-align: center; padding: 40px 20px; }
  #loading.show { display: block; }
  .spinner {
    width: 36px; height: 36px;
    border: 3px solid #e0e0e0;
    border-top-color: #25D366;
    border-radius: 50%;
    animation: spin .7s linear infinite;
    margin: 0 auto 12px;
  }
  @keyframes spin { to { transform: rotate(360deg); } }
  #loading p { color: #888; font-size: .88rem; }

  #error-msg {
    display: none;
    background: #fee2e2;
    border: 1px solid #fca5a5;
    border-radius: 10px;
    padding: 12px 16px;
    color: #991b1b;
    font-size: .88rem;
    margin-bottom: 16px;
  }

  /* ---- Intent color map ---- */
  .i-01 { background: #dbeafe; color: #1e3a8a; }
  .i-02 { background: #ccfbf1; color: #134e4a; }
  .i-03 { background: #ede9fe; color: #3b0764; }
  .i-04 { background: #ffedd5; color: #7c2d12; }
  .i-05 { background: #dcfce7; color: #14532d; }
  .i-06 { background: #d1fae5; color: #064e3b; }
  .i-07 { background: #e0f2fe; color: #0c4a6e; }
  .i-08 { background: #fee2e2; color: #7f1d1d; }
  .i-09 { background: #f1f5f9; color: #475569; }
</style>
</head>
<body>

<header>
  <h1>WhatsApp → CRM <span>/ AI Demo</span></h1>
  <span class="badge-sarvam">Powered by Sarvam</span>
</header>

<main>
  <!-- LEFT: Input -->
  <div class="card">
    <div class="card-title">WhatsApp Message</div>
    <textarea id="msgInput" rows="4"
      placeholder="Type a message in Hindi, Gujarati, or Marathi… or pick one below"></textarea>

    <div class="preset-label">Dataset samples (click to load)</div>
    <div class="preset-list" id="presetList"></div>

    <button class="btn-analyze" id="analyzeBtn" onclick="analyze()">Analyze Message</button>
  </div>

  <!-- RIGHT: Results -->
  <div class="card">
    <div class="card-title">AI Analysis</div>

    <div id="error-msg"></div>
    <div id="loading"><div class="spinner"></div><p>Calling Sarvam AI…</p></div>

    <div id="results">
      <div class="intent-block">
        <span class="intent-badge" id="intentBadge"></span>
        <span class="confidence-badge" id="confBadge"></span>
      </div>
      <div class="reasoning-text" id="reasoningText"></div>

      <div class="section-title">CRM Entry</div>
      <div class="crm-grid">
        <div class="crm-field full">
          <label>Suggested Action</label>
          <div class="value crm-action-value" id="crmAction"></div>
        </div>
        <div class="crm-field">
          <label>Product</label>
          <div class="value" id="crmProduct"></div>
        </div>
        <div class="crm-field">
          <label>Quantity</label>
          <div class="value" id="crmQty"></div>
        </div>
        <div class="crm-field">
          <label>Amount</label>
          <div class="value" id="crmAmount"></div>
        </div>
        <div class="crm-field">
          <label>Timeline</label>
          <div class="value" id="crmTimeline"></div>
        </div>
        <div class="crm-field full">
          <label>Key Note</label>
          <div class="value" id="crmNote"></div>
        </div>
      </div>

      <div class="section-title">What's Missing</div>
      <div id="missedContainer"></div>
    </div>
  </div>
</main>

<script>
const MESSAGES = {{ messages|tojson }};
const COLORS = {
  "I-01":"i-01","I-02":"i-02","I-03":"i-03","I-04":"i-04","I-05":"i-05",
  "I-06":"i-06","I-07":"i-07","I-08":"i-08","I-09":"i-09"
};

// Build preset chips
const list = document.getElementById("presetList");
MESSAGES.forEach(m => {
  const btn = document.createElement("button");
  btn.className = "preset-chip";
  btn.dataset.text = m.text;
  btn.innerHTML = `
    <span class="chip-meta">
      <span class="chip-id">${m.id}</span>
      <span class="chip-lang">${m.lang}</span>
    </span>
    <span class="chip-text">${m.text}</span>
    <span class="chip-intent intent-badge ${COLORS[m.intent] || ''}"
      style="font-size:.62rem;padding:3px 8px;">${m.intent}</span>
  `;
  btn.onclick = () => {
    document.querySelectorAll(".preset-chip").forEach(c => c.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById("msgInput").value = m.text;
  };
  list.appendChild(btn);
});

function setVal(id, val) {
  const el = document.getElementById(id);
  if (val) {
    el.textContent = val;
    el.classList.remove("null-val");
  } else {
    el.textContent = "—";
    el.classList.add("null-val");
  }
}

async function analyze() {
  const text = document.getElementById("msgInput").value.trim();
  if (!text) { document.getElementById("msgInput").focus(); return; }

  const btn = document.getElementById("analyzeBtn");
  const loading = document.getElementById("loading");
  const results = document.getElementById("results");
  const errMsg = document.getElementById("error-msg");

  btn.disabled = true;
  loading.classList.add("show");
  results.classList.remove("show");
  errMsg.style.display = "none";

  try {
    const resp = await fetch("/analyze", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message: text})
    });
    const data = await resp.json();

    loading.classList.remove("show");

    if (data.error) {
      errMsg.textContent = data.error;
      errMsg.style.display = "block";
      return;
    }

    // Intent badge
    const badge = document.getElementById("intentBadge");
    badge.textContent = `${data.intent} · ${data.intent_label}`;
    badge.className = `intent-badge ${COLORS[data.intent] || ""}`;

    // Confidence
    const conf = document.getElementById("confBadge");
    conf.textContent = data.confidence;
    conf.className = `confidence-badge conf-${data.confidence}`;

    // Reasoning
    document.getElementById("reasoningText").textContent = data.reasoning;

    // CRM fields
    const crm = data.crm_entry || {};
    setVal("crmAction", crm.suggested_action);
    setVal("crmProduct", crm.product);
    setVal("crmQty", crm.quantity);
    setVal("crmAmount", crm.amount);
    setVal("crmTimeline", crm.timeline);
    setVal("crmNote", crm.key_note);

    // Missed fields
    const container = document.getElementById("missedContainer");
    const missed = data.missed || [];
    if (missed.length === 0) {
      container.innerHTML = `<p class="no-missed">All key CRM fields captured.</p>`;
    } else {
      container.innerHTML = missed
        .map(m => `<span class="missed-chip">${m}</span>`)
        .join("");
      container.className = "missed-list";
    }

    results.classList.add("show");
  } catch (e) {
    loading.classList.remove("show");
    errMsg.textContent = "Network error: " + e.message;
    errMsg.style.display = "block";
  } finally {
    btn.disabled = false;
  }
}

// Allow Enter key in textarea (Shift+Enter = newline)
document.getElementById("msgInput").addEventListener("keydown", e => {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); analyze(); }
});
</script>
</body>
</html>"""


# --------------------------------------------------------------------------- #
# Routes
# --------------------------------------------------------------------------- #

@app.route("/")
def index():
    messages = [
        {
            "id": m["id"],
            "text": m["text"],
            "lang": LANG_DISPLAY.get(m["language"], m["language"]),
            "intent": m["expected_intent"],
        }
        for m in TEST_MESSAGES
    ]
    return render_template_string(HTML, messages=messages)


@app.route("/analyze", methods=["POST"])
def analyze():
    body = request.get_json(force=True)
    text = (body.get("message") or "").strip()
    if not text:
        return jsonify({"error": "Empty message"}), 400
    result = analyze_message(text)
    return jsonify(result)


if __name__ == "__main__":
    if not SARVAM_API_KEY:
        print("WARNING: SARVAM_API_KEY not found. Add it to your .env file.")
    print("Starting WhatsApp CRM AI Demo...")
    print("Open http://localhost:5000")
    app.run(debug=False, port=5000)
