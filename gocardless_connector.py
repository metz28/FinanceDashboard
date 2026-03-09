from nordigen import NordigenClient
from config import GOCARDLESS_SECRET_ID, GOCARDLESS_SECRET_KEY


def get_client():
    client = NordigenClient(
        secret_id=GOCARDLESS_SECRET_ID,
        secret_key=GOCARDLESS_SECRET_KEY
    )
    client.generate_token()
    return client


def setup_bank(institution_id: str, name: str):
    client = get_client()
    init = client.initialize_session(
        institution_id=institution_id,
        redirect_uri="http://localhost:8080/callback",
        reference_id=name
    )
    print(f"Öffne diesen Link im Browser: {init.link}")
    return init.requisition_id


def fetch_transactions(requisition_id: str) -> list:
    client = get_client()
    accounts = client.requisition.get_requisition_by_id(requisition_id)["accounts"]
    all_txns = []
    for acc_id in accounts:
        account = client.account(acc_id)
        txns = account.get_transactions()["transactions"]["booked"]
        all_txns.extend(txns)
    return all_txns
