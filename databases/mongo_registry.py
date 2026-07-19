from models.mongo_registry import RegistryToken

class RegistryDatabase:
    @staticmethod
    def add_token(token_address: str, symbol: str = "Token"):
        token = RegistryToken.objects(token_address=token_address).first()
        if not token:
            token = RegistryToken(token_address=token_address, symbol=symbol, is_active=True)
        else:
            token.is_active = True
            if symbol != "Token":
                token.symbol = symbol
        token.save()
        return token

    @staticmethod
    def remove_token(token_address: str):
        token = RegistryToken.objects(token_address=token_address).first()
        if token:
            token.is_active = False
            token.save()
        return token

    @staticmethod
    def get_all_active_tokens():
        tokens = RegistryToken.objects(is_active=True)
        return [{"token_address": t.token_address, "symbol": t.symbol} for t in tokens]
