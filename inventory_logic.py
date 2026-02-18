import json
import datetime
from datetime import timedelta

class InventoryLogic:
    def __init__(self):
        try:
            with open('defaults.json', 'r') as f:
                self.rules = json.load(f)
        except FileNotFoundError:
            self.rules = {}

    def normalize_item(self, raw_name):
        """
        Takes raw string (e.g. "Kroger Frozen Spinach") and returns structured data.
        """
        raw_name = raw_name.lower()
        
        # 1. Detect Storage Type
        storage_type = "fresh"
        if "frozen" in raw_name:
            storage_type = "frozen"
        
        # 2. Identify Core Item
        matched_key = None
        for key in sorted(self.rules, key=len, reverse=True):
            if key in raw_name:
                matched_key = key
                break
        
        # 3. Apply Rules
        if matched_key:
            rule = self.rules[matched_key]
            
            # PANTRY LOGIC: Override storage if category implies it
            if rule['category'] in ['Pantry', 'Canned', 'Dry']:
                storage_type = 'pantry'

            # CALCULATE EXPIRY
            if storage_type == "frozen" and rule.get('frozen_expiry_days'):
                days = rule['frozen_expiry_days']
                reason = f"Matched '{matched_key}' + detected 'frozen'"
            elif storage_type == 'pantry':
                days = rule['expiry_days']
                reason = f"Matched '{matched_key}' (Pantry Item)"
            else:
                days = rule['expiry_days']
                reason = f"Matched '{matched_key}' (Default Fresh)"
                
            return {
                "clean_name": matched_key,
                "category": rule['category'],
                "unit": rule['unit'],         
                "storage": storage_type,      
                "expiry_days": days,
                "reason": reason
            }
        else:
            # Fallback for unknown items
            return {
                "clean_name": raw_name,
                "category": "Unsorted",
                "unit": "unit",
                "storage": storage_type,
                "expiry_days": 7,
                "reason": "Unknown item (Safety Default)"
            }
