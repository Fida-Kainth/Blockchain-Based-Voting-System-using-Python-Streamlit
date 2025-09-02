# smart_contract.py
class VotingSmartContract:
    def __init__(self, eligible_users):
        self.voted = set()
        self.eligible_users = eligible_users  # dict: voter_hash -> age

    def can_vote(self, user_id, delegate):
        return (
            self.eligible_users.get(user_id, 0) >= 18 and
            user_id not in self.voted and
            delegate in ['D1', 'D2', 'D3', 'D4', 'D5']
        )

    def mark_voted(self, user_id):
        self.voted.add(user_id)

