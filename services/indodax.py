from schemas.indodax import IndodaxCallbackPayload
import logging

logger = logging.getLogger(__name__)

async def validate_withdrawal_request(payload: IndodaxCallbackPayload) -> bool:
    try:
        logger.info(f"Menerima validasi withdrawal: {payload.request_id} untuk {payload.withdraw_amount} {payload.withdraw_currency}")
        is_valid = True 
        if is_valid:
            return True
        return False
    except Exception as e:
        logger.error(f"Gagal memvalidasi callback Indodax: {e}")
        return False