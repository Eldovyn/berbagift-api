from mongoengine import StringField, IntField
from models.mongo_base import TimestampedDocument

class IndexerState(TimestampedDocument):
    state_id = StringField(primary_key=True)
    last_ledger_processed = IntField(default=0)
    meta = {'collection': 'indexer_state'}
