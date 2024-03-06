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
