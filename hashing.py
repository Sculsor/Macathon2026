import json
import hashlib

def compute_canonical_hash(data):
    """
    Normalizes receipt data and returns a SHA-256 hash.
    Fields used: merchant, date, currency, subtotal, tax, total.
    """
    try:
        # 1. Normalization & Cleaning
        # We use .get() to avoid KeyErrors if Gemini misses a field
        canonical = {
            "merchant": str(data.get('merchant', '')).lower().strip(),
            "date": str(data.get('date', "null")).strip(),
            "currency": str(data.get('currency', 'CAD')).upper().strip(),
            "subtotal": "{:.2f}".format(float(data.get('subtotal', 0))),
            "tax": "{:.2f}".format(float(data.get('tax', 0))),
            "total": "{:.2f}".format(float(data.get('total', 0)))
        }

        # 2. Key Sorting & Stable Serialization
        # sort_keys=True ensures the JSON string is always in the same order
        # separators removes whitespace for a "tight" string
        canonical_string = json.dumps(canonical, sort_keys=True, separators=(',', ':'))

        # 3. Generate SHA-256
        hash_object = hashlib.sha256(canonical_string.encode('utf-8'))
        return hash_object.hexdigest()

    except (ValueError, TypeError) as e:
        print(f"Error during hashing: {e}")
        return None

def verify_receipt(current_scan_json, solana_memo_string):
    """
    Compares the current physical receipt hash against the one on-chain.
    """
    # 1. Compute hash of the image currently being scanned
    current_hash = compute_canonical_hash(current_scan_json)
    
    # 2. Extract hash from Solana memo (Format: "DEEPFAKERECEIPT:<hash>")
    if ":" not in solana_memo_string:
        return False, "Invalid Solana memo format"
        
    expected_hash = solana_memo_string.split(':')[-1]

    # 3. Final comparison
    if current_hash == expected_hash:
        return True, "VERIFIED: Receipt matches the blockchain record."
    else:
        return False, "NOT VERIFIED: Receipt data does not match the original certification."


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Hashing Functions")
    print("=" * 60)
    
    # Test 1: Basic hash computation
    print("\n[Test 1] Computing hash for sample receipt data:")
    sample_receipt = {
        "merchant": "Starbucks",
        "date": "2026-02-07",
        "currency": "CAD",
        "subtotal": 5.15,
        "tax": 0.60,
        "total": 5.75
    }
    hash1 = compute_canonical_hash(sample_receipt)
    print(f"Sample Receipt: {sample_receipt}")
    print(f"Generated Hash: {hash1}")
    
    # Test 2: Verify hash consistency (same data = same hash)
    print("\n[Test 2] Testing hash consistency (identical data):")
    sample_receipt_2 = {
        "merchant": "STARBUCKS",  # Different case
        "date": "2026-02-07",
        "currency": "cad",  # Different case
        "subtotal": 5.15,
        "tax": 0.60,
        "total": 5.75
    }
    hash2 = compute_canonical_hash(sample_receipt_2)
    print(f"Sample Receipt 2: {sample_receipt_2}")
    print(f"Generated Hash: {hash2}")
    print(f"Hashes match (normalization works): {hash1 == hash2}")
    
    # Test 3: Different data produces different hash
    print("\n[Test 3] Different receipt data produces different hash:")
    sample_receipt_3 = {
        "merchant": "McDonald's",
        "date": "2026-02-07",
        "currency": "CAD",
        "subtotal": 11.20,
        "tax": 1.30,
        "total": 12.50
    }
    hash3 = compute_canonical_hash(sample_receipt_3)
    print(f"Sample Receipt 3: {sample_receipt_3}")
    print(f"Generated Hash: {hash3}")
    print(f"Hashes differ: {hash1 != hash3}")
    
    # Test 4: Verify receipt (matching case)
    print("\n[Test 4] Verify receipt with matching blockchain memo:")
    solana_memo_1 = f"DEEPFAKERECEIPT:{hash1}"
    is_valid, message = verify_receipt(sample_receipt, solana_memo_1)
    print(f"Blockchain Memo: {solana_memo_1}")
    print(f"Verification Result: {is_valid}")
    print(f"Message: {message}")
    
    # Test 5: Verify receipt (non-matching case)
    print("\n[Test 5] Verify receipt with mismatched blockchain memo:")
    solana_memo_2 = f"DEEPFAKERECEIPT:{hash3}"
    is_valid, message = verify_receipt(sample_receipt, solana_memo_2)
    print(f"Current Receipt: {sample_receipt}")
    print(f"Blockchain Memo: {solana_memo_2}")
    print(f"Verification Result: {is_valid}")
    print(f"Message: {message}")
    
    # Test 6: Error handling - invalid memo format
    print("\n[Test 6] Error handling for invalid memo format:")
    invalid_memo = "INVALID_FORMAT_NO_COLON"
    is_valid, message = verify_receipt(sample_receipt, invalid_memo)
    print(f"Invalid Memo: {invalid_memo}")
    print(f"Verification Result: {is_valid}")
    print(f"Message: {message}")
    
    # Test 7: Error handling - missing fields
    print("\n[Test 7] Error handling for missing fields:")
    incomplete_receipt = {
        "merchant": "CVS",
        "total": 25.00
        # Missing date, currency, subtotal, and tax
    }
    hash_incomplete = compute_canonical_hash(incomplete_receipt)
    print(f"Incomplete Receipt: {incomplete_receipt}")
    print(f"Generated Hash (with defaults): {hash_incomplete}")
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)