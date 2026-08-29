# Utility Functions - Shared across all modules

def safe_float(value, default=0.0):
    """Safely convert value to float"""
    try:
        if value is None or value == '':
            return default
        return float(str(value).replace('$', '').replace(',', ''))
    except:
        return default


def safe_int(value, default=0):
    """Safely convert value to int"""
    try:
        if value is None or value == '':
            return default
        return int(float(safe_float(value)))
    except:
        return default


def format_currency(value):
    """Format number as currency"""
    try:
        return f"${float(value):,.2f}"
    except:
        return "$0.00"


def format_percentage(value):
    """Format number as percentage"""
    try:
        return f"{float(value):.1f}%"
    except:
        return "0%"


def parse_date_string(date_str, format='%Y-%m-%d'):
    """Parse date string safely"""
    from datetime import datetime
    try:
        if isinstance(date_str, str):
            return datetime.strptime(date_str, format).date()
        return date_str
    except:
        return None


def days_between(date1, date2):
    """Calculate days between two dates"""
    try:
        from datetime import datetime
        if isinstance(date1, str):
            date1 = datetime.strptime(date1, '%Y-%m-%d').date()
        if isinstance(date2, str):
            date2 = datetime.strptime(date2, '%Y-%m-%d').date()
        return abs((date2 - date1).days)
    except:
        return 0


def get_months_list(months=12):
    """Get list of months (for dropdowns)"""
    from datetime import datetime, timedelta
    months_list = []
    today = datetime.now()
    for i in range(months):
        month_date = today - timedelta(days=30*i)
        months_list.append(month_date.strftime('%B %Y'))
    return months_list


def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    try:
        if old_value == 0:
            return 0
        return ((new_value - old_value) / old_value) * 100
    except:
        return 0


def flatten_dict(d, parent_key='', sep='_'):
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst, chunk_size):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def get_or_default(dictionary, key, default=None):
    """Get value from dict with default fallback"""
    try:
        return dictionary.get(key, default)
    except:
        return default


def is_valid_email(email):
    """Check if string looks like email"""
    try:
        return '@' in email and '.' in email.split('@')[1]
    except:
        return False
