def sign_as_agent(bill, agent_name, principal):
    signature_block = {
        "signed_by": agent_name,
        "capacity": f"Authorized Representative of {principal}",
        "signature": "SIMULATED_DIGITAL_SIGNATURE_ABC123",
        "date": "2025-08-18"
    }

    bill["signature_block"] = signature_block
    return bill