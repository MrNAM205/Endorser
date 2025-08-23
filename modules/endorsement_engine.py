def classify_instrument(bill):
    if "description" in bill and "amount" in bill:
        if "issuer" in bill and "recipient" in bill:
            return "draft"  # Most utility bills are orders to pay
    return "note"

def apply_endorsement(bill, instrument_type, text):
    endorsement = {
        "endorser_name": bill["recipient"],
        "text": text,
        "next_payee": "GFL Environmental Services",
        "prev_hash": bill.get("prev_hash", "N/A"),
        "signature": "SIMULATED_SIGNATURE_1234567890"
    }

    bill.setdefault("endorsements", []).append(endorsement)
    return bill