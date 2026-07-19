from models.mongo_activity import Activity
from models.mongo_activity_read import ActivityRead
from mongoengine import Q


def _extract_id(act_dict: dict) -> str:
    """Extract string _id from a to_dict() result."""
    raw = act_dict.get("_id")
    if isinstance(raw, dict):
        return raw.get("$oid", str(raw))
    return str(raw) if raw else ""


class ActivityDatabase:
    @staticmethod
    def upsert_activity(data: dict) -> tuple:
        """Upsert activity. Returns (activity, is_new). is_new=True on first insert."""
        tx_hash = data.get("transaction_hash")
        act_type = data.get("activity_type")
        wallet = data.get("wallet_address")
        details = data.get("details")
        activity = Activity.objects(
            transaction_hash=tx_hash,
            wallet_address=wallet,
            activity_type=act_type,
            details=details,
        ).first()
        is_new = activity is None
        if not activity:
            activity = Activity(**data)
        else:
            for k, v in data.items():
                setattr(activity, k, v)
        activity.save()
        return activity, is_new

    # ------------------------------------------------------------------
    # Read-status helpers (per-user, stored in activity_reads collection)
    # ------------------------------------------------------------------

    @staticmethod
    def mark_read(activity_id: str, wallet_address: str):
        """Mark a single activity as read for a specific wallet."""
        existing = ActivityRead.objects(
            activity_id=activity_id, wallet_address=wallet_address
        ).first()
        if not existing:
            ActivityRead(activity_id=activity_id, wallet_address=wallet_address).save()

    @staticmethod
    def get_read_ids(wallet_address: str) -> set:
        """Return a set of activity_ids already read by this wallet."""
        reads = ActivityRead.objects(wallet_address=wallet_address).only("activity_id")
        return {r.activity_id for r in reads}

    @staticmethod
    def mark_all_read_for_wallet(wallet_address: str, activity_ids: list):
        """Bulk-mark a list of activity_ids as read for a wallet."""
        already_read = ActivityDatabase.get_read_ids(wallet_address)
        to_insert = [
            ActivityRead(activity_id=aid, wallet_address=wallet_address)
            for aid in activity_ids
            if aid not in already_read
        ]
        if to_insert:
            ActivityRead.objects.insert(to_insert, load_bulk=False)
        return len(to_insert)

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    @staticmethod
    def get_activities(wallet_address: str, limit: int = 50, category: str = None):
        base_query = Q(wallet_address=wallet_address) | Q(to_address=wallet_address)

        if category == "System":
            query = Q(activity_type="Deposit Liquidity")
        elif category and category not in ("All Notification",):
            if category == "Transfer":
                query = base_query & Q(activity_type__in=["Sent token", "Received token"])
            elif category == "Swap":
                query = base_query & Q(activity_type="Swap token")
            elif category == "Rewards":
                query = base_query & Q(activity_type__icontains="Reward")
            elif category == "Rooms":
                query = base_query & Q(activity_type__icontains="Room")
            else:
                query = base_query
        else:
            # All Notification or no category: all personal activities + Deposit Liquidity
            query = base_query | Q(activity_type="Deposit Liquidity")

        activities = Activity.objects(query).order_by("-datetime").limit(limit)
        return [act.to_dict() for act in activities]

    @staticmethod
    def get_public_room_created(limit: int = 50):
        """Return all 'Created Room' activities (public broadcast, any creator)."""
        activities = Activity.objects(activity_type="Created Room").order_by("-datetime").limit(limit)
        return [act.to_dict() for act in activities]

    @staticmethod
    def get_room_activities(room_id: int, limit: int = 100):
        """Return activity feed for a specific room (Joined Room, Left Room, Claimed Reward)."""
        ROOM_ACTIVITY_TYPES = ["Joined Room", "Left Room", "Claimed Reward", "Completed Room"]
        activities = Activity.objects(
            room_id=room_id,
            activity_type__in=ROOM_ACTIVITY_TYPES
        ).order_by("-datetime").limit(limit)
        return [act.to_dict() for act in activities]

    @staticmethod
    def get_public_token_listings(limit: int = 50):
        """Return all token listing activities (Add Token) visible to everyone."""
        activities = Activity.objects(activity_type__in=["Add Token"]).order_by("-datetime").limit(limit)
        return [act.to_dict() for act in activities]

    @staticmethod
    def get_all_public_activities(limit: int = 50):
        """Return all public activities (Created Room, Add Token, Completed Room)."""
        activities = Activity.objects(
            activity_type__in=["Created Room", "Add Token", "Completed Room"]
        ).order_by("-datetime").limit(limit)
        return [act.to_dict() for act in activities]

    # ------------------------------------------------------------------
    # Kept for backward compatibility – now delegates to per-user table
    # ------------------------------------------------------------------

    @staticmethod
    def mark_all_read(wallet_address: str, category: str = None):
        """Mark all matching activities as read for the given wallet (per-user table)."""
        base_query = Q(wallet_address=wallet_address) | Q(to_address=wallet_address)

        if category == "System":
            query = Q(activity_type="Deposit Liquidity")
        elif category and category != "All Notification":
            if category == "Transfer":
                query = base_query & Q(activity_type__in=["Sent token", "Received token"])
            elif category == "Swap":
                query = base_query & Q(activity_type="Swap token")
            elif category == "Rewards":
                query = base_query & Q(activity_type__icontains="Reward")
            elif category == "Rooms":
                query = base_query & Q(activity_type__icontains="Room")
            else:
                query = base_query
        else:
            query = base_query | Q(activity_type="Deposit Liquidity")

        activities = Activity.objects(query).order_by("-datetime")
        activity_ids = [_extract_id(a.to_dict()) for a in activities]
        return ActivityDatabase.mark_all_read_for_wallet(wallet_address, activity_ids)
