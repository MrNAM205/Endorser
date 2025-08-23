import base64
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.backends import default_backend

def sign_endorsement(endorsement_data, endorser_name, private_key_pem: str = None, private_key_object=None):
    """
    Signs an endorsement using an RSA private key.

    Args:
        endorsement_data: The endorsement object/data to be signed.
                          It should have a __str__ method or be directly convertible to string.
        endorser_name (str): The name of the endorser (used for context, not for key loading).
        private_key_pem (str, optional): The RSA private key as a PEM-formatted string.
        private_key_object: An already loaded cryptography RSA private key object.
                            If private_key_pem is not provided, this object must be.

    Returns:
        The endorsement_data object with a 'signature' attribute added.

    Raises:
        ValueError: If neither private_key_pem nor private_key_object is provided.
        Exception: For issues with key loading or signing.
    """
    if private_key_pem:
        try:
            private_key = serialization.load_pem_private_key(
                private_key_pem.encode('utf-8'),
                password=None,  # Assuming no password, adjust if needed
                backend=default_backend()
            )
        except Exception as e:
            raise Exception(f"Error loading private key from PEM string: {e}")
    elif private_key_object:
        private_key = private_key_object
    else:
        raise ValueError("Either 'private_key_pem' (as a string) or 'private_key_object' must be provided.")

    if not hasattr(private_key, 'sign'):
        raise Exception("Provided private key object does not have a 'sign' method (is it an RSA private key?).")

    # Convert endorsement data to bytes
    # Assuming endorsement_data can be converted to a string, similar to PowerShell's .ToString()
    bytes_to_sign = str(endorsement_data).encode('utf-8')

    try:
        signature = private_key.sign(
            bytes_to_sign,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
    except Exception as e:
        raise Exception(f"Error during signing: {e}")

    # Add the base64 encoded signature to the endorsement data
    # Assuming endorsement_data is a mutable object (e.g., a dictionary or a custom class instance)
    # If it's immutable, you'll need to return a new object or a tuple.
    if isinstance(endorsement_data, dict):
        endorsement_data['signature'] = base64.b64encode(signature).decode('utf-8')
    else:
        # For custom objects, you might need to set an attribute
        setattr(endorsement_data, 'signature', base64.b64encode(signature).decode('utf-8'))

    return endorsement_data

# Example Usage (for demonstration purposes, you would replace this with your actual usage)
if __name__ == "__main__":
    # This is a placeholder for your actual endorsement data structure
    class Endorsement:
        def __init__(self, id, content):
            self.id = id
            self.content = content
            self.signature = None # Will be set by the function

        def __str__(self):
            return f"Endorsement ID: {self.id}, Content: {self.content}"

    # --- IMPORTANT: Replace with your actual private key path ---
    # For testing, you can generate a dummy key:
    # from cryptography.hazmat.primitives.asymmetric import rsa
    # private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    # with open("private_key.pem", "wb") as f:
    #     f.write(private_key.private_bytes(
    #         encoding=serialization.Encoding.PEM,
    #         format=serialization.PrivateFormat.PKCS8,
    #         encryption_algorithm=serialization.NoEncryption()
    #     ))
    # -------------------------------------------------------------

    # Example 1: Using a private key from a PEM file
    # Make sure 'private_key.pem' exists and contains your RSA private key
    # private_key_file_path = "private_key.pem"
    # try:
    #     my_endorsement = Endorsement(id="123", content="This is a test endorsement.")
    #     signed_endorsement = sign_endorsement(my_endorsement, "John Doe", private_key_pem_path=private_key_file_path)
    #     print(f"Signed Endorsement (from file): {signed_endorsement.signature}")
    # except Exception as e:
    #     print(f"Error in example 1: {e}")

    # Example 2: Using an already loaded private key object (e.g., generated in memory)
    from cryptography.hazmat.primitives.asymmetric import rsa
    in_memory_private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())

    try:
        my_endorsement_2 = Endorsement(id="456", content="Another test endorsement.")
        signed_endorsement_2 = sign_endorsement(my_endorsement_2, "Jane Smith", private_key_object=in_memory_private_key)
        print(f"Signed Endorsement (from object): {signed_endorsement_2.signature}")
    except Exception as e:
        print(f"Error in example 2: {e}")
