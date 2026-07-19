from mongoengine import StringField, IntField, DateTimeField, BooleanField
from models.mongo_base import TimestampedDocument

class NFT(TimestampedDocument):
    token_id = IntField(required=True, unique=True)
    contract_id = StringField(required=True)
    owner_address = StringField(required=True)
    sender_address = StringField(required=True)
    token_uri = StringField(required=True)
    message = StringField(default="")
    token_used = StringField(null=True)
    token_amount = StringField(null=True)
    is_listed = BooleanField(default=False)
    is_purchased = BooleanField(default=False)
    price = StringField(null=True)
    datetime = DateTimeField(required=True)
    transaction_hash = StringField(default="")

    meta = {
        'collection': 'nfts',
        'indexes': [
            'owner_address',
            'token_id'
        ]
    }
