from stellar_sdk.xdr import SCVal

def scval_to_native(sc_val: SCVal):
    if sc_val.type == sc_val.type.SCV_ADDRESS:
        if sc_val.address.account_id:
            from stellar_sdk.strkey import StrKey
            return StrKey.encode_ed25519_public_key(sc_val.address.account_id.account_id.ed25519.uint256)
        elif sc_val.address.contract_id:
            from stellar_sdk.strkey import StrKey
            return StrKey.encode_contract(sc_val.address.contract_id.contract_id.hash)
    elif sc_val.type == sc_val.type.SCV_SYMBOL:
        return sc_val.sym.sc_symbol.decode()
    elif sc_val.type == sc_val.type.SCV_I128:
        hi = sc_val.i128.hi.int64
        lo = sc_val.i128.lo.uint64
        return (hi << 64) | lo
    elif sc_val.type == sc_val.type.SCV_U32:
        return sc_val.u32.uint32
    elif sc_val.type == sc_val.type.SCV_I32:
        return sc_val.i32.int32
    elif sc_val.type == sc_val.type.SCV_STRING:
        return sc_val.str.sc_string.decode()
    elif sc_val.type == sc_val.type.SCV_U64:
        return sc_val.u64.uint64
    elif sc_val.type == sc_val.type.SCV_I64:
        return sc_val.i64.int64
    elif sc_val.type == sc_val.type.SCV_BOOL:
        return sc_val.b
    return str(sc_val)
