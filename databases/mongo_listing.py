from models.mongo_listing import Listing


class ListingDatabase:
    @staticmethod
    def upsert_listing(data: dict):
        token_id = data.get("token_id")
        listing = Listing.objects(token_id=token_id).first()
        if not listing:
            listing = Listing(**data)
        else:
            for k, v in data.items():
                setattr(listing, k, v)
        listing.save()
        return listing

    @staticmethod
    def remove_listing(token_id: int):
        Listing.objects(token_id=token_id).delete()
        return True

    @staticmethod
    def get_listed_nfts(limit: int = 50):
        listings = Listing.objects().order_by("-created_at").limit(limit)
        return [l.to_dict() for l in listings]

    @staticmethod
    def get_listing_by_token_id(token_id: int):
        listing = Listing.objects(token_id=token_id).first()
        return listing.to_dict() if listing else None

    @staticmethod
    def get_user_listings(wallet_address: str, limit: int = 50):
        listings = (
            Listing.objects(wallet_address=wallet_address)
            .order_by("-created_at")
            .limit(limit)
        )
        return [l.to_dict() for l in listings]
