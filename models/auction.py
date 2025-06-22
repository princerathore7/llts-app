from datetime import datetime

class Auction:
    def __init__(self, item_name, title, description, starting_bid, base_price, location, condition, end_date, created_by):
        self.item_name = item_name
        self.title = title
        self.description = description
        self.starting_bid = starting_bid
        self.base_price = base_price
        self.location = location
        self.condition = condition
        self.end_date = end_date
        self.date_posted = datetime.utcnow()
        self.created_by = created_by

    def to_dict(self):
        return {
            "item_name": self.item_name,
            "title": self.title,
            "description": self.description,
            "starting_bid": self.starting_bid,
            "base_price": self.base_price,
            "location": self.location,
            "condition": self.condition,
            "end_date": self.end_date.strftime('%Y-%m-%d'),
            "date_posted": self.date_posted.strftime('%Y-%m-%d'),
            "created_by": self.created_by
        }
