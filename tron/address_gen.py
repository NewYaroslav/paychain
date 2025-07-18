"""
Module: tron.address_gen
Description: Generates deterministic TRON addresses for users using BIP44 HD wallets.
"""

from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from tronpy.keys import PrivateKey


def generate_tron_address(mnemonic: str, user_id: int, salt: str = "") -> dict:
    """
    Generate a deterministic TRON address for a given user using BIP44 derivation.

    :param mnemonic: BIP39 mnemonic phrase (secret!)
    :param user_id: Unique user identifier used as derivation index
    :param salt: Optional project-specific salt to differentiate environments
    :return: Dictionary with 'address' and 'private_key' (hex)
    """
    # Derive seed from mnemonic + optional salt
    seed_bytes = Bip39SeedGenerator(mnemonic + salt).Generate()

    # Derive: m/44'/195'/0'/0/{user_id}
    wallet = Bip44.FromSeed(seed_bytes, Bip44Coins.TRON)
    derived = wallet.Purpose().Coin().Account(0).Change(Bip44Changes.CHAIN_EXT).AddressIndex(user_id)

    private_key_hex = derived.PrivateKey().Raw().ToHex()
    address_base58 = derived.PublicKey().ToAddress()

    return {
        "address": address_base58,
        "private_key": private_key_hex,
    }