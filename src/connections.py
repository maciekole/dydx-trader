from dydx3 import Client
from web3 import Web3

import constants


def connect_dydx():
    """

    :return:
    """
    print("connect_dydx()")  # @todo debug
    client = Client(
        host=constants.HOST,
        api_key_credentials={
            "key": constants.DYDX_API_KEY,
            "secret": constants.DYDX_API_SECRET,
            "passphrase": constants.DYDX_API_PASSPHRASE,
        },
        stark_private_key=constants.STARK_PRIVATE_KEY,
        eth_private_key=constants.ETH_PRIVATE_KEY,
        default_ethereum_address=constants.ETHEREUM_ADDRESS,
        web3=Web3(Web3.HTTPProvider(constants.HTTP_PROVIDER)),
    )
    # Assert client connection
    account = client.private.get_account()
    account_id = account.data["account"]["id"]
    assert account_id
    quote_balance = account.data["account"]["quoteBalance"]
    print(f"account_id: {account_id}")  # @todo debug
    print(f"quote_balance: {quote_balance}")  # @todo debug

    return client


def connect_mainnet_dydx():
    """

    :return:
    """
    print("connect_mainnet_dydx()")  # @todo debug
    client = Client(
        host=constants.API_HOST_MAINNET,
        api_key_credentials={
            "key": constants.DYDX_API_KEY_MAINNET,
            "secret": constants.DYDX_API_SECRET_MAINNET,
            "passphrase": constants.DYDX_API_PASSPHRASE_MAINNET,
        },
        stark_private_key=constants.STARK_PRIVATE_KEY_MAINNET,
        eth_private_key=constants.ETH_PRIVATE_KEY_MAINNET,
        default_ethereum_address=constants.ETHEREUM_ADDRESS_MAINNET,
        web3=Web3(Web3.HTTPProvider(constants.HTTP_PROVIDER_MAINNET)),
    )
    # Assert client connection
    account = client.private.get_account()
    account_id = account.data["account"]["id"]
    assert account_id
    quote_balance = account.data["account"]["quoteBalance"]
    print(f"account_id: {account_id}")  # @todo debug
    print(f"quote_balance: {quote_balance}")  # @todo debug

    return client
