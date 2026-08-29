# Configuration & Constants for Health & Wealth Tracker

# ==================== SETTINGS ====================
SETTINGS_HEADERS = [
    'your_salary', 'wife_salary', 'fixed_rent', 'fixed_car_payment', 
    'fixed_car_insurance', 'fixed_health_insurance', 'fixed_mobile', 
    'fixed_utilities', 'fixed_tfsa', 'fixed_rrsp', 'fixed_india_transfer', 
    'fixed_other', 'annual_costco', 'annual_caa', 'annual_car_registration', 
    'annual_gym', 'annual_home_insurance', 'annual_other', 
    'annual_monthly_equivalent', 'tfsa_rrsp_start_date'
]

# ==================== BUDGETS ====================
BUDGET_HEADERS = ['Groceries', 'Dining', 'Transportation', 'Entertainment', 'Shopping', 'Healthcare']

# ==================== EXPENSES ====================
EXPENSE_HEADERS = ['merchant', 'date', 'total', 'category', 'items', 'uploaded_at']

EXPENSE_CATEGORIES = [
    'Groceries', 'Dining Out', 'Gas', 'Transportation', 'Shopping', 
    'Entertainment', 'Healthcare', 'Utilities', 'Rent/Mortgage', 'Insurance', 
    'Phone/Internet', 'Gym/Fitness', 'Subscriptions', 'Travel', 'Other'
]

# ==================== DEBTS ====================
DEBT_HEADERS = ['name', 'principal', 'monthly_payment', 'interest_rate', 'months_to_payoff', 'created_date']

# ==================== HEALTH ====================
HEALTH_HEADERS = ['date', 'metric', 'value', 'unit', 'normal_range', 'type', 'person', 'added_at']

# ==================== WELLNESS LOG ====================
WELLNESS_HEADERS = [
    'date', 'person', 'exercise', 'exercise_name', 'water', 'pee_count', 
    'poop_count', 'sleep', 'mood', 'stress', 'symptoms', 'medications', 
    'steps', 'diet_notes', 'notes'
]

# ==================== NUTRITION ====================
NUTRITION_MEALS_HEADERS = [
    'date', 'person', 'meal_type', 'description', 'time', 'comfort_score', 
    'protein_g', 'carbs_g', 'fat_g', 'fiber_g', 'calories', 'notes'
]

# ==================== FERTILITY ====================
FERTILITY_HEADERS = [
    'date_start', 'date_end', 'cycle_length', 'cervical_fluid', 
    'temperature', 'symptoms', 'notes', 'added_at'
]

# ==================== SHOPPING ====================
PRICE_HISTORY_HEADERS = ['date', 'store', 'product', 'quantity', 'price', 'uploaded_at']

# ==================== RECIPES DATABASE ====================
RECIPES = {
    "Breakfast": {
        "Eggs & Toast": {"protein": 12, "carbs": 30, "fat": 8, "fiber": 3, "cal": 250},
        "Oatmeal + Berries": {"protein": 8, "carbs": 45, "fat": 4, "fiber": 8, "cal": 280},
        "Yogurt Parfait": {"protein": 15, "carbs": 40, "fat": 5, "fiber": 4, "cal": 300},
    },
    "Lunch": {
        "Chicken Sandwich": {"protein": 25, "carbs": 35, "fat": 10, "fiber": 3, "cal": 400},
        "Tuna Salad": {"protein": 20, "carbs": 15, "fat": 8, "fiber": 4, "cal": 280},
        "Rice & Curry": {"protein": 15, "carbs": 60, "fat": 8, "fiber": 4, "cal": 450},
    },
    "Dinner": {
        "Grilled Chicken + Veggies": {"protein": 35, "carbs": 25, "fat": 8, "fiber": 5, "cal": 420},
        "Fish + Rice": {"protein": 30, "carbs": 45, "fat": 6, "fiber": 3, "cal": 480},
    }
}

# ==================== RESTAURANTS DATABASE ====================
RESTAURANTS = {
    "McDonald's": {
        "Big Mac": {"protein": 25, "carbs": 45, "fat": 30, "fiber": 2, "cal": 550},
    },
    "Subway": {
        '6" Turkey': {"protein": 18, "carbs": 45, "fat": 5, "fiber": 4, "cal": 320},
    },
    "Chipotle": {
        "Chicken Bowl": {"protein": 30, "carbs": 60, "fat": 15, "fiber": 12, "cal": 520},
    }
}

# ==================== NUTRITION GOALS ====================
NUTRITION_GOALS = {
    "calories": (1800, 2200),
    "protein_g": (60, 70),
    "carbs_g": (200, 250),
    "fat_g": (60, 75),
    "fiber_g": (25, 30),
}

# ==================== APP CONFIG ====================
APP_TITLE = "💰 Health & Wealth Tracker"
APP_ICON = "💎"
LAYOUT = "wide"

# Users
USERS = ["Govind", "Amrithavarshini"]

# Tabs order
MAIN_TABS = [
    "⚙️ Setup", 
    "💳 Debts", 
    "💰 Spending", 
    "🛒 Shopping Analytics", 
    "📊 Wealth", 
    "🏥 Health", 
    "🏋️ Fitness Plan", 
    "✅ Daily Wellness Log", 
    "🍽️ Nutrition Tracker", 
    "👶 Fertility Tracker", 
    "🥗 Smart Grocery", 
    "🎯 Budgets"
]
