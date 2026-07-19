from fastapi import APIRouter, Query, HTTPException, Depends
from sqlalchemy.orm import Session
from schemas.response import APIResponse
from databases.mongo_nft import NFTDatabase
from databases.mongo_listing import ListingDatabase
from databases.user import UserDatabase
from databases.connection import get_db_session

router = APIRouter(prefix="/api/nfts", tags=["NFT"])

@router.get("/marketplace", response_model=APIResponse)
async def get_marketplace_nfts(
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db_session)
):
    try:
        listings = ListingDatabase.get_listed_nfts(limit)
        user_db = UserDatabase(db)

        enriched = []
        for listing in listings:
            owner_wallet = listing.get("wallet_address")
            if owner_wallet:
                user = user_db.get_user_by_wallet(owner_wallet)
                if user and user.username:
                    listing["owner_username"] = f"@{user.username}"
                else:
                    listing["owner_username"] = f"{owner_wallet[:4]}...{owner_wallet[-4:]}"

            # Merge in message from NFT document
            token_id = listing.get("token_id")
            if token_id:
                nft_doc = NFTDatabase.get_nft_by_token_id(token_id)
                if nft_doc:
                    listing["message"] = nft_doc.get("message", "")
                    listing["sender_address"] = nft_doc.get("sender_address", "")

            enriched.append(listing)

        return {
            "message": "Berhasil mendapatkan daftar NFT Marketplace",
            "data": enriched,
            "errors": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("", response_model=APIResponse)
async def get_user_nfts(
    wallet_address: str = Query(..., description="Wallet address to fetch NFTs for"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db_session)
):
    try:
        nfts = NFTDatabase.get_user_nfts(wallet_address, limit)
        user_db = UserDatabase(db)

        for nft in nfts:
            sender_wallet = nft.get("sender_address")
            if sender_wallet:
                user = user_db.get_user_by_wallet(sender_wallet)
                if user and user.username:
                    nft["sender_username"] = f"@{user.username}"
                else:
                    nft["sender_username"] = f"{sender_wallet[:4]}...{sender_wallet[-4:]}"

        return {
            "message": "Berhasil mendapatkan daftar NFT",
            "data": nfts,
            "errors": None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
