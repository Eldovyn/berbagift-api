from models.mongo_state import IndexerState

class StateDatabase:
    @staticmethod
    def get_last_ledger(contract_id: str) -> int:
        state = IndexerState.objects(state_id=contract_id).first()
        if not state:
            state = IndexerState(state_id=contract_id, last_ledger_processed=0).save()
        return state.last_ledger_processed

    @staticmethod
    def update_last_ledger(contract_id: str, ledger: int):
        state = IndexerState.objects(state_id=contract_id).first()
        if not state:
            state = IndexerState(state_id=contract_id)
        state.last_ledger_processed = ledger
        state.save()
