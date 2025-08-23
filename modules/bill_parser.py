import re

class BillParser:
    def __init__(self):
        # Define regex patterns for common bill data fields
        self.patterns = {
            "bill_number": r"(?:Account Number|Account No|Invoice Number|Bill No|Reference No)[:\s]*([\w-]+)",
            "total_amount": r"(?:Total Amount|Amount Due|Balance Due)[:\s]*[\$€£¥]?\s*([\d.,]+)",
            "currency": r"(?:Total Amount|Amount Due|Balance Due)[:\s]*([\$€£¥])", # Capture the currency symbol
            "customer_name": r"(?:Customer Name|Client Name|Name)[:\s]*(.+)", # Placeholder, as it's not in the sample PDF
            "remittance_coupon_keywords": r"(?:Remittance Coupon|Payment Stub|Please Detach|Return with Payment|please return bottom portion with your payment)"
        }

    def find_remittance_coupon(self, bill_text: str) -> str:
        coupon_text = ""
        lines = bill_text.split('\n')
        found_coupon = False
        coupon_start_line = -1

        for i, line in enumerate(lines):
            if re.search(self.patterns["remittance_coupon_keywords"], line, re.IGNORECASE):
                found_coupon = True
                coupon_start_line = i
                break
        
        if found_coupon:
            # Heuristic: Capture a few lines after the keyword as the coupon
            # This can be improved with more advanced layout analysis
            for i in range(coupon_start_line, min(coupon_start_line + 10, len(lines))):
                coupon_text += lines[i] + "\n"
        
        return coupon_text.strip()

    def parse_bill(self, bill_text: str) -> dict:
        bill_data = {}
        
        # Extract bill number
        match = re.search(self.patterns["bill_number"], bill_text, re.IGNORECASE)
        if match:
            bill_data["bill_number"] = match.group(1).strip()
        
        # Extract total amount
        match = re.search(self.patterns["total_amount"], bill_text, re.IGNORECASE)
        if match:
            bill_data["total_amount"] = match.group(1).strip()

        # Extract currency
        match = re.search(self.patterns["currency"], bill_text)
        if match:
            currency_symbol = match.group(1)
            if currency_symbol == "$":
                bill_data["currency"] = "USD"
            else:
                bill_data["currency"] = currency_symbol # Or handle other currencies
        else:
            bill_data["currency"] = "N/A" # Default if no currency symbol found

        # Extract customer name (using placeholder for now)
        match = re.search(self.patterns["customer_name"], bill_text, re.IGNORECASE)
        if match:
            bill_data["customer_name"] = match.group(1).strip()
        else:
            bill_data["customer_name"] = "Valued Customer" # Default if not found

        # Find and parse remittance coupon (for demonstration)
        remittance_coupon_text = self.find_remittance_coupon(bill_text)
        if remittance_coupon_text:
            print(f"\n--- Remittance Coupon Found ---\n{remittance_coupon_text}\n---")
            # You can add more specific regex patterns here to extract data from the coupon
            # For example, if the coupon has its own amount due or account number

        return bill_data