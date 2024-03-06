from flask.json import JSONEncoder
from decimal import Decimal

class CustomJSONEncoder(JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode decimal types.
    """
    def default(self, obj):
        if isinstance(obj, Decimal):
            # Decimals are not serializable by default, convert to float.
            return float(obj)
        # Delegate the serialization of other types to the base class method.
        return super().default(obj)



def calculate_salmon_box(amount, threshold=2):
    full_box, half_box = 0, 0
    # Convert amount to a float for simplicity
    amount = float(amount)
    if amount <= 0:
        full_box, half_box = 0, 0

    if amount < 10:
        full_box, half_box = 0, 1
    
    if amount == 10:
        full_box, half_box = 1, 0
    
    # Check if amount is divisible by 10
    if amount % 10 == 0:
        full_box, half_box = amount / 10, 0
    
    # If not divisible by 10, check the threshold
    lower_bound = amount - (amount % 10)  # Lower multiple of 10
    if (amount - lower_bound) <= threshold:
        full_box, half_box = lower_bound / 10, 0
    else:
        full_box, half_box = lower_bound / 10, 1

    return [int(full_box), int(half_box)]