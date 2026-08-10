#!/usr/bin/env python3
"""
Smart Budget Tracker AI
========================

Personal finance AI that:
1. Extracts expense details from receipt photos (Vision API)
2. Categorizes spending automatically
3. Analyzes spending patterns
4. Predicts future spending
5. Provides smart recommendations

Author: Govind Raj
"""

import os
import json
import base64
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple
import anthropic
from collections import defaultdict


class ReceiptProcessor:
    """Process receipt images and extract expense details using Claude Vision."""
    
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))
    
    def extract_from_image(self, image_path: str) -> Dict:
        """Extract receipt details from image using Claude Vision."""
        print(f"📸 Processing receipt: {image_path}")
        
        # Read and encode image
        with open(image_path, "rb") as f:
            image_data = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Determine media type
        suffix = Path(image_path).suffix.lower()
        media_type_map = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp'
        }
        media_type = media_type_map.get(suffix, 'image/jpeg')
        
        prompt = """Extract receipt information. Output ONLY valid JSON.

{
    "merchant": "Store name",
    "date": "YYYY-MM-DD",
    "time": "HH:MM",
    "items": [
        {"name": "Item name", "quantity": 1, "price": 0.00},
        {"name": "Item name", "quantity": 2, "price": 15.50}
    ],
    "subtotal": 0.00,
    "tax": 0.00,
    "total": 0.00,
    "payment_method": "Card/Cash/etc"
}

Be precise. If information is unclear, use reasonable defaults.
Only output JSON, no other text."""
        
        try:
            message = self.client.messages.create(
                model="claude-opus-4-1",
                max_tokens=1000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_data,
                                },
                            },
                            {
                                "type": "text",
                                "text": prompt
                            }
                        ],
                    }
                ],
            )
            
            response_text = message.content[0].text
            receipt_data = json.loads(response_text)
            print(f"✅ Extracted: {receipt_data.get('merchant', 'Unknown')} - ${receipt_data.get('total', 0):.2f}")
            return receipt_data
            
        except json.JSONDecodeError:
            print(f"⚠️  Failed to parse receipt. Using fallback.")
            return {
                "merchant": "Unknown",
                "date": datetime.now().strftime("%Y-%m-%d"),
                "items": [],
                "total": 0.00
            }
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            return None


class ExpenseAnalyzer:
    """Analyze spending patterns, trends, and generate recommendations."""
    
    def __init__(self, api_key: str = None):
        self.client = anthropic.Anthropic(api_key=api_key or os.environ.get('ANTHROPIC_API_KEY'))
    
    def categorize_expense(self, receipt: Dict) -> str:
        """Categorize expense based on merchant and items."""
        merchant = receipt.get('merchant', '').lower()
        items = [item.get('name', '').lower() for item in receipt.get('items', [])]
        items_text = ', '.join(items[:3])
        
        prompt = f"""Categorize this expense into ONE category.

Merchant: {merchant}
Items: {items_text}

Choose from:
- Groceries (supermarket, farmers market, food stores)
- Dining (restaurants, cafes, food delivery)
- Transportation (gas, uber, transit, parking)
- Utilities (electric, water, internet)
- Entertainment (movies, games, hobbies)
- Shopping (clothes, home, general retail)
- Healthcare (pharmacy, doctor, medical)
- Other

Output ONLY the category name, nothing else."""
        
        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}]
            )
            category = message.content[0].text.strip()
            return category if any(cat in category for cat in ['Groceries', 'Dining', 'Transportation', 'Utilities', 'Entertainment', 'Shopping', 'Healthcare', 'Other']) else 'Other'
        except:
            return 'Other'
    
    def analyze_spending_data(self, expenses: List[Dict]) -> Dict:
        """Analyze spending patterns from expense data."""
        if not expenses:
            return {"message": "No expense data yet"}
        
        # Calculate metrics
        total_spent = sum(e.get('total', 0) for e in expenses)
        num_expenses = len(expenses)
        avg_expense = total_spent / num_expenses if num_expenses > 0 else 0
        
        # Category breakdown
        categories = defaultdict(float)
        for exp in expenses:
            category = exp.get('category', 'Other')
            categories[category] += exp.get('total', 0)
        
        # Find highest and lowest
        highest_category = max(categories, key=categories.get) if categories else 'N/A'
        highest_amount = categories.get(highest_category, 0) if categories else 0
        
        # Calculate days
        if len(expenses) > 1:
            dates = [exp.get('date') for exp in expenses if exp.get('date')]
            if dates:
                days_span = (datetime.strptime(max(dates), '%Y-%m-%d') - 
                            datetime.strptime(min(dates), '%Y-%m-%d')).days + 1
            else:
                days_span = 1
        else:
            days_span = 1
        
        daily_avg = total_spent / days_span if days_span > 0 else 0
        
        return {
            'total_spent': round(total_spent, 2),
            'num_expenses': num_expenses,
            'avg_expense': round(avg_expense, 2),
            'daily_average': round(daily_avg, 2),
            'categories': {k: round(v, 2) for k, v in sorted(categories.items(), key=lambda x: x[1], reverse=True)},
            'highest_category': highest_category,
            'highest_amount': round(highest_amount, 2),
            'days_span': days_span
        }
    
    def generate_recommendations(self, analysis: Dict, expenses: List[Dict]) -> List[str]:
        """Generate smart spending recommendations using Claude."""
        if not expenses or not analysis:
            return ["Start tracking expenses to get personalized recommendations!"]
        
        # Prepare data for Claude
        categories_summary = '\n'.join([f"- {cat}: ${amt:.2f}" for cat, amt in analysis.get('categories', {}).items()])
        
        prompt = f"""Based on this spending analysis, provide 3-4 specific, actionable recommendations.

Spending Summary:
- Total spent: ${analysis.get('total_spent', 0):.2f}
- Number of transactions: {analysis.get('num_expenses', 0)}
- Average expense: ${analysis.get('avg_expense', 0):.2f}
- Daily average: ${analysis.get('daily_average', 0):.2f}

Category Breakdown:
{categories_summary}

Generate 3-4 specific recommendations to save money or improve spending habits.
Format as bullet points. Be practical and actionable."""
        
        try:
            message = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            text = message.content[0].text
            recommendations = [line.strip() for line in text.split('\n') if line.strip().startswith('-') or line.strip().startswith('•')]
            return recommendations[:4] if recommendations else ["Keep tracking to get better insights!"]
        except:
            return ["Continue logging expenses for personalized insights!"]
    
    def predict_monthly_spending(self, expenses: List[Dict]) -> Dict:
        """Predict future monthly spending based on trends."""
        if not expenses:
            return {"message": "Not enough data to predict"}
        
        analysis = self.analyze_spending_data(expenses)
        daily_avg = analysis.get('daily_average', 0)
        
        # Simple prediction: daily average * 30 days
        predicted_month = daily_avg * 30
        
        # Calculate category predictions
        category_predictions = {}
        for category, amount in analysis.get('categories', {}).items():
            daily_cat_avg = amount / analysis.get('days_span', 1)
            monthly_cat_pred = daily_cat_avg * 30
            category_predictions[category] = round(monthly_cat_pred, 2)
        
        return {
            'predicted_monthly_total': round(predicted_month, 2),
            'category_predictions': category_predictions,
            'confidence': 'Medium' if len(expenses) >= 5 else 'Low',
            'data_points': len(expenses),
            'note': 'Based on current spending rate'
        }
    
    def detect_anomalies(self, expenses: List[Dict], analysis: Dict) -> List[Dict]:
        """Detect unusual spending patterns."""
        anomalies = []
        
        if not expenses or not analysis:
            return anomalies
        
        avg_expense = analysis.get('avg_expense', 0)
        
        for exp in expenses[-10:]:  # Check last 10
            amount = exp.get('total', 0)
            merchant = exp.get('merchant', 'Unknown')
            
            # Flag if 2x average
            if amount > avg_expense * 2:
                anomalies.append({
                    'date': exp.get('date'),
                    'merchant': merchant,
                    'amount': amount,
                    'reason': f"High spend (${amount:.2f} vs avg ${avg_expense:.2f})"
                })
        
        return anomalies


class BudgetTracker:
    """Main budget tracker coordinator."""
    
    def __init__(self):
        self.processor = ReceiptProcessor()
        self.analyzer = ExpenseAnalyzer()
        self.expenses = []
    
    def process_receipt(self, image_path: str) -> bool:
        """Process receipt image and add to expense list."""
        receipt = self.processor.extract_from_image(image_path)
        if not receipt:
            return False
        
        # Categorize
        category = self.analyzer.categorize_expense(receipt)
        receipt['category'] = category
        receipt['processed_date'] = datetime.now().isoformat()
        
        self.expenses.append(receipt)
        return True
    
    def get_summary(self) -> Dict:
        """Get complete spending summary with analysis."""
        analysis = self.analyzer.analyze_spending_data(self.expenses)
        predictions = self.analyzer.predict_monthly_spending(self.expenses)
        recommendations = self.analyzer.generate_recommendations(analysis, self.expenses)
        anomalies = self.analyzer.detect_anomalies(self.expenses, analysis)
        
        return {
            'analysis': analysis,
            'predictions': predictions,
            'recommendations': recommendations,
            'anomalies': anomalies,
            'generated_at': datetime.now().isoformat()
        }
    
    def save_to_file(self, filename: str = None):
        """Save expenses and summary to JSON file."""
        if not filename:
            filename = f"budget_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        summary = self.get_summary()
        summary['expenses'] = self.expenses
        
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2)
        
        print(f"✅ Saved to {filename}")
        return filename


def main():
    """Demo mode with sample data."""
    print("=" * 70)
    print("Smart Budget Tracker AI")
    print("=" * 70)
    
    tracker = BudgetTracker()
    
    # Sample expenses for demo
    sample_expenses = [
        {
            "merchant": "Whole Foods Market",
            "date": "2026-08-08",
            "items": [
                {"name": "Organic Milk", "quantity": 1, "price": 5.99},
                {"name": "Chicken Breast", "quantity": 2, "price": 12.99},
                {"name": "Vegetables Bundle", "quantity": 1, "price": 8.50}
            ],
            "total": 27.48
        },
        {
            "merchant": "Chipotle Mexican Grill",
            "date": "2026-08-07",
            "items": [
                {"name": "Chicken Burrito Bowl", "quantity": 1, "price": 9.50},
                {"name": "Guacamole", "quantity": 1, "price": 2.75}
            ],
            "total": 12.25
        },
        {
            "merchant": "Shell Gas Station",
            "date": "2026-08-06",
            "items": [
                {"name": "Gasoline (35 gal)", "quantity": 1, "price": 52.50}
            ],
            "total": 52.50
        },
        {
            "merchant": "Target",
            "date": "2026-08-05",
            "items": [
                {"name": "Shirt", "quantity": 2, "price": 19.99},
                {"name": "Socks 6-pack", "quantity": 1, "price": 12.00}
            ],
            "total": 51.98
        },
        {
            "merchant": "Starbucks",
            "date": "2026-08-04",
            "items": [
                {"name": "Latte", "quantity": 2, "price": 5.75}
            ],
            "total": 11.50
        }
    ]
    
    # Categorize sample expenses
    print("\n📊 Processing sample expenses...\n")
    for exp in sample_expenses:
        category = tracker.analyzer.categorize_expense(exp)
        exp['category'] = category
        tracker.expenses.append(exp)
        print(f"✅ {exp['merchant']}: ${exp['total']:.2f} ({category})")
    
    # Generate summary
    print("\n" + "=" * 70)
    print("SPENDING SUMMARY")
    print("=" * 70)
    
    summary = tracker.get_summary()
    
    # Display analysis
    analysis = summary['analysis']
    print(f"\n📈 Analysis:")
    print(f"  Total Spent: ${analysis['total_spent']:.2f}")
    print(f"  Number of Purchases: {analysis['num_expenses']}")
    print(f"  Average Purchase: ${analysis['avg_expense']:.2f}")
    print(f"  Daily Average: ${analysis['daily_average']:.2f}")
    
    # Display categories
    print(f"\n🏷️  Category Breakdown:")
    for cat, amt in analysis['categories'].items():
        pct = (amt / analysis['total_spent'] * 100) if analysis['total_spent'] > 0 else 0
        print(f"  {cat}: ${amt:.2f} ({pct:.1f}%)")
    
    # Display predictions
    print(f"\n🔮 Predictions:")
    pred = summary['predictions']
    print(f"  Predicted Monthly Total: ${pred['predicted_monthly_total']:.2f}")
    print(f"  Confidence: {pred['confidence']}")
    
    # Display recommendations
    print(f"\n💡 Recommendations:")
    for i, rec in enumerate(summary['recommendations'], 1):
        print(f"  {i}. {rec}")
    
    # Display anomalies
    if summary['anomalies']:
        print(f"\n⚠️  Anomalies Detected:")
        for anomaly in summary['anomalies']:
            print(f"  {anomaly['date']}: {anomaly['merchant']} - {anomaly['reason']}")
    
    # Save summary
    output_file = tracker.save_to_file()
    
    print("\n" + "=" * 70)
    print(f"✅ Demo complete! Summary saved to: {output_file}")
    print("=" * 70)


if __name__ == "__main__":
    main()
