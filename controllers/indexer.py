import time
import os
import traceback
import requests
from datetime import datetime, timezone
from stellar_sdk import SorobanServer
from stellar_sdk.xdr import SCVal

from databases.mongo_state import StateDatabase
from databases.mongo_activity import ActivityDatabase
from databases.mongo_nft import NFTDatabase
from databases.mongo_room import RoomDatabase
from databases.mongo_registry import RegistryDatabase
from databases.mongo_listing import ListingDatabase
from utils.scval import scval_to_native
from services.socket_manager import emit_threadsafe

TOKEN_MAP = {
    "CAXMJUKELFC7THVUKVH4NA5RYUDLORCKSZ5HTOPOMEXRMZJLFHKZJCQZ": "RPK",
    "CDLZFC3SYJYDZT7K67VZ75HPJVIEUVNIXF47ZG2FB2RMQQVU2HHGCYSC": "XLM"
}

def format_amount(amount_stroops: int) -> str:
    amount = amount_stroops / 10000000
    if amount == int(amount):
        return f"{int(amount):,}"
    else:
        formatted = f"{amount:,.7f}".rstrip('0')
        if formatted.endswith('.'):
            formatted = formatted[:-1]
        return formatted

class IndexerController:
    def __init__(self):
        RPC_URL = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org")
        self.server = SorobanServer(RPC_URL)
        self.swap_contract_id = os.getenv("SWAP_CONTRACT_ID", "CCINFSQEIMF2AT5J3KKYFZ6ZAI6DSG5OKJQCHQNKLE7W56LBLSFNAYNZ")
        self.gift_contract_id = os.getenv("NFT_GIFT_CONTRACT_ID", "CDRUJJ6LXZS445XOKRXVDBTV4J4YHP3INTJB2Z5YKEMF4G2SWHDCPAIA")
        self.marketplace_contract_id = os.getenv("MARKETPLACE_CONTRACT_ID", "CBQUQ4MBD2HFTTR2X6WG6CHTOMPIK72XEQIG4HKUUSMT7F2R3LL64C7R")
        self.multi_room_contract_id = os.getenv("MULTI_ROOM_CONTRACT_ID", "CANYHO2JONDBIKBCL4GCQKI6EFKRSIUMSOI2NYVA725U35JZPE3LIQHE")
        self.registry_contract_id = os.getenv("TOKEN_REGISTRY_CONTRACT_ID", "")

    def process_events(self, contract_id: str, start_ledger: int, latest_ledger: int) -> int:
        if start_ledger == 0:
            start_ledger = max(latest_ledger - 5000, 1)
        elif start_ledger > latest_ledger:
            return start_ledger

        try:
            RPC_URL = os.getenv("SOROBAN_RPC_URL", "https://soroban-testnet.stellar.org")
            payload = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "getEvents",
                "params": {
                    "startLedger": start_ledger,
                    "filters": [{"type": "contract", "contractIds": [contract_id]}],
                    "limit": 100,
                    "pagination": {"limit": 100}
                }
            }
            res = requests.post(RPC_URL, json=payload).json()
            if "error" in res:
                raise Exception(str(res["error"]))
                
            events = res.get("result", {}).get("events", [])
            if not events:
                return latest_ledger + 1
                
            for event in events:
                if event.get("type") != 'contract':
                    continue
                try:
                    topic_xdr = event.get("topic", [])
                    val_obj = event.get("value")
                    value_xdr = val_obj.get("xdr") if isinstance(val_obj, dict) else val_obj
                    if not value_xdr:
                        continue
                        
                    topic_scval = [SCVal.from_xdr(t) for t in topic_xdr]
                    value_scval = SCVal.from_xdr(value_xdr)
                    event_type = scval_to_native(topic_scval[0])
                    tx_hash = event.get("txHash", "")
                    ledger_seq = event.get("ledger", 0)
                    if event_type == "add_token":
                        token_address = scval_to_native(topic_scval[1])
                        token_symbol = TOKEN_MAP.get(token_address, "Token")
                        RegistryDatabase.add_token(token_address, token_symbol)
                        _, is_new = ActivityDatabase.upsert_activity({
                            "transaction_hash": tx_hash,
                            "wallet_address": "System",
                            "activity_type": "Add Token",
                            "from_address": "Admin",
                            "to_address": self.registry_contract_id,
                            "details": f"Added {token_symbol} ({token_address[:4]}...{token_address[-4:]})",
                            "amount": "-",
                            "status": "success",
                            "datetime": datetime.now(timezone.utc).isoformat(),
                            "ledger": ledger_seq
                        })
                        if is_new:
                            emit_threadsafe('activity:new', {
                                "wallet_address": "System",
                                "activity_type": "Add Token",
                                "tx_hash": tx_hash
                            })
                        print(f"✅ Indexed Activity: Added Token {token_symbol} to Registry")

                    elif event_type == "rm_token":
                        token_address = scval_to_native(topic_scval[1])
                        token_symbol = TOKEN_MAP.get(token_address, "Token")
                        RegistryDatabase.remove_token(token_address)
                        _, is_new = ActivityDatabase.upsert_activity({
                            "transaction_hash": tx_hash,
                            "wallet_address": "System",
                            "activity_type": "Remove Token",
                            "from_address": "Admin",
                            "to_address": self.registry_contract_id,
                            "details": f"Removed {token_symbol} ({token_address[:4]}...{token_address[-4:]})",
                            "amount": "-",
                            "status": "success",
                            "datetime": datetime.now(timezone.utc).isoformat(),
                            "ledger": ledger_seq
                        })
                        if is_new:
                            emit_threadsafe('activity:new', {
                                "wallet_address": "System",
                                "activity_type": "Remove Token",
                                "tx_hash": tx_hash
                            })
                        print(f"✅ Indexed Activity: Removed Token {token_symbol} from Registry")
                        
                    elif event_type == "swap_b2t":
                        caller = scval_to_native(topic_scval[1])
                        token_address = scval_to_native(topic_scval[2])
                        token_out_symbol = TOKEN_MAP.get(token_address, "Token")
                        token_in_symbol = "XLM"
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 3:
                            amount_in = scval_to_native(value_scval.vec.sc_vec[0])
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": caller,
                                "activity_type": "Swap token",
                                "from_address": caller,
                                "to_address": self.swap_contract_id,
                                "details": f"{token_in_symbol} to {token_out_symbol}",
                                "amount": f"{format_amount(amount_in)} {token_in_symbol}",
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": caller,
                                    "activity_type": "Swap token",
                                    "tx_hash": tx_hash
                                })
                            print(f"✅ Indexed Activity: Swap token ({token_in_symbol} to {token_out_symbol}) by {caller}")

                    elif event_type == "swap_t2b":
                        caller = scval_to_native(topic_scval[1])
                        token_address = scval_to_native(topic_scval[2])
                        token_in_symbol = TOKEN_MAP.get(token_address, "Token")
                        token_out_symbol = "XLM"
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 3:
                            amount_in = scval_to_native(value_scval.vec.sc_vec[0])
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": caller,
                                "activity_type": "Swap token",
                                "from_address": caller,
                                "to_address": self.swap_contract_id,
                                "details": f"{token_in_symbol} to {token_out_symbol}",
                                "amount": f"{format_amount(amount_in)} {token_in_symbol}",
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": caller,
                                    "activity_type": "Swap token",
                                    "tx_hash": tx_hash
                                })
                            print(f"✅ Indexed Activity: Swap token ({token_in_symbol} to {token_out_symbol}) by {caller}")

                    elif event_type == "swap_t2t":
                        caller = scval_to_native(topic_scval[1])
                        token_in_address = scval_to_native(topic_scval[2])
                        token_out_address = scval_to_native(topic_scval[3])
                        token_in_symbol = TOKEN_MAP.get(token_in_address, "Token")
                        token_out_symbol = TOKEN_MAP.get(token_out_address, "Token")
                        
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 4:
                            amount_in = scval_to_native(value_scval.vec.sc_vec[0])
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": caller,
                                "activity_type": "Swap token",
                                "from_address": caller,
                                "to_address": self.swap_contract_id,
                                "details": f"{token_in_symbol} to {token_out_symbol}",
                                "amount": f"{format_amount(amount_in)} {token_in_symbol}",
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": caller,
                                    "activity_type": "Swap token",
                                    "tx_hash": tx_hash
                                })
                            print(f"✅ Indexed Activity: Swap token ({token_in_symbol} to {token_out_symbol}) by {caller}")

                    elif event_type == "add_liq":
                        caller = scval_to_native(topic_scval[1])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 4:
                            token_addr = scval_to_native(value_scval.vec.sc_vec[0])
                            base_amount = scval_to_native(value_scval.vec.sc_vec[1])
                            token_amount = scval_to_native(value_scval.vec.sc_vec[2])
                            token_symbol = TOKEN_MAP.get(token_addr, "Token")
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": caller,
                                "activity_type": "Deposit Liquidity",
                                "from_address": caller,
                                "to_address": self.swap_contract_id,
                                "details": f"Added by {caller[:4]}...{caller[-4:]}",
                                "amount": f"{format_amount(base_amount)} XLM & {format_amount(token_amount)} {token_symbol}",
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": caller,
                                    "activity_type": "Deposit Liquidity",
                                    "tx_hash": tx_hash
                                })
                            print(f"✅ Indexed Activity: Deposit by {caller}")

                    elif event_type == "BndlSent":
                        sender_addr = scval_to_native(topic_scval[1])
                        recipient_addr = scval_to_native(topic_scval[2])
                        item_id = scval_to_native(topic_scval[3])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 4:
                            token_addr = scval_to_native(value_scval.vec.sc_vec[0])
                            token_amount = scval_to_native(value_scval.vec.sc_vec[1])
                            token_uri = scval_to_native(value_scval.vec.sc_vec[2])
                            user_message = scval_to_native(value_scval.vec.sc_vec[3])
                            token_symbol = TOKEN_MAP.get(token_addr, "Token")
                            formatted_amount = f"{format_amount(token_amount)} {token_symbol}"
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": sender_addr,
                                "activity_type": "Sent token",
                                "from_address": sender_addr,
                                "to_address": recipient_addr,
                                "details": f"To {recipient_addr[:4]}...{recipient_addr[-4:]}",
                                "amount": formatted_amount,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": sender_addr,
                                    "activity_type": "Sent token",
                                    "tx_hash": tx_hash
                                })
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": recipient_addr,
                                "activity_type": "Received token",
                                "from_address": sender_addr,
                                "to_address": recipient_addr,
                                "details": f"From {sender_addr[:4]}...{sender_addr[-4:]}",
                                "amount": formatted_amount,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": recipient_addr,
                                    "activity_type": "Received token",
                                    "tx_hash": tx_hash
                                })
                            
                            NFTDatabase.upsert_nft({
                                "token_id": item_id,
                                "contract_id": contract_id,
                                "owner_address": recipient_addr,
                                "sender_address": sender_addr,
                                "token_uri": token_uri,
                                "message": user_message,
                                "token_used": token_addr,
                                "token_amount": formatted_amount,
                                "is_purchased": False,
                                "datetime": datetime.now(timezone.utc),
                                "transaction_hash": tx_hash
                            })
                            
                            print(f"✅ Indexed Activity: Gift from {sender_addr} to {recipient_addr}")

                    elif event_type == "Transfer":
                        from_addr = scval_to_native(topic_scval[1])
                        to_addr = scval_to_native(topic_scval[2])
                        token_id = scval_to_native(topic_scval[3])
                        # Don't overwrite token_uri — keep the original IPFS metadata
                        NFTDatabase.update_owner(token_id, to_addr, default_uri=None)
                        print(f"✅ Indexed NFT Transfer #{token_id} from {from_addr} to {to_addr}")

                    elif event_type == "Listed":
                        seller = scval_to_native(topic_scval[1])
                        token_id = scval_to_native(topic_scval[2])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 2:
                            payment_token = scval_to_native(value_scval.vec.sc_vec[0])
                            price = scval_to_native(value_scval.vec.sc_vec[1])
                            token_symbol = TOKEN_MAP.get(payment_token, "Token")
                            formatted_price = f"{format_amount(price)} {token_symbol}"
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": seller,
                                "activity_type": "List NFT",
                                "from_address": seller,
                                "to_address": self.marketplace_contract_id,
                                "details": f"NFT #{token_id}",
                                "amount": formatted_price,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": seller,
                                    "activity_type": "List NFT",
                                    "tx_hash": tx_hash
                                })
                            NFTDatabase.set_listing_status(token_id, True, formatted_price)

                            # Also write to dedicated Listing collection
                            from models.mongo_nft import NFT
                            nft_doc = NFT.objects(token_id=token_id).first()
                            token_uri = ""
                            if nft_doc:
                                token_uri = nft_doc.token_uri or ""
                            ListingDatabase.upsert_listing({
                                "token_id": token_id,
                                "token_uri": token_uri,
                                "transaction_hash": tx_hash,
                                "price": formatted_price,
                                "payment_token": token_symbol,
                                "wallet_address": seller,
                            })

                            print(f"✅ Indexed Activity: Listed NFT #{token_id} by {seller}")

                    elif event_type == "Sold":
                        buyer = scval_to_native(topic_scval[1])
                        seller = scval_to_native(topic_scval[2])
                        token_id = scval_to_native(topic_scval[3])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 2:
                            payment_token = scval_to_native(value_scval.vec.sc_vec[0])
                            price = scval_to_native(value_scval.vec.sc_vec[1])
                            token_symbol = TOKEN_MAP.get(payment_token, "Token")
                            formatted_price = f"{format_amount(price)} {token_symbol}"
                            
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": buyer,
                                "activity_type": "Buy NFT",
                                "from_address": buyer,
                                "to_address": seller,
                                "details": f"Bought NFT #{token_id}",
                                "amount": formatted_price,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": buyer,
                                    "activity_type": "Buy NFT",
                                    "tx_hash": tx_hash
                                })
                            
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": seller,
                                "activity_type": "Sell NFT",
                                "from_address": buyer,
                                "to_address": seller,
                                "details": f"Sold NFT #{token_id}",
                                "amount": formatted_price,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": seller,
                                    "activity_type": "Sell NFT",
                                    "tx_hash": tx_hash
                                })
                            
                            NFTDatabase.set_listing_status(token_id, False, None)
                            NFTDatabase.update_owner(token_id, buyer)
                            NFTDatabase.clear_personal_data(token_id)
                            ListingDatabase.remove_listing(token_id)
                            
                            print(f"✅ Indexed Activity: Sold NFT #{token_id} from {seller} to {buyer}")
                    
                    elif event_type == "Canceled":
                        seller = scval_to_native(topic_scval[1])
                        token_id = scval_to_native(topic_scval[2])
                        _, is_new = ActivityDatabase.upsert_activity({
                            "transaction_hash": tx_hash,
                            "wallet_address": seller,
                            "activity_type": "Cancel Listing",
                            "from_address": seller,
                            "to_address": self.marketplace_contract_id,
                            "details": f"NFT #{token_id}",
                            "amount": "-",
                            "status": "success",
                            "datetime": datetime.now(timezone.utc).isoformat(),
                            "ledger": ledger_seq
                        })
                        if is_new:
                            emit_threadsafe('activity:new', {
                                "wallet_address": seller,
                                "activity_type": "Cancel Listing",
                                "tx_hash": tx_hash
                            })
                        NFTDatabase.set_listing_status(token_id, False, None)
                        ListingDatabase.remove_listing(token_id)
                        print(f"✅ Indexed Activity: Canceled NFT #{token_id} by {seller}")

                    elif event_type == "RoomCreated":
                        room_id = scval_to_native(topic_scval[1])
                        if value_scval.vec and len(value_scval.vec.sc_vec) >= 6:
                            admin = scval_to_native(value_scval.vec.sc_vec[0])
                            title = scval_to_native(value_scval.vec.sc_vec[1])
                            description = scval_to_native(value_scval.vec.sc_vec[2])
                            reward = scval_to_native(value_scval.vec.sc_vec[3])
                            token_addr = scval_to_native(value_scval.vec.sc_vec[4])
                            total_winners = scval_to_native(value_scval.vec.sc_vec[5])
                            
                            capacity = 0
                            if len(value_scval.vec.sc_vec) >= 7:
                                capacity = scval_to_native(value_scval.vec.sc_vec[6])
                                
                            claim_session_start = None
                            if len(value_scval.vec.sc_vec) >= 8:
                                claim_session_start = scval_to_native(value_scval.vec.sc_vec[7])
                                
                            token_symbol = TOKEN_MAP.get(token_addr, "Token")
                            formatted_amount = f"{format_amount(reward)} {token_symbol}"
                            
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": admin,
                                "activity_type": "Created Room",
                                "from_address": admin,
                                "to_address": self.multi_room_contract_id,
                                "details": f"Room '{title}' (#{room_id})",
                                "amount": formatted_amount,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": admin,
                                    "activity_type": "Created Room",
                                    "tx_hash": tx_hash
                                })
                            
                            room_data = {
                                "room_id": room_id,
                                "owner": admin,
                                "title": title,
                                "description": description,
                                "reward": formatted_amount,
                                "token_address": token_addr,
                                "total_winners": total_winners,
                                "capacity": capacity,
                                "transaction_hash": tx_hash
                            }
                            if claim_session_start is not None:
                                room_data["claim_session_start"] = claim_session_start
                                
                            RoomDatabase.upsert_room(room_data)
                            
                            print(f"✅ Indexed Activity: Room {room_id} created by {admin}")

                    elif event_type == "UserJoined":
                        room_id = scval_to_native(topic_scval[1])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 2:
                            user = scval_to_native(value_scval.vec.sc_vec[0])
                            total_joined = scval_to_native(value_scval.vec.sc_vec[1])
                        else:
                            user = scval_to_native(value_scval)
                            total_joined = 0
                            
                        RoomDatabase.upsert_room({
                            "room_id": room_id,
                            "total_joined": total_joined
                        })
                        RoomDatabase.upsert_participant(room_id, user)
                        
                        _, is_new = ActivityDatabase.upsert_activity({
                            "transaction_hash": tx_hash,
                            "wallet_address": user,
                            "activity_type": "Joined Room",
                            "from_address": user,
                            "to_address": self.multi_room_contract_id,
                            "details": f"Room #{room_id} (Total: {total_joined})",
                            "amount": "-",
                            "status": "success",
                            "datetime": datetime.now(timezone.utc).isoformat(),
                            "ledger": ledger_seq,
                            "room_id": room_id
                        })
                        if is_new:
                            emit_threadsafe('activity:new', {
                                "wallet_address": user,
                                "activity_type": "Joined Room",
                                "tx_hash": tx_hash
                            })
                        print(f"✅ Indexed Activity: User {user} joined Room {room_id}")

                    elif event_type == "UserLeft":
                        room_id = scval_to_native(topic_scval[1])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 2:
                            user = scval_to_native(value_scval.vec.sc_vec[0])
                            total_joined = scval_to_native(value_scval.vec.sc_vec[1])
                        else:
                            user = scval_to_native(value_scval)
                            total_joined = 0
                            
                        RoomDatabase.upsert_room({
                            "room_id": room_id,
                            "total_joined": total_joined
                        })
                        RoomDatabase.set_participant_left(room_id, user)
                        
                        _, is_new = ActivityDatabase.upsert_activity({
                            "transaction_hash": tx_hash,
                            "wallet_address": user,
                            "activity_type": "Left Room",
                            "from_address": self.multi_room_contract_id,
                            "to_address": user,
                            "details": f"Room #{room_id} (Total: {total_joined})",
                            "amount": "-",
                            "status": "success",
                            "datetime": datetime.now(timezone.utc).isoformat(),
                            "ledger": ledger_seq,
                            "room_id": room_id
                        })
                        if is_new:
                            emit_threadsafe('activity:new', {
                                "wallet_address": user,
                                "activity_type": "Left Room",
                                "tx_hash": tx_hash
                            })
                        print(f"✅ Indexed Activity: User {user} left Room {room_id}")

                    elif event_type == "Completed":
                        room_id = scval_to_native(topic_scval[1])

                        winners = []
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 2:
                            winners_scval = value_scval.vec.sc_vec[1]
                            if winners_scval.vec:
                                for w in winners_scval.vec.sc_vec:
                                    winners.append(scval_to_native(w))

                        RoomDatabase.set_room_winners(room_id, winners)

                        _, is_new = ActivityDatabase.upsert_activity({
                            "transaction_hash": tx_hash,
                            "wallet_address": "System",
                            "activity_type": "Completed Room",
                            "from_address": self.multi_room_contract_id,
                            "to_address": "System",
                            "details": f"Room #{room_id} giveaway has been completed.",
                            "amount": "-",
                            "status": "success",
                            "datetime": datetime.now(timezone.utc).isoformat(),
                            "ledger": ledger_seq,
                            "room_id": room_id
                        })
                        if is_new:
                            emit_threadsafe('activity:new', {
                                "wallet_address": "System",
                                "activity_type": "Completed Room",
                                "tx_hash": tx_hash
                            })
                        
                        print(f"✅ Indexed Activity: Room {room_id} Giveaway Completed — winners: {winners}")

                    elif event_type == "Claimed":
                        room_id = scval_to_native(topic_scval[1])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 2:
                            user = scval_to_native(value_scval.vec.sc_vec[0])
                            
                            RoomDatabase.set_participant_claimed(room_id, user)

                            # Fetch room reward from database
                            reward_amount = "Reward"
                            room_doc = RoomDatabase.get_room_by_id(str(room_id))
                            if room_doc:
                                reward_amount = room_doc.get("reward", "Reward")
                            
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": user,
                                "activity_type": "Claimed Reward",
                                "from_address": self.multi_room_contract_id,
                                "to_address": user,
                                "details": f"Room #{room_id}",
                                "amount": reward_amount,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq,
                                "room_id": room_id
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": user,
                                    "activity_type": "Claimed Reward",
                                    "tx_hash": tx_hash
                                })
                            print(f"✅ Indexed Activity: User {user} claimed reward for Room {room_id}")

                    elif event_type == "FeePaid":
                        payer = scval_to_native(topic_scval[1])
                        platform_wallet = scval_to_native(topic_scval[2])
                        if value_scval.vec and len(value_scval.vec.sc_vec) == 2:
                            token_addr = scval_to_native(value_scval.vec.sc_vec[0])
                            fee_amount = scval_to_native(value_scval.vec.sc_vec[1])
                            token_symbol = TOKEN_MAP.get(token_addr, "Token")
                            formatted_fee = f"{format_amount(fee_amount)} {token_symbol}"
                            
                            contract_name_map = {
                                self.gift_contract_id: "Gift",
                                self.marketplace_contract_id: "Marketplace",
                                self.multi_room_contract_id: "Room",
                            }
                            source_name = contract_name_map.get(contract_id, "Unknown")
                            
                            _, is_new = ActivityDatabase.upsert_activity({
                                "transaction_hash": tx_hash,
                                "wallet_address": payer,
                                "activity_type": "Platform Fee",
                                "from_address": payer,
                                "to_address": platform_wallet,
                                "details": f"Fee from {source_name}",
                                "amount": formatted_fee,
                                "status": "success",
                                "datetime": datetime.now(timezone.utc).isoformat(),
                                "ledger": ledger_seq
                            })
                            if is_new:
                                emit_threadsafe('activity:new', {
                                    "wallet_address": payer,
                                    "activity_type": "Platform Fee",
                                    "tx_hash": tx_hash
                                })
                            print(f"✅ Indexed Activity: Fee {formatted_fee} from {payer} ({source_name})")

                except Exception as e:
                    print(f"Error parsing event {tx_hash}: {e}")
                    traceback.print_exc()

            return latest_ledger + 1

        except Exception as e:
            err_msg = str(e)
            print(f"Error fetching events for {contract_id}: {err_msg}")
            if "startLedger must be within the ledger range" in err_msg or "too old" in err_msg.lower():
                print(f"Self-recovery: skipping to latest_ledger - 5000 for {contract_id}")
                return max(latest_ledger - 5000, 1)
            return start_ledger

    def run_loop(self):
        print("Starting Web3 Indexer Loop (Per-Contract State)...")
        while True:
            try:
                try:
                    latest_ledger_info = self.server.get_latest_ledger()
                    latest_ledger = latest_ledger_info.sequence
                except Exception as e:
                    print(f"Error fetching latest ledger: {e}")
                    time.sleep(5)
                    continue

                swap_last = StateDatabase.get_last_ledger(self.swap_contract_id)
                new_swap_last = self.process_events(self.swap_contract_id, swap_last, latest_ledger)
                if new_swap_last != swap_last:
                    StateDatabase.update_last_ledger(self.swap_contract_id, new_swap_last)
                gift_last = StateDatabase.get_last_ledger(self.gift_contract_id)
                new_gift_last = self.process_events(self.gift_contract_id, gift_last, latest_ledger)
                if new_gift_last != gift_last:
                    StateDatabase.update_last_ledger(self.gift_contract_id, new_gift_last)
                    
                marketplace_last = StateDatabase.get_last_ledger(self.marketplace_contract_id)
                new_marketplace_last = self.process_events(self.marketplace_contract_id, marketplace_last, latest_ledger)
                if new_marketplace_last != marketplace_last:
                    StateDatabase.update_last_ledger(self.marketplace_contract_id, new_marketplace_last)
                    
                if self.registry_contract_id:
                    registry_last = StateDatabase.get_last_ledger(self.registry_contract_id)
                    new_registry_last = self.process_events(self.registry_contract_id, registry_last, latest_ledger)
                    if new_registry_last != registry_last:
                        StateDatabase.update_last_ledger(self.registry_contract_id, new_registry_last)

                multi_room_last = StateDatabase.get_last_ledger(self.multi_room_contract_id)
                new_multi_room_last = self.process_events(self.multi_room_contract_id, multi_room_last, latest_ledger)
                if new_multi_room_last != multi_room_last:
                    StateDatabase.update_last_ledger(self.multi_room_contract_id, new_multi_room_last)
            except Exception as e:
                print(f"Unhandled error in main loop: {e}")
                traceback.print_exc()
            time.sleep(5)
