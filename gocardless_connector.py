from nordigen import NordigenClient

client = NordigenClient(

    secret_id= "",
    secret_key= ""
)

client.generate_token()

def setup_bank(institution_id: str, name: str):
    init = client.initialize_session(
        institution_id=institution_id,
        redirect_uri="http://localhost:8080/callback",
        reference_id=name
    )
    print(f"Öffne diesen Link im Browser: {init.link}")
    # requisition_id speichern
    return init.requisition_id

# Transaktionen holen
def fetch_transactions(requisition_id: str) -> list:
    accounts = client.requisition.get_requisition_by_id(requisition_id)["accounts"]
    all_txns = []
    for acc_id in accounts:
        account = client.account(acc_id)
        txns = account.get_transactions()["transactions"]["booked"]
        all_txns.extend(txns)
    return all_txns