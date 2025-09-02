# blockchain.py
import hashlib, json, time, random
from smart_contract import VotingSmartContract

def sha256(data): return hashlib.sha256(data.encode()).hexdigest()

class VoteTransaction:
    def __init__(self, voter_hash, delegate):
        self.voter_hash = voter_hash
        self.delegate = delegate
        self.timestamp = time.time()

    def to_dict(self):
        return {'voter_hash': self.voter_hash, 'delegate': self.delegate, 'timestamp': self.timestamp}

    def __str__(self):
        return json.dumps(self.to_dict(), sort_keys=True)

class Block:
    def __init__(self, index, prev_hash, transactions, validator, contract):
        self.index = index
        self.timestamp = time.time()
        self.transactions = transactions
        self.previous_hash = prev_hash
        self.validator = validator
        self.contract_snapshot = json.dumps(sorted(list(contract.voted)))
        self.hash = self.compute_hash()

    def compute_hash(self):
        tx_str = ''.join(str(tx) for tx in self.transactions)
        return sha256(f"{self.index}{self.timestamp}{tx_str}{self.previous_hash}{self.validator}{self.contract_snapshot}")

class Blockchain:
    def __init__(self, contract):
        self.chain = []
        self.contract = contract
        self.create_genesis_block()

    def create_genesis_block(self):
        self.chain.append(Block(0, '0', [], 'genesis', self.contract))

    def select_validator(self):
        # PoS-style: choose from eligible users (age >=18) who haven't voted yet
        eligible = [uid for uid, age in self.contract.eligible_users.items()
                    if age >= 18 and uid not in self.contract.voted]
        if not eligible:
            return "default_validator"
        return random.choice(eligible)

    def add_block(self, transactions):
        # Smart contract checks for each tx
        for tx in transactions:
            if not self.contract.can_vote(tx.voter_hash, tx.delegate):
                raise Exception("Vote invalid (underage, already voted, or bad delegate).")
        # Mark voters as voted (state change must happen before sealing block)
        for tx in transactions:
            self.contract.mark_voted(tx.voter_hash)

        validator = self.select_validator()
        block = Block(len(self.chain), self.chain[-1].hash, transactions, validator, self.contract)
        self.chain.append(block)
