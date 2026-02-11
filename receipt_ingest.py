from bs4 import BeautifulSoup
from inventory_manager import InventoryManager
import os

class ReceiptParser:
    def __init__(self):
        self.inventory = InventoryManager()

    def parse_file(self, filename):
        if not os.path.exists(filename):
            print(f"❌ Error: File '{filename}' not found.")
            return

        print(f"--- 📧 Processing Receipt: {filename} ---")
        with open(filename, 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')

        items = soup.find_all('tr', class_='item-row')

        for item in items:
            raw_name = item.find('td', class_='name').text
            # Send raw text to manager; logic handles cleaning/detecting frozen
            self.inventory.add_item(raw_name, quantity=1)

if __name__ == "__main__":
    parser = ReceiptParser()
    parser.parse_file("email_receipt.html")