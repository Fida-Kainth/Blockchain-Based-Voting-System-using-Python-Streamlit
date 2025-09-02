# blockchain.py
import hashlib
import json
import time
import random

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()

class VoteTransaction:
    def __init__(self, voter_hash: str, delegate: str):
        self.voter_hash = voter_hash
        self.delegate = delegate
        self.timestamp = time.time()

    def to_dict(self):
        return {
            "voter_hash": self.voter_hash,
            "delegate": self.delegate,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        return json.dumps(self.to_dict(), sort_keys=True)

class Block:
    def __init__(self, index: int, prev_hash: str, transactions, validator: str, contract):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions  # list[VoteTransaction]
        self.previous_hash = prev_hash
        self.validator = validator
        self.contract_snapshot = json.dumps(sorted(list(contract.voted)))
        self.hash = self.compute_hash()

    def compute_hash(self) -> str:
        tx_str = ''.join(str(tx) for tx in self.transactions)
        payload = f"{self.index}{self.timestamp}{tx_str}{self.previous_hash}{self.validator}{self.contract_snapshot}"
        return sha256(payload)

class Blockchain:
    def __init__(self, contract):
        self.chain = []
        self.contract = contract
        self.create_genesis_block()

    def create_genesis_block(self):
        self.chain.append(Block(0, '0', [], 'genesis', self.contract))

    def select_validator(self) -> str:
        eligible = [
            uid for uid, age in self.contract.eligible_users.items()
            if age >= 18 and uid not in self.contract.voted
        ]
        if not eligible:
            return "default_validator"
        return random.choice(eligible)

    def add_block(self, transactions):
        for tx in transactions:
            if not self.contract.can_vote(tx.voter_hash, tx.delegate):
                raise Exception("Vote invalid (underage, already voted, or bad delegate).")

        for tx in transactions:
            self.contract.mark_voted(tx.voter_hash)

        validator = self.select_validator()
        block = Block(len(self.chain), self.chain[-1].hash, transactions, validator, self.contract)
        self.chain.append(block)
