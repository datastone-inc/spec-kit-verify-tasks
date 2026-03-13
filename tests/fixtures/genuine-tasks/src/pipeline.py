"""
Processing pipeline — T009.
Chains validate_email and format_currency; imported by src/app.py.
"""
from validator import validate_email
from formatter import format_currency


class Pipeline:
    """Simple data-processing pipeline that validates and formats."""

    def process(self, email: str, amount: float, currency: str = "USD"):
        """Validate email and format the amount. Returns a result dict."""
        return {
            "email_valid": validate_email(email),
            "formatted_amount": format_currency(amount, currency),
        }
