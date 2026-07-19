import datetime
from mongoengine import Document, DateTimeField

class TimestampedDocument(Document):
    meta = {'abstract': True}
    
    created_at = DateTimeField(default=datetime.datetime.utcnow)
    updated_at = DateTimeField(default=datetime.datetime.utcnow)
    deleted_at = DateTimeField(null=True)

    def save(self, *args, **kwargs):
        self.updated_at = datetime.datetime.utcnow()
        return super().save(*args, **kwargs)

    def to_dict(self):
        import json
        data = json.loads(self.to_json())
        
        for key, value in data.items():
            if isinstance(value, dict):
                if '$date' in value:
                    date_val = value['$date']
                    if isinstance(date_val, (int, float)):
                        from datetime import datetime, timezone
                        data[key] = datetime.fromtimestamp(date_val / 1000.0, tz=timezone.utc).isoformat()
                    else:
                        data[key] = date_val
                elif '$oid' in value:
                    data[key] = value['$oid']
                    
        return data
