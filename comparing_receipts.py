from google import genai
from google.genai import types
from dotenv import load_dotenv
from datetime import datetime
import json
import os

load_dotenv()

# Your API key
API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini client
client = genai.Client(api_key=API_KEY)

# Sample pre-stored receipt data
SAMPLE_RECEIPTS = {
    "receipt_001": {
        "merchant": "Walmart",
        "date": "2026-02-07",
        "time": "14:30:22",
        "currency": "USD",
        "subtotal": 45.99,
        "tax": 3.68,
        "total": 49.67,
        "line_items": [
            {"item": "Milk 2%", "quantity": 2, "price": 4.99},
            {"item": "Bread", "quantity": 1, "price": 3.49},
            {"item": "Eggs Dozen", "quantity": 3, "price": 11.97}
        ]
    },
    "receipt_002": {
        "merchant": "Target",
        "date": "2026-02-06",
        "time": "10:15:00",
        "currency": "USD",
        "subtotal": 89.50,
        "tax": 7.16,
        "total": 96.66,
        "line_items": [
            {"item": "Coffee Maker", "quantity": 1, "price": 49.99},
            {"item": "Coffee Beans", "quantity": 2, "price": 19.98},
            {"item": "Filters", "quantity": 1, "price": 8.99}
        ]
    }
}

def analyze_receipt_with_gemini(receipt_data):
    """
    Uses Gemini to analyze receipt data for fraud/inconsistencies
    (TEXT-ONLY - no image scanning)
    """
    
    prompt = f"""
You are a receipt fraud detection AI. Analyze this receipt data and return ONLY valid JSON.

Receipt Data:
{json.dumps(receipt_data, indent=2)}

Your tasks:
1. Verify arithmetic: Does subtotal + tax = total? (allow ±$0.02 rounding)
2. Verify line items: Do line items sum to subtotal?
3. Check for anomalies:
   - Date in the future compared to today's date ({datetime.today().strftime('%Y-%m-%d')})        
   - Unusual merchant names
   - Suspicious date/time patterns
   - Currency mismatches
   - Missing required fields
   - Implausible values (negative amounts, extremely high tax rates)
4. Assign fraud_score (0-100):
   - 0-30: Likely Legit
   - 31-70: Suspicious
   - 71-100: Highly Suspicious

Return ONLY this JSON format, no other text:
{{
  "fraud_score": number,
  "verdict": "Likely Legit" | "Suspicious" | "Highly Suspicious",
  "reasons": ["reason 1", "reason 2", ...],
  "arithmetic_valid": true/false,
  "line_items_valid": true/false,
  "anomalies_found": ["anomaly 1", ...]
}}
"""

    try:
        # Call Gemini with TEXT only (no image)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        
        # Parse response
        result_text = response.text.strip()
        result_text = result_text.replace('```json', '').replace('```', '').strip()
        analysis = json.loads(result_text)
        
        return analysis
        
    except Exception as e:
        # Fallback to basic validation if API fails
        print(f"⚠️ Gemini API error: {e}")
        print("Falling back to basic validation...")
        return basic_validation(receipt_data)

def basic_validation(receipt_data):
    """
    Fallback validation without Gemini
    """
    reasons = []
    anomalies = []
    fraud_score = 0

    # Check if date is in the future
    try:
        receipt_date = datetime.strptime(receipt_data.get("date", ""), "%Y-%m-%d")
        today = datetime.today()
        if receipt_date.date() > today.date():
            anomalies.append(f"Receipt date {receipt_data.get('date')} is in the future")
            reasons.append(f"Receipt date {receipt_data.get('date')} is invalid (future date)")
            fraud_score += 40
    except ValueError:
        # Invalid date format
        anomalies.append(f"Invalid date format: {receipt_data.get('date')}")
        reasons.append(f"Invalid date format")
        fraud_score += 20

    
    # Check arithmetic
    calculated_total = receipt_data.get('subtotal', 0) + receipt_data.get('tax', 0)
    actual_total = receipt_data.get('total', 0)
    arithmetic_valid = abs(calculated_total - actual_total) <= 0.02
    
    if not arithmetic_valid:
        reasons.append(f"Math error: {receipt_data.get('subtotal')} + {receipt_data.get('tax')} ≠ {actual_total}")
        fraud_score += 50
    else:
        reasons.append("Arithmetic checks passed")
    
    # Check line items
    line_items_valid = True
    if receipt_data.get('line_items'):
        line_total = sum(item['quantity'] * item['price'] for item in receipt_data['line_items'])
        line_items_valid = abs(line_total - receipt_data.get('subtotal', 0)) <= 0.02

        if not line_items_valid:
            reasons.append(f"Line items sum to {line_total:.2f} but subtotal is {receipt_data.get('subtotal')}")
            fraud_score += 30
    
    # Check required fields
    required_fields = ['merchant', 'date', 'currency', 'subtotal', 'tax', 'total']
    missing = [f for f in required_fields if not receipt_data.get(f)]
    
    if missing:
        anomalies.append(f"Missing fields: {', '.join(missing)}")
        fraud_score += 20
    
    # Determine verdict
    if fraud_score <= 30:
        verdict = "Likely Legit"
    elif fraud_score <= 70:
        verdict = "Suspicious"
    else:
        verdict = "Highly Suspicious"
    
    return {
        "fraud_score": fraud_score,
        "verdict": verdict,
        "reasons": reasons,
        "arithmetic_valid": arithmetic_valid,
        "line_items_valid": line_items_valid,
        "anomalies_found": anomalies
    }

def compare_to_certified(user_input, receipt_id):
    """
    Compares user input to a certified receipt
    """
    if receipt_id not in SAMPLE_RECEIPTS:
        return False, ["Receipt ID not found in certified database"]
    
    certified = SAMPLE_RECEIPTS[receipt_id]
    differences = []
    
    key_fields = ['merchant', 'date', 'time', 'currency', 'subtotal', 'tax', 'total']
    
    for field in key_fields:
        user_value = user_input.get(field)
        cert_value = certified.get(field)
        
        if user_value != cert_value:
            differences.append(f"{field}: user has '{user_value}', certified has '{cert_value}'")
    
    matches = len(differences) == 0
    
    if matches:
        differences = ["✓ All fields match certified receipt"]
    
    return matches, differences

if __name__ == "__main__":
    print("--- DEEPFAKE RECEIPT ANALYZER (Gemini-Enhanced) ---\n")
    
    # Example 1: Valid receipt
    print("--- Example 1: Valid Receipt ---")
    valid_receipt = {
        "merchant": "Walmart",
        "date": "2026-02-07",
        "time": "14:30:22",
        "currency": "USD",
        "subtotal": 45.99,
        "tax": 3.68,
        "total": 49.67,
        "line_items": [
            {"item": "Milk 2%", "quantity": 2, "price": 9.98},
            {"item": "Bread", "quantity": 1, "price": 3.49},
            {"item": "Eggs Dozen", "quantity": 3, "price": 11.97},
            {"item": "Butter", "quantity": 1, "price": 4.99},
            {"item": "Cheese", "quantity": 2, "price": 15.56}
        ]
    }

    analysis = analyze_receipt_with_gemini(valid_receipt)
    print(json.dumps(analysis, indent=2))
    
    # Example 2: Tampered receipt
    print("\n--- Example 2: Tampered Receipt ---")
    tampered_receipt = {
        "merchant": "Walmart",
        "date": "2026-02-07",
        "time": "14:30:22",
        "currency": "USD",
        "subtotal": 45.99,
        "tax": 3.68,
        "total": 99.99,  # TAMPERED HERE!
        "line_items": []
    }
    
    analysis = analyze_receipt_with_gemini(tampered_receipt)
    print(json.dumps(analysis, indent=2))
    
    # Example 3: Compare to certified
    print("\n--- Example 3: Verification Against Certified Receipt ---")
    matches, differences = compare_to_certified(valid_receipt, "receipt_001")
    
    print(f"Verification: {'✓ VERIFIED' if matches else '✗ NOT VERIFIED'}")
    for diff in differences:
        print(f"  {diff}")