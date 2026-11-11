from app.main import fallback_analysis

def test_billing_message_is_classified():
    category, priority, _ = fallback_analysis("I need a refund for a payment")
    assert category == "Billing"
    assert priority == "Normal"

def test_urgent_message_is_high_priority():
    _, priority, _ = fallback_analysis("Urgent, I cannot access my account")
    assert priority == "High"
