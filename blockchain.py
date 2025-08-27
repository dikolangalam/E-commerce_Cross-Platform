import os
import json
from web3 import Web3
from dotenv import load_dotenv
from web3.exceptions import BadFunctionCallOutput, ContractLogicError

load_dotenv()

ALCHEMY_URL = os.getenv('ALCHEMY_URL')
PRIVATE_KEY = os.getenv('PRIVATE_KEY')
CONTRACT_ADDRESS = os.getenv('CONTRACT_ADDRESS')

if not CONTRACT_ADDRESS:
    raise ValueError("CONTRACT_ADDRESS is not set in .env")

CONTRACT_ADDRESS = Web3.to_checksum_address(CONTRACT_ADDRESS)

with open('contracts/CertificateABI.json') as f:
    abi = json.load(f)

web3 = Web3(Web3.HTTPProvider(ALCHEMY_URL))

def print_network_info():
    try:
        chain_id = web3.eth.chain_id
        print(f"Connected to network with chain ID: {chain_id}")
    except Exception as e:
        print(f"Failed to get chain ID: {e}")

def get_balance_eth(address):
    balance_wei = web3.eth.get_balance(address)
    return web3.from_wei(balance_wei, 'ether')

account = web3.eth.account.from_key(PRIVATE_KEY)
sender_address = account.address

print_network_info()
print(f"Using sender address: {sender_address}")
print(f"Sender ETH balance: {get_balance_eth(sender_address)} ETH")

contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=abi)

def register_certificate(student_name, course, cert_hash):
    balance = web3.eth.get_balance(sender_address)
    gas_price = web3.eth.gas_price

    txn_dict = contract.functions.registerCertificate(student_name, course, cert_hash).build_transaction({'from': sender_address})

    txn_data = txn_dict['data']

    try:
        gas_estimate = web3.eth.estimate_gas({
            'to': CONTRACT_ADDRESS,
            'from': sender_address,
            'data': txn_data,
        })
        print(f"Gas estimate: {gas_estimate}")
    except Exception as e:
        print(f"Gas estimation failed: {e}")
        raise Exception("Transaction simulation failed, likely contract revert")

    required_eth = gas_estimate * gas_price

    print(f"Current balance (wei): {balance}")
    print(f"Gas price (wei): {gas_price}")
    print(f"Gas estimate: {gas_estimate}")
    print(f"Required ETH for gas: {web3.from_wei(required_eth, 'ether')}")

    if balance < required_eth:
        raise Exception(
            f"Insufficient funds to cover gas costs. Balance: {web3.from_wei(balance, 'ether')} ETH, "
            f"Required: {web3.from_wei(required_eth, 'ether')} ETH"
        )

    nonce = web3.eth.get_transaction_count(sender_address)
    txn = contract.functions.registerCertificate(student_name, course, cert_hash).build_transaction({
        'from': sender_address,
        'nonce': nonce,
        'gas': gas_estimate + 10000,  
        'gasPrice': gas_price,
    })

    signed_txn = web3.eth.account.sign_transaction(txn, private_key=PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)
    print(f"Transaction sent with hash: {web3.to_hex(tx_hash)}")
    return web3.to_hex(tx_hash)


def verify_certificate(cert_hash):
    try:
        result = contract.functions.verifyCertificate(cert_hash).call()
        print(f"verifyCertificate result: {result}")
        return result
    except ContractLogicError as e:
        print(f"Contract reverted during verification: {e}")
        return False
    except Exception as e:
        print(f"Contract call failed with exception: {e}")
        return False
