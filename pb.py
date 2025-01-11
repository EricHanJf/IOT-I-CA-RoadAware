from Cryptodome.Cipher import AES
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from pubnub.crypto import PubNubCryptoModule, AesCbcCryptoModule, LegacyCryptoModule
from pubnub.models.consumer.v3.channel import Channel
from pubnub.models.consumer.v3.group import Group
from pubnub.models.consumer.v3.uuid import UUID
from .config import config

cipher_key = config.get("PUBNUB_CIPHER_KEY")

pn_config = PNConfiguration()
pn_config.publish_key = config.get("PUBNUB_PUBLISH_KEY")
pn_config.subscribe_key = config.get("PUBNUB_SUBSCRIBE_KEY")
pn_config.uuid = config.get("PUBNUB_UUID")
pn_config.secret_key = config.get("PUBNUB_SECRET_KEY")
pn_config.cipher_key = cipher_key
pn_config.cipher_mode = AES.MODE_GCM
pn_config.fallback_cipher_mode = AES.MODE_CBC
pn_config.crypto_module = AesCbcCryptoModule(pn_config)
pubnub = PubNub(pn_config)

pi_channel = "RoadEase"


def grant_read_access(user_id):
    envelope = (
        pubnub.grant_token()
        .channels([Channel.id(channel).read() for channel in (pi_channel)])
        .authorized_uuid(user_id)
        .ttl(60)
        .sync()
    )
    return envelope.result.token


def grant_write_access(user_id):
    envelope = (
        pubnub.grant_token()
        .channels([Channel.id(channel).write() for channel in (pi_channel)])
        .authorized_uuid(user_id)
        .ttl(60)
        .sync()
    )
    return envelope.result.token


def grant_read_and_write_access(user_id):
    print(f"GRANTING READ AND WRITE ACCESS {user_id} ")
    envelope = (
        pubnub.grant_token()
        .channels([Channel.id("RoadEase").read().write()])
        .authorized_uuid(user_id)
        .ttl(5)
        .sync()
    )
    return envelope.result.token


def revoke_access(token):
    envelope = pubnub.revoke_token(token)


def parse_token(token):
    token_details = pubnub.parse_token(token)
    print("Parsing the TOKEN")
    print(token_details)
    read_access = token_details["resources"]["channels"]["RoadEase"]["read"]
    write_access = token_details["resources"]["channels"]["RoadEase"]["write"]
    uuid = token_details["authorized_uuid"]
    return (
        token_details["timestamp"],
        token_details["ttl"],
        uuid,
        read_access,
        write_access,
    )
