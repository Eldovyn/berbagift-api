from mongoengine import StringField, IntField
from models.mongo_base import TimestampedDocument

class Listing(TimestampedDocument):
    """Dedicated collection for marketplace listings."""
    token_id = IntField(required=True, unique=True)
    token_uri = StringField(required=True)
    transaction_hash = StringField(required=True)
    price = StringField(required=True)
    payment_token = StringField(default="")
    wallet_address = StringField(required=True)  # seller

    meta = {
        'collection': 'listings',
        'indexes': [
            'wallet_address',
            'token_id',
        ]
    }
