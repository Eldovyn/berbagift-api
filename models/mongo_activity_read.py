from mongoengine import StringField
from models.mongo_base import TimestampedDocument

class ActivityRead(TimestampedDocument):
    """
    Tracks which activities have been read by which user.
    Replaces the is_read flag on the Activity document for multi-user support.
    """
    activity_id = StringField(required=True)    # Activity._id as string
    wallet_address = StringField(required=True)  # who read it

    meta = {
        'collection': 'activity_reads',
        'indexes': [
            {'fields': ['activity_id', 'wallet_address'], 'unique': True},
            'wallet_address',
        ]
    }
