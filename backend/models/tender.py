from datetime import datetime

class Tender:
    def __init__(self, title, description, location, condition, budget, category, deadline, created_by):
        self.title = title
        self.description = description
        self.location = location
        self.condition = condition
        self.budget = budget
        self.category = category
        self.deadline = deadline
        self.date_posted = datetime.utcnow()
        self.created_by = created_by

    def to_dict(self):
        return {
            "title": self.title,
            "description": self.description,
            "location": self.location,
            "condition": self.condition,
            "budget": self.budget,
            "category": self.category,
            "deadline": self.deadline.strftime('%Y-%m-%d'),
            "date_posted": self.date_posted.strftime('%Y-%m-%d'),
            "created_by": self.created_by
        }
