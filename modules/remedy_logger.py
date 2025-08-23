import os
import json
from datetime import datetime

def log_remedy(bill):
    date_str = datetime.now().strftime("%Y-%m-%d")
    bill_name = bill.get("instrument_id", "unnamed_bill")
    log_folder = "remedy_logs"
    os.makedirs(log_folder, exist_ok=True)

    # Save JSON log
    json_path = os.path.join(log_folder, f"{date_str}_{bill_name}.json")
    with open(json_path, "w") as f:
        json.dump(bill, f, indent=4)

    # Save human-readable log
    txt_path = os.path.join(log_folder, f"{date_str}_{bill_name}.txt")
    with open(txt_path, "w") as f:
        f.write(f"Remedy Log for {bill_name} — {date_str}\n\n")
        f.write(f"Issuer: {bill['issuer']}\n")
        f.write(f"Recipient: {bill['recipient']}\n")
        f.write(f"Amount: {bill['amount']} {bill['currency']}\n")
        f.write(f"Description: {bill['description']}\n\n")
        for i, e in enumerate(bill.get("endorsements", []), start=1):
            f.write(f"Endorsement {i}:\n")
            f.write(f"  Endorser: {e['endorser_name']}\n")
            f.write(f"  Text: {e['text']}\n")
            f.write(f"  Next Payee: {e['next_payee']}\n")
            f.write(f"  Signature: {e['signature'][:60]}...\n\n")
        sig = bill.get("signature_block", {})
        f.write(f"Signed by: {sig.get('signed_by')} ({sig.get('capacity')})\n")
        f.write(f"Signature: {sig.get('signature')}\n")
        f.write(f"Date: {sig.get('date')}\n")

    print(f"📜 Remedy log saved: {json_path}")