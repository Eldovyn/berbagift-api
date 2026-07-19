from mongoengine import StringField, BooleanField
from models.mongo_base import TimestampedDocument

class RegistryToken(TimestampedDocument):
    token_address = StringField(required=True, unique=True)
    symbol = StringField(default="Token")
    is_active = BooleanField(default=True)

    meta = {
        'collection': 'registry_tokens',
        'indexes': [
            'token_address',
            'is_active'
        ]
    }
