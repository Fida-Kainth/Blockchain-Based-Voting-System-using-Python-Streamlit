# app.py
# Streamlit Voting UI

import streamlit as st
import random
import time
from blockchain import Blockchain, VoteTransaction, sha256
from smart_contract import VotingSmartContract

st.set_page_config(page_title="Blockchain Voting (PoS)", page_icon="🔐", layout="wide")
st.title("🔐 Blockchain Voting System (PoS)")

DELEGATES = ['D1', 'D2', 'D3', 'D4', 'D5']

# --------- Initialization (runs once) ---------
def init_simulation():
    # Create 100 users with IDs U001..U100 and ages (16–60)
    user_ids = [f"U{str(i).zfill(3)}" for i in range(1, 101)]
    ages = [random.randint(16, 60) for _ in user_ids]

    # Registry for contract: keys are HASHED user IDs -> age
    eligible_users_hashed = {sha256(uid): age for uid, age in zip(user_ids, ages)}

    # Keep a plain reference list only for test/demo (not used on-chain)
    registry_plain = [{"user_id": uid, "age": age} for uid, age in zip(user_ids, ages)]

    contract = VotingSmartContract(eligible_users=eligible_users_hashed)
    chain = Blockchain(contract)

    st.session_state.registry_plain = registry_plain              # demo/testing aid
    st.session_state.contract = contract
    st.session_state.blockchain = chain
    st.session_state.submitted_votes = 0

if "blockchain" not in st.session_state:
    init_simulation()

contract = st.session_state.contract
blockchain = st.session_state.blockchain

# --------- Sidebar: Simulation controls ---------
with st.sidebar:
    st.header("⚙️ Controls")
    if st.button("🔄 Reset simulation", use_container_width=True):
        init_simulation()
        st.success("Simulation reset with a fresh set of 100 users.")
        st.stop()

    with st.expander("🧪 Show test users (for manual testing)"):
        st.caption("These are simulated users. On-chain we only store *hashed* IDs.")
        st.dataframe(st.session_state.registry_plain, use_container_width=True, height=260)
        st.markdown(
            "- Try IDs like `U001`, `U042`, etc.\n"
            "- Some are under 18 to test rejections."
        )

# --------- Vote form ---------
st.subheader("🗳️ Cast Your Vote")

with st.form("vote_form", clear_on_submit=False):
    col1, col2, col3 = st.columns([2, 1.4, 1.6])
    with col1:
        user_id_input = st.text_input("User ID", placeholder="e.g., U042")
    with col2:
        age_input = st.number_input("Your Age (for display only)", min_value=0, max_value=120, value=18, step=1)
    with col3:
        delegate_choice = st.selectbox("Choose a delegate", DELEGATES, index=0)

    submitted = st.form_submit_button("Submit vote ✅")

if submitted:
    user_id_clean = (user_id_input or "").strip()
    if not user_id_clean:
        st.error("Please enter your User ID (e.g., U042).")
    else:
        voter_hash = sha256(user_id_clean)
        # Ensure user exists in registry
        if voter_hash not in contract.eligible_users:
            st.error("User not found in the eligible registry.")
        else:
            # Build a single-transaction block
            tx = VoteTransaction(voter_hash=voter_hash, delegate=delegate_choice)
            try:
                blockchain.add_block([tx])
            except Exception as e:
                st.error(f"❌ Vote rejected: {e}")
            else:
                st.session_state.submitted_votes += 1
                st.success(f"✅ Vote recorded for {delegate_choice}. "
                           f"Your identity is anonymized as hash `{voter_hash[:10]}…`.")
                time.sleep(0.25)

# --------- Status & Tallies ---------
st.subheader("📊 Current Status")

# Tally votes per delegate (skip genesis)
tally = {d: 0 for d in DELEGATES}
tx_rows = []
for blk in blockchain.chain[1:]:
    for tx in blk.transactions:
        tally[tx.delegate] += 1
        tx_rows.append({
            "Block #": blk.index,
            "Voter (hash, first 10)": tx.voter_hash[:10] + "…",
            "Delegate": tx.delegate,
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tx.timestamp)),
            "Validator (hash, first 10)": (blk.validator[:10] + "…") if blk.validator else ""
        })

left, right = st.columns([1, 1])
with left:
    st.metric("Total Blocks (incl. genesis)", len(blockchain.chain))
    st.metric("Votes Recorded", sum(tally.values()))
with right:
    # Eligible validator pool = users aged >=18 who haven't voted yet
    validator_pool = [uid for uid, age in contract.eligible_users.items()
                      if age >= 18 and uid not in contract.voted]
    st.metric("Eligible Validators Remaining", len(validator_pool))

st.markdown("#### 🧮 Vote Tally")
tally_cols = st.columns(len(DELEGATES))
for i, d in enumerate(DELEGATES):
    with tally_cols[i]:
        st.metric(d, tally[d])

st.markdown("#### ⛓️ Blockchain (Blocks)")
for blk in blockchain.chain:
    with st.expander(f"Block #{blk.index} — Validator: {(blk.validator[:10] + '…') if blk.validator else ''}"):
        st.write({
            "index": blk.index,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(blk.timestamp)),
            "previous_hash": blk.previous_hash[:24] + "…",
            "validator": blk.validator,
            "transactions": len(blk.transactions),
            "hash": blk.hash
        })
        if blk.transactions:
            st.write("Transactions:")
            for tx in blk.transactions:
                st.write({
                    "voter_hash": tx.voter_hash,
                    "delegate": tx.delegate,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(tx.timestamp))
                })

# Optional quick integrity check
def verify_chain(chain):
    for i, blk in enumerate(chain):
        if i == 0:
            continue
        if blk.previous_hash != chain[i-1].hash:
            return False, f"Prev hash mismatch at block {i}"
        if blk.compute_hash() != blk.hash:
            return False, f"Hash mismatch at block {i}"
    return True, "OK"

ok, msg = verify_chain(blockchain.chain)
st.info(f"🔎 Chain integrity: **{msg}**" if ok else f"🚨 Chain integrity failed: {msg}")
