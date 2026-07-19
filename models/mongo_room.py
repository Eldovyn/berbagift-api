from mongoengine import StringField, IntField, BooleanField, ListField
from models.mongo_base import TimestampedDocument

class Room(TimestampedDocument):
    room_id = IntField(required=True)
    owner = StringField(required=True)
    title = StringField(required=True)
    description = StringField(required=True)
    reward = StringField(required=True)
    token_address = StringField(required=True)
    total_winners = IntField(default=1)
    total_joined = IntField(default=0)
    capacity = IntField(default=0)
    status = StringField(default="Active")
    transaction_hash = StringField()
    claim_session_start = IntField(null=True)
    winners = ListField(StringField(), default=list)

    meta = {'collection': 'rooms'}

class RoomParticipant(TimestampedDocument):
    room_id = IntField(required=True)
    wallet_address = StringField(required=True)
    is_joined = BooleanField(default=True)
    is_claimed = BooleanField(default=False)

    meta = {'collection': 'room_participants'}
