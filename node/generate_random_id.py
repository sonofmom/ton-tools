#!/usr/bin/env python3
"""Python port of TON's generate-random-id utility.

https://github.com/ton-blockchain/ton/blob/master/utils/generate-random-id.cpp

Generates a random Ed25519 key (or imports one with -k) and, depending on --mode:

  id      print the private key, public key and ADNL short id as TL JSON; with
          --dict, as one {"pk": ..., "pub": ..., "adnl": ...} object of base64 values
  adnl    print an adnl.node record for the key and an address list (-a/-f)
  dht     print a signed dht.node record, as used in global config files
  keys    write the key to <name> and <name>.pub, print its hash (hex, base64)
  adnlid  write the key to a file named after its hash, print hash and ADNL address

Output and key files are byte-for-byte compatible with the C++ tool (--dict is
an addition of this port). Requires PyNaCl (pip install pynacl).
"""

import argparse
import base64
import binascii
import hashlib
import json
import os
import struct
import sys

try:
    import nacl.signing
except ImportError:
    sys.exit("generate_random_id.py requires PyNaCl: pip install pynacl")


class ToolError(Exception):
    pass


# Subset of tl/generate/scheme/ton_api.tl used by the tool:
#   name: (constructor id, result type, [(field, field type), ...])
# A constructor id is the CRC32 of its normalized schema line.
SCHEMA = {
    "pk.ed25519": (0x49682317, "PrivateKey", [("key", "int256")]),
    "pk.aes": (0xA5E85137, "PrivateKey", [("key", "int256")]),
    "pub.unenc": (0xB61F450A, "PublicKey", [("data", "bytes")]),
    "pub.ed25519": (0x4813B4C6, "PublicKey", [("key", "int256")]),
    "pub.aes": (0x2DBCADD4, "PublicKey", [("key", "int256")]),
    "pub.overlay": (0x34BA45CB, "PublicKey", [("name", "bytes")]),
    "adnl.id.short": (0x3E3F654F, "adnl.id.Short", [("id", "int256")]),
    "adnl.address.udp": (0x670DA6E7, "adnl.Address", [("ip", "int"), ("port", "int")]),
    "adnl.address.udp6": (0xE31D63FA, "adnl.Address", [("ip", "int128"), ("port", "int")]),
    "adnl.address.tunnel": (0x092B02EB, "adnl.Address", [("to", "int256"), ("pubkey", "PublicKey")]),
    "adnl.address.reverse": (0x27795286, "adnl.Address", []),
    "adnl.address.quic": (0x78017253, "adnl.Address", [("ip", "int"), ("port", "int")]),
    "adnl.addressList": (0x2227E658, "adnl.AddressList", [
        ("addrs", "vector adnl.Address"), ("version", "int"), ("reinit_date", "int"),
        ("priority", "int"), ("expire_at", "int"),
    ]),
    "adnl.node": (0x6B561285, "adnl.Node", [("id", "PublicKey"), ("addr_list", "adnl.addressList")]),
    "dht.node": (0x84533248, "dht.Node", [
        ("id", "PublicKey"), ("addr_list", "adnl.addressList"), ("version", "int"), ("signature", "bytes"),
    ]),
}
FIXED_SIZE = {"int128": 16, "int256": 32}

# TL objects are dicts shaped like their TL JSON: {"@type": name, field: value, ...}
# with int for `int` and bytes for `int128`, `int256` and `bytes` fields.


def tl_serialize(obj, boxed=True):
    """serialize_tl_object(): TL binary form, prefixed by the constructor id if boxed."""
    ctor, _, fields = SCHEMA[obj["@type"]]
    out = struct.pack("<I", ctor) if boxed else b""
    for name, ftype in fields:
        out += _serialize_field(obj[name], ftype)
    return out


def _serialize_field(value, ftype):
    if ftype == "int":
        return struct.pack("<i", value)
    if ftype in FIXED_SIZE:
        return value
    if ftype == "bytes":
        n = len(value)
        data = (bytes([n]) if n < 254 else b"\xfe" + n.to_bytes(3, "little")) + value
        return data + b"\0" * (-len(data) % 4)
    if ftype.startswith("vector "):
        return struct.pack("<i", len(value)) + b"".join(_serialize_field(v, ftype[7:]) for v in value)
    # Capitalized (abstract) types are boxed, constructor names are bare.
    return tl_serialize(value, boxed=ftype not in SCHEMA)


def tl_to_json(obj):
    """td::json_encode(td::ToJson(obj)): compact JSON, binary fields as base64."""
    def convert(value):
        if isinstance(value, bytes):
            return base64.b64encode(value).decode()
        if isinstance(value, dict):
            return {k: convert(v) for k, v in value.items()}
        if isinstance(value, list):
            return [convert(v) for v in value]
        return value

    return json.dumps(convert(obj), separators=(",", ":"))


def tl_from_json(value, ftype):
    """td::from_json(): missing or null fields keep defaults, abstract types need "@type"."""
    if ftype == "int":
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            value = str(value)  # a JSON number; floats then fail to parse, as in td
        if not isinstance(value, str):
            raise ToolError("expected a number")
        return to_int32(value)
    if ftype in FIXED_SIZE or ftype == "bytes":
        raw = _decode_base64(value)
        if ftype in FIXED_SIZE and len(raw) != FIXED_SIZE[ftype]:
            raise ToolError("Wrong length for UInt")
        return raw
    if ftype.startswith("vector "):
        if not isinstance(value, list):
            raise ToolError("expected an array")
        if any(v is None for v in value):
            raise ToolError("Unexpected null in array")
        return [tl_from_json(v, ftype[7:]) for v in value]

    if value is None:
        return None
    if not isinstance(value, dict):
        raise ToolError("expected an object")
    name = ftype if ftype in SCHEMA else _constructor_name(value, ftype)
    obj = {"@type": name}
    for field, field_type in SCHEMA[name][2]:
        v = value.get(field)
        obj[field] = _default(field_type) if v is None else tl_from_json(v, field_type)
    return obj


def _constructor_name(value, abstract_type):
    if "@type" not in value:
        raise ToolError('Can\'t find field "@type"')
    t = value["@type"]
    if not isinstance(t, (str, int)) or isinstance(t, bool):
        raise ToolError('"@type" must be a string or an int')
    for name, (ctor, result, _) in SCHEMA.items():
        if result == abstract_type and (t == name if isinstance(t, str) else (t & 0xFFFFFFFF) == ctor):
            return name
    if isinstance(t, str):
        raise ToolError(f'Unknown class "{t}"')
    raise ToolError(f"Unknown constructor 0x{t & 0xFFFFFFFF:08x}")


def _default(ftype):
    if ftype == "int":
        return 0
    if ftype in FIXED_SIZE:
        return bytes(FIXED_SIZE[ftype])
    if ftype == "bytes":
        return b""
    if ftype.startswith("vector "):
        return []
    return None


def _decode_base64(value):
    """td::base64_decode(): standard alphabet, canonical padding only."""
    if not isinstance(value, str):
        raise ToolError("expected a base64 string")
    try:
        raw = base64.b64decode(value, validate=True)
    except ValueError:
        raw = None
    if raw is None or base64.b64encode(raw).decode() != value:
        raise ToolError(f"invalid base64 string {value!r}")
    return raw


def to_int32(text):
    """td::to_integer_safe<int32>(): plain decimal that fits in 32 bits."""
    try:
        n = int(text)
    except ValueError:
        n = None
    if n is None or str(n) != text or not -2**31 <= n < 2**31:
        raise ToolError(f'Can\'t parse "{text}" as number')
    return n


def prefixed(prefix, fn, *args):
    """TRY_RESULT_PREFIX: call fn, prefixing any error message."""
    try:
        return fn(*args)
    except (ToolError, OSError, ValueError) as e:
        raise ToolError(f"{prefix}{e}") from None


class PrivateKey:
    """ton::PrivateKey as produced by PrivateKey::import: pk.ed25519 or pk.aes."""

    def __init__(self, kind, key):
        self.kind = kind
        self.key = key

    @classmethod
    def random(cls):
        return cls("pk.ed25519", bytes(nacl.signing.SigningKey.generate()))

    @classmethod
    def import_(cls, data):
        if len(data) < 4:
            raise ToolError("too short key")
        (ctor,) = struct.unpack_from("<I", data)
        for kind in ("pk.ed25519", "pk.aes"):
            if ctor == SCHEMA[kind][0]:
                if len(data) != 36:
                    raise ToolError("bad length")
                return cls(kind, data[4:])
        raise ToolError(f"unknown magic {struct.unpack_from('<i', data)[0]}")

    def tl(self):
        return {"@type": self.kind, "key": self.key}

    def export(self):
        return tl_serialize(self.tl())

    def public_key(self):
        if self.kind == "pk.aes":
            return {"@type": "pub.aes", "key": self.key}
        return {"@type": "pub.ed25519", "key": bytes(nacl.signing.SigningKey(self.key).verify_key)}

    def sign(self, data):
        if self.kind == "pk.aes":
            raise ToolError("failed to sign: AES keys can not sign")
        return nacl.signing.SigningKey(self.key).sign(data).signature


def _pubkey_serialized_size(pub):
    """PublicKey::serialized_size() (an estimate for unenc/overlay keys, as in C++)."""
    if pub["@type"] in ("pub.ed25519", "pub.aes"):
        return 36
    return len(pub["data"] if "data" in pub else pub["name"]) + 8


def normalize_addr_list(addr_list):
    """AdnlAddressList::create(tl).tl(): ports are truncated to 16 bits, the reverse
    marker is deduplicated and placed after regular addresses, QUIC addresses go last."""
    if addr_list is None:
        raise ToolError("addr list is null")
    regular, quic, has_reverse, size = [], [], False, 24
    for addr in addr_list["addrs"]:
        kind = addr["@type"]
        if kind == "adnl.address.reverse":
            has_reverse = True
        elif kind == "adnl.address.tunnel":
            if addr["pubkey"] is None:
                raise ToolError("tunnel address without pubkey")
            regular.append(addr)
            size += 36 + _pubkey_serialized_size(addr["pubkey"])
        else:
            addr = dict(addr, port=addr["port"] & 0xFFFF)
            if kind == "adnl.address.quic":
                quic.append(addr)
                size += 12
            else:
                regular.append(addr)
                size += 24 if kind == "adnl.address.udp6" else 12
    if has_reverse:
        size += 4
    if size > 128:
        raise ToolError(f"too big addr list: size={size}")
    reverse = [{"@type": "adnl.address.reverse"}] if has_reverse else []
    return dict(addr_list, addrs=regular + reverse + quic)


def parse_addr_list(text):
    value = prefixed("bad addr list JSON: ", json.loads, text)
    tl_list = prefixed("bad addr list TL: ", tl_from_json, value, "adnl.addressList")
    return prefixed("bad addr list: ", normalize_addr_list, tl_list)


def read_file(path):
    with open(path, "rb") as f:
        return f.read()


def write_file(path, data):
    """td::write_file(): create with mode 0600 (or truncate) and write."""
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600), "wb") as f:
        f.write(data)


def adnl_id_encode(short_id):
    """User-friendly ADNL address: base32(0x2d || id || crc16) without the leading 'f'."""
    data = b"\x2d" + short_id
    data += binascii.crc_hqx(data, 0).to_bytes(2, "big")
    return base64.b32encode(data).decode().lower()[1:]


def dht_node(pk, pub, addr_list, network_id):
    """dht::DhtNode{pub, addr_list, version -1, network_id, signature}.tl(), where the
    signature covers the same node with an empty signature. A network id other than
    -1 is stored as a 4-byte prefix of the signature field."""
    prefix = struct.pack("<i", network_id) if network_id != -1 else b""

    def node(signature):
        return {"@type": "dht.node", "id": pub, "addr_list": addr_list, "version": -1,
                "signature": prefix + signature}

    return node(pk.sign(tl_serialize(node(b""))))


class _InOrder(argparse.Action):
    """Queue checked options so they are validated in command-line order, like td::OptionParser."""

    def __call__(self, parser, namespace, values, option_string=None):
        namespace.checked.append((self.option_strings[0], values))


def main(argv=None):
    p = argparse.ArgumentParser(description="generate random id")
    p.add_argument("-m", "--mode", default="", help="sets mode (one of id/adnl/dht/keys/adnlid)")
    p.add_argument("-V", "--version", action="version",
                   version="generate-random-id (Python port of ton/utils/generate-random-id.cpp)")
    p.add_argument("-n", "--name", default="id_ton", help="path to save private keys to")
    p.add_argument("-k", "--key", action=_InOrder, help="path to private key to import")
    p.add_argument("-a", "--addr-list", action=_InOrder, help="addr list to sign")
    p.add_argument("-f", "--addr-list-file", action=_InOrder, help="path to file with addr-list")
    p.add_argument("-i", "--network-id", action=_InOrder, help="dht network id (default: -1)")
    p.add_argument("--dict", action="store_true",
                   help="with -m id: print one JSON object with pk, pub and adnl (short id) values")
    p.set_defaults(checked=[])
    args = p.parse_args(argv)

    pk = addr_list = network_id = None
    try:
        for opt, value in args.checked:
            if opt == "-k":
                if pk is not None:
                    raise ToolError("duplicate '-k' option")
                data = prefixed("failed to read private key: ", read_file, value)
                pk = prefixed("failed to import private key: ", PrivateKey.import_, data)
            elif opt in ("-a", "-f"):
                if addr_list is not None:
                    raise ToolError(f"duplicate '{opt}' option")
                if opt == "-f":
                    value = prefixed("failed to read addr-list: ", read_file, value)
                addr_list = parse_addr_list(value)
            else:
                if network_id is not None:
                    raise ToolError("duplicate '-i' option")
                network_id = prefixed("bad network id: ", to_int32, value)
    except ToolError as e:
        print(e, file=sys.stderr)
        return 2

    if not args.mode:
        print("'--mode' option missing", file=sys.stderr)
        return 2
    if args.dict and args.mode != "id":
        print("'--dict' is only supported with '-m id'", file=sys.stderr)
        return 2

    if pk is None:
        pk = PrivateKey.random()
    pub = pk.public_key()
    short_id = hashlib.sha256(tl_serialize(pub)).digest()

    try:
        if args.mode == "id":
            if args.dict:
                print(tl_to_json({"pk": pk.key, "pub": pub["key"], "adnl": short_id}))
            else:
                print(tl_to_json(pk.tl()))
                print(tl_to_json(pub))
                print(tl_to_json({"@type": "adnl.id.short", "id": short_id}))
        elif args.mode in ("adnl", "dht"):
            if addr_list is None:
                print("'-a' option missing", file=sys.stderr)
                return 2
            if args.mode == "adnl":
                node = {"@type": "adnl.node", "id": pub, "addr_list": addr_list}
                pk.sign(tl_serialize(node))  # unused, but the C++ tool fails here for AES keys too
            else:
                node = dht_node(pk, pub, addr_list, -1 if network_id is None else network_id)
            print(tl_to_json(node))
        elif args.mode == "keys":
            write_file(args.name, pk.export())
            write_file(args.name + ".pub", tl_serialize(pub))
            print(short_id.hex().upper(), base64.b64encode(short_id).decode())
        elif args.mode == "adnlid":
            name = short_id.hex().upper()
            write_file(name, pk.export())
            print(name, adnl_id_encode(short_id))
        else:
            print(f"unknown mode {args.mode}", file=sys.stderr)
            return 2
    except (ToolError, OSError) as e:
        print(e, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
