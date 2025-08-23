from flask import Flask, request, jsonify
import subprocess
import os
import yaml
from datetime import datetime
from PyPDF2 import PdfReader
import pytesseract

# --- MODULES FROM ENDORSEMENT ENGINE ---
from modules.Ucc3_Endorsements import sign_endorsement
from modules.remedy_logger import log_remedy
from modules.bill_parser import BillParser
from modules.attach_endorsement_to_pdf import attach_endorsement_to_pdf_function

app = Flask(__name__)

# --- CONFIGURATION ---
# Load the private key from an environment variable for security
PRIVATE_KEY_PEM = os.environ.get("PRIVATE_KEY_PEM")
SOVEREIGN_OVERLAY_CONFIG = "config/sovereign_overlay.yaml"

# --- HELPER FUNCTIONS (from endorsement engine) ---

def load_yaml_config(config_path: str) -> dict:
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config
    except FileNotFoundError:
        return {"error": f"Config file not found: {config_path}"}
    except yaml.YAMLError as e:
        return {"error": f"Error parsing YAML: {e}"}

def get_bill_data_from_source(bill_source_path: str) -> dict:
    if bill_source_path.endswith(".pdf"):
        text = ""
        try:
            with open(bill_source_path, "rb") as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""
        except Exception as e:
            return {"error": f"PyPDF2 text extraction failed: {e}"}

        if not text.strip():
            return {"error": "Could not parse bill data from PDF (no text extracted)."}
        
        parser = BillParser()
        bill_data = parser.parse_bill(text)

        if not bill_data.get("bill_number"):
            return {"error": "Could not parse bill number from PDF."}
            
        return bill_data
    else:
        return {"error": "Unsupported bill source format."}

def prepare_endorsement_for_signing(bill_data: dict, endorsement_text: str) -> dict:
    return {
        "document_type": bill_data.get("document_type", "Unknown"),
        "bill_number": bill_data.get("bill_number", "N/A"),
        "customer_name": bill_data.get("customer_name", "N/A"),
        "total_amount": bill_data.get("total_amount", "N/A"),
        "currency": bill_data.get("currency", "N/A"),
        "endorsement_date": datetime.now().strftime("%Y-%m-%d"),
        "endorser_id": "WEB-UTIL-001",
        "endorsement_text": endorsement_text
    }

@app.route('/scan-contract', methods=['POST'])
def scan_contract():
    file = request.files['contract']
    tag = request.form['tag']
    filepath = os.path.join('uploads', file.filename)
    file.save(filepath)

    result = subprocess.run(['bash', 'clausescanner.sh', f'--contract={filepath}', f'--tags={tag}'], capture_output=True, text=True)
    return jsonify({'output': result.stdout})

@app.route('/endorse-bill', methods=['POST'])
def endorse_bill():
    if not PRIVATE_KEY_PEM:
        return jsonify({"error": "Server is not configured with a private key."}), 500

    if 'bill' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['bill']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    uploads_dir = os.path.join(os.getcwd(), 'uploads')
    os.makedirs(uploads_dir, exist_ok=True)
    filepath = os.path.join(uploads_dir, file.filename)
    file.save(filepath)

    try:
        bill_data = get_bill_data_from_source(filepath)
        if "error" in bill_data:
            return jsonify(bill_data), 500

        overlay_config = load_yaml_config(SOVEREIGN_OVERLAY_CONFIG)
        if "error" in overlay_config:
            sovereign_endorsements = []
        else:
            sovereign_endorsements = overlay_config.get("sovereign_endorsements", [])

        if not sovereign_endorsements:
            return jsonify({"message": "Bill processed, but no applicable endorsements found in config."}), 200

        endorsed_files = []
        for endorsement_type in sovereign_endorsements:
            trigger = endorsement_type.get("trigger", "Unknown")
            meaning = endorsement_type.get("meaning", "")
            ink_color = endorsement_type.get("ink_color", "black")
            placement = endorsement_type.get("placement", "Front")
            page_index = 0 if placement.lower() == "front" else -1

            endorsement_text = f"{trigger}: {meaning}"
            endorsement_to_sign = prepare_endorsement_for_signing(bill_data, endorsement_text)

            signed_endorsement = sign_endorsement(
                endorsement_data=endorsement_to_sign,
                endorser_name=bill_data.get("customer_name", "N/A"),
                private_key_pem=PRIVATE_KEY_PEM
            )

            bill_for_logging = {
                "instrument_id": bill_data.get("bill_number"),
                "issuer": bill_data.get("issuer", "Unknown"),
                "recipient": bill_data.get("customer_name"),
                "amount": bill_data.get("total_amount"),
                "currency": bill_data.get("currency"),
                "description": bill_data.get("description", "N/A"),
                "endorsements": [{
                    "endorser_name": signed_endorsement.get("endorser_id"),
                    "text": endorsement_text,
                    "next_payee": "Original Creditor",
                    "signature": signed_endorsement["signature"]
                }],
                "signature_block": {
                    "signed_by": signed_endorsement.get("endorser_id"),
                    "capacity": "Payer",
                    "signature": signed_endorsement["signature"],
                    "date": signed_endorsement.get("endorsement_date")
                }
            }

            log_remedy(bill_for_logging)

            output_pdf_name = f"endorsed_{os.path.basename(filepath).replace('.pdf', '')}_{trigger.replace(' ', '')}.pdf"
            endorsed_output_path = os.path.join(uploads_dir, output_pdf_name)

            attach_endorsement_to_pdf_function(
                original_pdf_path=filepath,
                endorsement_data=bill_for_logging,
                output_pdf_path=endorsed_output_path,
                ink_color=ink_color,
                page_index=page_index
            )
            endorsed_files.append(output_pdf_name)

        return jsonify({"message": "Bill endorsed successfully", "endorsed_files": endorsed_files})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/generate-remedy', methods=['POST'])
def generate_remedy():
    violation = request.form['violation']
    jurisdiction = request.form['jurisdiction']
    result = subprocess.run(['bash', 'remedygenerator.sh', f'--violation={violation}', f'--jurisdiction={jurisdiction}'], capture_output=True, text=True)
    return jsonify({'output': result.stdout})

if __name__ == '__main__':
    os.makedirs('uploads', exist_ok=True)
    app.run(debug=True)