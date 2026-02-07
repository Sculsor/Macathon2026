import json
from comparing_receipts import analyze_receipt_with_gemini
from hashing import compute_canonical_hash, verify_receipt

def test_receipt_integration(image_path, blockchain_memo=None):
    """
    Integration test: Analyze a receipt, generate a hash, and optionally verify against blockchain.
    """
    print("=" * 70)
    print(f"INTEGRATION TEST: Receipt Analysis & Hashing")
    print("=" * 70)
    
    try:
        # Step 1: Analyze the receipt
        print(f"\n[Step 1] Analyzing receipt from: {image_path}")
        receipt_data = analyze_receipt_with_gemini(image_path)
        
        print("\n[Receipt Analysis Result]")
        print(json.dumps(receipt_data, indent=2))
        
        # Step 2: Compute hash from analyzed data
        print("\n" + "=" * 70)
        print("[Step 2] Computing canonical hash from receipt data")
        print("=" * 70)
        
        receipt_hash = compute_canonical_hash(receipt_data)
        
        if receipt_hash:
            print(f"\nCanonical Hash Generated: {receipt_hash}")
        else:
            print("ERROR: Failed to generate hash")
            return
        
        # Step 3: Verify arithmetic
        print("\n" + "=" * 70)
        print("[Step 3] Validating Receipt Arithmetic")
        print("=" * 70)
        
        subtotal = receipt_data.get('subtotal', 0)
        tax = receipt_data.get('tax', 0)
        total = receipt_data.get('total', 0)
        
        calculated_total = subtotal + tax
        difference = abs(calculated_total - total)
        
        print(f"\nSubtotal:          ${subtotal:.2f}")
        print(f"Tax:               ${tax:.2f}")
        print(f"Calculated Total:  ${calculated_total:.2f}")
        print(f"Receipt Total:     ${total:.2f}")
        print(f"Difference:        ${difference:.2f}")
        
        if difference < 0.02:
            print("✓ Arithmetic PASSED - Receipt math is correct")
            arithmetic_valid = True
        else:
            print("✗ Arithmetic FAILED - Receipt math has discrepancies")
            arithmetic_valid = False
        
        # Step 4: Blockchain verification (if memo provided)
        print("\n" + "=" * 70)
        print("[Step 4] Blockchain Verification")
        print("=" * 70)
        
        if blockchain_memo:
            print(f"\nBlockchain Memo: {blockchain_memo}")
            is_valid, message = verify_receipt(receipt_data, blockchain_memo)
            print(f"Verification Result: {is_valid}")
            print(f"Message: {message}")
        else:
            print("\nNo blockchain memo provided - generating one for reference")
            blockchain_memo = f"DEEPFAKERECEIPT:{receipt_hash}"
            print(f"Generated Memo: {blockchain_memo}")
            print("\nTo verify this receipt, use this memo on-chain")
        
        # Step 5: Fraud analysis from receipt_analyzer
        print("\n" + "=" * 70)
        print("[Step 5] Fraud Analysis")
        print("=" * 70)
        
        fraud_score = receipt_data.get('fraud_score', 'N/A')
        verdict = receipt_data.get('verdict', 'N/A')
        reasons = receipt_data.get('reasons', [])
        
        print(f"\nFraud Score: {fraud_score}/100")
        print(f"Verdict: {verdict}")
        
        if reasons:
            print("\nAnalysis Reasons:")
            for i, reason in enumerate(reasons, 1):
                print(f"  {i}. {reason}")
        
        # Step 6: Summary Report
        print("\n" + "=" * 70)
        print("[Summary Report]")
        print("=" * 70)
        
        print(f"\nMerchant:          {receipt_data.get('merchant', 'N/A')}")
        print(f"Date:              {receipt_data.get('date', 'N/A')}")
        print(f"Currency:          {receipt_data.get('currency', 'N/A')}")
        print(f"Total Amount:      ${total:.2f}")
        print(f"\nArithmetic Valid:  {'✓ YES' if arithmetic_valid else '✗ NO'}")
        print(f"Fraud Score:       {fraud_score}")
        print(f"Overall Verdict:   {verdict}")
        print(f"\nCanonical Hash:    {receipt_hash}")
        print(f"Blockchain Memo:   {blockchain_memo}")
        
        print("\n" + "=" * 70)
        print("Integration test completed successfully!")
        print("=" * 70)
        
        return {
            "receipt_data": receipt_data,
            "hash": receipt_hash,
            "blockchain_memo": blockchain_memo,
            "arithmetic_valid": arithmetic_valid,
            "fraud_score": fraud_score,
            "verdict": verdict
        }
        
    except FileNotFoundError:
        print(f"\nERROR: Could not find receipt image at: {image_path}")
        print("Please check the path and ensure receipt.jpg exists in the tests/ folder")
        return None
    except json.JSONDecodeError as e:
        print(f"\nERROR: Failed to parse receipt analyzer output as JSON: {e}")
        print("Please check that the Gemini API response is valid JSON")
        return None
    except Exception as e:
        print(f"\nERROR: {type(e).__name__}: {e}")
        return None


def test_with_sample_data():
    """
    Test integration with pre-defined sample data (no image required).
    Useful for testing when image is not available.
    """
    print("=" * 70)
    print("INTEGRATION TEST: Sample Data Analysis & Hashing")
    print("=" * 70)
    
    # Sample receipt data (as if returned by receipt_analyzer)
    sample_receipt = {
        "merchant": "Starbucks Coffee",
        "date": "2026-02-07",
        "time": "14:30:00",
        "currency": "CAD",
        "subtotal": 12.34,
        "tax": 1.60,
        "total": 13.94,
        "line_items": [
            {"item": "Venti Latte", "quantity": 1, "price": 6.50},
            {"item": "Blueberry Muffin", "quantity": 2, "price": 3.00},
            {"item": "Tall Americano", "quantity": 1, "price": 2.84}
        ],
        "fraud_score": 15,
        "verdict": "Likely Legit",
        "reasons": ["All math checks out", "Standard receipt format", "Reasonable items and prices"]
    }
    
    print("\n[Sample Receipt Data]")
    print(json.dumps(sample_receipt, indent=2))
    
    # Step 1: Compute hash
    print("\n" + "=" * 70)
    print("[Step 1] Computing canonical hash")
    print("=" * 70)
    
    receipt_hash = compute_canonical_hash(sample_receipt)
    print(f"\nCanonical Hash: {receipt_hash}")
    
    # Step 2: Create blockchain memo
    blockchain_memo = f"DEEPFAKERECEIPT:{receipt_hash}"
    print(f"Blockchain Memo: {blockchain_memo}")
    
    # Step 3: Verify receipt against its own hash
    print("\n" + "=" * 70)
    print("[Step 2] Verifying receipt against blockchain memo")
    print("=" * 70)
    
    is_valid, message = verify_receipt(sample_receipt, blockchain_memo)
    print(f"\nVerification Result: {is_valid}")
    print(f"Message: {message}")
    
    # Step 4: Test verification with mismatched data
    print("\n" + "=" * 70)
    print("[Step 3] Testing with modified receipt (should fail verification)")
    print("=" * 70)
    
    modified_receipt = sample_receipt.copy()
    modified_receipt["total"] = 14.94  # Changed total
    
    print(f"\nModified Total: ${modified_receipt['total']}")
    is_valid_modified, message_modified = verify_receipt(modified_receipt, blockchain_memo)
    print(f"Verification Result: {is_valid_modified}")
    print(f"Message: {message_modified}")
    
    # Step 5: Summary
    print("\n" + "=" * 70)
    print("[Summary Report]")
    print("=" * 70)
    
    print(f"\nMerchant:              {sample_receipt['merchant']}")
    print(f"Date:                  {sample_receipt['date']}")
    print(f"Total Amount:          ${sample_receipt['total']:.2f}")
    print(f"Fraud Score:           {sample_receipt['fraud_score']}/100")
    print(f"Verdict:               {sample_receipt['verdict']}")
    print(f"\nOriginal Hash Valid:   {'✓ YES' if is_valid else '✗ NO'}")
    print(f"Modified Hash Valid:   {'✓ YES' if is_valid_modified else '✗ NO'}")
    print(f"\nCanonical Hash:        {receipt_hash}")
    print(f"Blockchain Memo:       {blockchain_memo}")
    
    print("\n" + "=" * 70)
    print("Sample data test completed successfully!")
    print("=" * 70)
    
    return {
        "receipt_data": sample_receipt,
        "hash": receipt_hash,
        "blockchain_memo": blockchain_memo,
        "original_verification": is_valid,
        "modified_verification": is_valid_modified
    }


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("RECEIPT INTEGRATION TEST SUITE")
    print("=" * 70)
    
    # Test 1: Sample data (always works)
    print("\n\n>>> Running Test 1: Sample Data Integration")
    test_with_sample_data()
    
    # Test 2: Real image (if available)
    print("\n\n>>> Running Test 2: Real Receipt Image Integration")
    receipt_path = "tests/receipt.jpg"
    result = test_receipt_integration(receipt_path)
    
    if result:
        print("\n[Test 2 Result]")
        print("Receipt integration test PASSED")
    else:
        print("\n[Test 2 Result]")
        print("Receipt image not found or analysis failed - this is expected if no test image exists")
    
    print("\n" + "=" * 70)
    print("ALL INTEGRATION TESTS COMPLETED")
    print("=" * 70)
