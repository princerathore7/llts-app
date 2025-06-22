from mongoengine import Document, StringField, EmailField, DateTimeField, ListField

class User(Document):
    name = StringField(required=True)
    username = StringField(required=True, unique=True)
    email = EmailField(required=True, unique=True)
    password = StringField(required=True)
    role = StringField(required=True, choices=["owner", "worker"])
    experience = StringField()
    skills = ListField(StringField())
    created_at = DateTimeField()
