import google.generativeai as genai
import json

API_KEY = "AIzaSyCS-tKJMvqec28l9BOgiKFuNgJKvH3mdEg"

# Configure Gemini
genai.configure(api_key=API_KEY)

def analyze_receipt(image_path):
    """
    Analyzes a receipt image and returns structured JSON
    """
    
    # Create the prompt for Gemini
    prompt = """
You are a receipt verification AI. Analyze this receipt image and return ONLY valid JSON with no markdown formatting, no code blocks, no explanations.

Extract these fields:
- merchant: store/business name
- date: transaction date (YYYY-MM-DD format)
- time: transaction time (HH:MM:SS format, or null if not visible)
- currency: 3-letter code (USD, EUR, etc.)
- subtotal: amount before tax (as number)
- tax: tax amount (as number)
- total: final total (as number)
- line_items: array of items (ONLY if clearly readable, otherwise return empty array)
  - Each item: {"item": "name", "quantity": number, "price": number}

Fraud Analysis:
1. Check if subtotal + tax ≈ total (allow small rounding differences)
2. Check if receipt looks structurally valid
3. Assign fraud_score (0-100): 
   - 0-30: Likely Legit
   - 31-70: Suspicious
   - 71-100: Highly Suspicious
4. Set verdict: "Likely Legit" OR "Suspicious" OR "Unreadable"
5. List reasons: explain what you found (arithmetic errors, missing fields, etc.)

Return format:
{
  "merchant": "string",
  "date": "YYYY-MM-DD",
  "time": "HH:MM:SS or null",
  "currency": "string",
  "subtotal": number,
  "tax": number,
  "total": number,
  "line_items": [],
  "fraud_score": number,
  "verdict": "string",
  "reasons": ["string"]
}

Return ONLY the JSON. No other text.
"""
    
    # Upload the image file with mime type specified
    with open(image_path, 'rb') as f:
        uploaded_file = client.files.upload(
            file=f,
            config={'mime_type': 'image/jpeg'}
        )
    
    # Send to Gemini with the uploaded file - CHANGED MODEL NAME
    response = client.models.generate_content(
        model='gemini-2.0-flash',
        contents=[
            prompt,
            uploaded_file
        ]
    )
    
    # Get the text response
    result_text = response.text
    
    # Clean up any markdown formatting if it sneaks in
    result_text = result_text.replace('```json', '').replace('```', '').strip()
    
    # Parse JSON
    receipt_data = json.loads(result_text)
    
    return receipt_data

# Test the function
if __name__ == "__main__":
    # Test with your receipt image
    receipt_path = r"C:\Users\macma\macathon2026\tests\receipt.jpg"
    
    print("Analyzing receipt...")
    
    try:
        result = analyze_receipt(receipt_path)
        
        # Pretty print the result
        print("\n=== RECEIPT ANALYSIS ===")
        print(json.dumps(result, indent=2))
        
        # Validate arithmetic
        calculated_total = result['subtotal'] + result['tax']
        actual_total = result['total']
        difference = abs(calculated_total - actual_total)
        
        print(f"\n=== VALIDATION ===")
        print(f"Subtotal + Tax = {calculated_total:.2f}")
        print(f"Receipt Total = {actual_total:.2f}")
        print(f"Difference = {difference:.2f}")
        
        if difference < 0.02:
            print("✓ Math checks out!")
        else:
            print("✗ Math doesn't match - potential issue")
            
    except FileNotFoundError:
        print(f"ERROR: Could not find receipt image at: {receipt_path}")
        print("Please check the path is correct!")
    except Exception as e:
        print(f"ERROR: {e}")
