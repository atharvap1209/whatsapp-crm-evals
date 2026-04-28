"""
Test dataset: 20 SMB WhatsApp messages across Hindi, Gujarati, Marathi.
Covers all 9 intents. Designed to stress-test Sarvam's ASR + classification
on real Indian manufacturing SMB sales conversations.

Intent taxonomy defined before model selection -- the model is evaluated
against this, not the other way around.
"""

TEST_MESSAGES = [
    # ---- HINDI / HINGLISH ----
    {
        "id": "H-01",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Bhai, M12 anchor bolts chahiye, 500 pcs, rate batao?",
        "expected_intent": "I-02",
        "intent_label": "New Enquiry",
        "notes": "Core Hinglish. Product code M12 is critical -- must survive ASR intact."
    },
    {
        "id": "H-02",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Kal payment kar deta hoon, 15000 ka hai na?",
        "expected_intent": "I-06",
        "intent_label": "Payment Update",
        "notes": "Payment commitment with amount. Intent relies on 'payment kar deta hoon'."
    },
    {
        "id": "H-03",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Order kab tak aayega? Ek hafte se wait kar raha hoon.",
        "expected_intent": "I-07",
        "intent_label": "Delivery Follow-up",
        "notes": "Delivery inquiry. Mild frustration -- should be I-07, not I-08 (Complaint)."
    },
    {
        "id": "H-04",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Bhai, jo pipe fittings aaye the, unme se 20 defective nikle. Kya karein?",
        "expected_intent": "I-08",
        "intent_label": "Complaint",
        "notes": "Clear complaint with quantity of defective items."
    },
    {
        "id": "H-05",
        "language": "hi-IN",
        "script": "devanagari",
        "text": "भाई, GI पाइप 2 इंच वाले 200 पीस चाहिए, क्या रेट है?",
        "expected_intent": "I-02",
        "intent_label": "New Enquiry",
        "notes": "Pure Devanagari. Tests native script handling. 'GI' is a product code."
    },
    {
        "id": "H-06",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Ha bhai confirm hai, 1000 pcs ka order de do. PO kal bhejta hoon.",
        "expected_intent": "I-05",
        "intent_label": "Order Confirmation",
        "notes": "High-stakes intent. 'Confirm' + 'PO' are the key signals."
    },
    {
        "id": "H-07",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Bhai 10000 mein nahi hoga kya? Thoda adjust karo.",
        "expected_intent": "I-04",
        "intent_label": "Price Negotiation",
        "notes": "Negotiation without explicit product mention. Needs open deal context."
    },
    {
        "id": "H-08",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Haan haan, sab theek hai. Aaj raat free hoon kya?",
        "expected_intent": "I-09",
        "intent_label": "Out of Scope",
        "notes": "Personal message. Must not trigger a CRM action."
    },

    # ---- GUJARATI ----
    {
        "id": "G-01",
        "language": "gu-IN",
        "script": "gujarati",
        "text": "ભાઈ, M16 બોલ્ટ 300 નંગ જોઈએ છે, ભાવ શું છે?",
        "expected_intent": "I-02",
        "intent_label": "New Enquiry",
        "notes": "Pure Gujarati script. M16 is the product code. 'નંગ' = pieces."
    },
    {
        "id": "G-02",
        "language": "gu-IN",
        "script": "gujarati_roman",
        "text": "Bhai, kal payment mokli dau chhu, 22000 nu che.",
        "expected_intent": "I-06",
        "intent_label": "Payment Update",
        "notes": "Gujarati-Roman. 'Mokli dau' = will send. Amount embedded."
    },
    {
        "id": "G-03",
        "language": "gu-IN",
        "script": "gujarati",
        "text": "ઓર્ડર ક્યારે આવશે? ૧૦ દિવસ થઈ ગયા.",
        "expected_intent": "I-07",
        "intent_label": "Delivery Follow-up",
        "notes": "Gujarati numerals (૧૦ = 10). Tests numeral handling in ASR."
    },
    {
        "id": "G-04",
        "language": "gu-IN",
        "script": "gujarati_roman",
        "text": "Ha confirm che, 500 piece no order apo. PO moku chu.",
        "expected_intent": "I-05",
        "intent_label": "Order Confirmation",
        "notes": "Gujarati-Roman. 'Moku chu' = will send. PO signal present."
    },
    {
        "id": "G-05",
        "language": "gu-IN",
        "script": "gujarati",
        "text": "ભાઈ, આ pipe fittings માં leakage આવે છે. બધા return કરવા છે.",
        "expected_intent": "I-08",
        "intent_label": "Complaint",
        "notes": "Code-switched: Gujarati + English (leakage, return, pipe fittings)."
    },

    # ---- MARATHI ----
    {
        "id": "M-01",
        "language": "mr-IN",
        "script": "marathi_roman",
        "text": "Bhai, GI pipe 1 inch wale 500 feet pahije, rate kiti?",
        "expected_intent": "I-02",
        "intent_label": "New Enquiry",
        "notes": "Marathi-Roman. 'Pahije' = need. 'Kiti' = how much."
    },
    {
        "id": "M-02",
        "language": "mr-IN",
        "script": "devanagari",
        "text": "भाऊ, उद्या पेमेंट करतो, ₹18,000 आहे ना?",
        "expected_intent": "I-06",
        "intent_label": "Payment Update",
        "notes": "Marathi Devanagari. Rupee symbol + comma-formatted amount -- known ASR failure point."
    },
    {
        "id": "M-03",
        "language": "mr-IN",
        "script": "marathi_roman",
        "text": "Confirm aahe, 200 piece order dya. PO pathvato.",
        "expected_intent": "I-05",
        "intent_label": "Order Confirmation",
        "notes": "Marathi-Roman. 'Pathvato' = will send."
    },
    {
        "id": "M-04",
        "language": "mr-IN",
        "script": "marathi_roman",
        "text": "Bhai, mala aajun ek order dyaycha aahe, vegle product aahe.",
        "expected_intent": "I-03",
        "intent_label": "Deal Creation",
        "notes": "Tricky: existing customer, NEW deal. 'Vegle product' = different product. Must not be I-02."
    },
    {
        "id": "M-05",
        "language": "mr-IN",
        "script": "devanagari",
        "text": "भाऊ, थोडं कमी होईल का? ₹12,000 मध्ये जमेल?",
        "expected_intent": "I-04",
        "intent_label": "Price Negotiation",
        "notes": "Marathi Devanagari. Pure price negotiation, no product mention."
    },

    # ---- STRESS TESTS ----
    {
        "id": "E-01",
        "language": "hi-IN",
        "script": "mixed",
        "text": "Bhai confirmed hai order, lekin 10% discount chahiye tabhi final karunga.",
        "expected_intent": "I-04",
        "intent_label": "Price Negotiation",
        "notes": "Ambiguous: sounds like confirmation but is conditional. Must be I-04, not I-05."
    },
    {
        "id": "E-02",
        "language": "hi-IN",
        "script": "hinglish_roman",
        "text": "Namaste",
        "expected_intent": "I-09",
        "intent_label": "Out of Scope",
        "notes": "Single word greeting. Simplest out-of-scope case."
    },
]

INTENT_TAXONOMY = {
    "I-01": "New Contact - Unknown number + business message",
    "I-02": "New Enquiry - Known contact asking about product/price",
    "I-03": "Deal Creation - Known contact, new distinct opportunity",
    "I-04": "Price Negotiation - Known contact, open deal, price discussion",
    "I-05": "Order Confirmation - Known contact, confirming intent to proceed",
    "I-06": "Payment Update - Payment status or timeline shared",
    "I-07": "Delivery Follow-up - Asking about order/delivery status",
    "I-08": "Complaint - Problem with existing order",
    "I-09": "Out of Scope - Personal, greeting, spam, unrelated",
}

if __name__ == "__main__":
    print(f"Total messages: {len(TEST_MESSAGES)}")
    intent_counts: dict[str, int] = {}
    for m in TEST_MESSAGES:
        intent_counts[m["expected_intent"]] = intent_counts.get(m["expected_intent"], 0) + 1
    print("Intent distribution:")
    for k, v in sorted(intent_counts.items()):
        print(f"  {k} ({INTENT_TAXONOMY[k].split(' - ')[0]}): {v}")
    lang_counts: dict[str, int] = {}
    for m in TEST_MESSAGES:
        lang_counts[m["language"]] = lang_counts.get(m["language"], 0) + 1
    print("Language distribution:")
    for k, v in lang_counts.items():
        print(f"  {k}: {v}")
