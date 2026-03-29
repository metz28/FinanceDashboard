# test_credentials.py
# Teste alle API-Verbindungen bevor du die Pipeline startest

import requests
from config import BITPANDA_API_KEY, GOCARDLESS_SECRET_ID, GOCARDLESS_SECRET_KEY
from config import REVOLUT_REQUISITION_ID, C24_REQUISITION_ID

def test_bitpanda():
    print("\n[1/2] Teste Bitpanda API...")

    try:
        r = requests.get(
            "https://api.bitpanda.com/v1/trades",
            headers={"X-API-KEY": BITPANDA_API_KEY},
            timeout=10,
            verify=False
        )

        if r.status_code == 200:
            print(f"  ✓ Verbindung erfolgreich!")
            print(f"  ✓ API Key: {BITPANDA_API_KEY[:10]}...{BITPANDA_API_KEY[-4:]}")
            return True
        elif r.status_code == 401:
            print(f"  ✗ API Key ungültig (401 Unauthorized)")
            print(f"  → Prüfe deinen Key auf bitpanda.com")
            print(BITPANDA_API_KEY)
            return False
        elif r.status_code == 403:
            print(f"  ✗ Zugriff verweigert (403 Forbidden)")
            return False
        else:
            print(f"  ✗ HTTP-Fehler {r.status_code}")
            return False

    except requests.exceptions.Timeout:
        print("  ✗ Timeout - Bitpanda antwortet nicht")
        return False
    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        return False

def test_gocardless():
    print("\n[2/2] Teste GoCardless (Nordigen) API...")

    if GOCARDLESS_SECRET_ID in ["", "dein_id", None]:
        print("  ⊘ GoCardless nicht konfiguriert - übersprungen")
        print("  → Registriere dich auf bankaccountdata.gocardless.com")
        return None

    try:
        from nordigen import NordigenClient

        client = NordigenClient(
            secret_id=GOCARDLESS_SECRET_ID,
            secret_key=GOCARDLESS_SECRET_KEY
        )

        token = client.generate_token()

        if token.get("access"):
            print(f"  ✓ Authentifizierung erfolgreich!")
            print(f"  ✓ Token gültig für: {token.get('access_expires', 'unbekannt')}s")

            # Prüfe Requisition IDs
            if REVOLUT_REQUISITION_ID:
                print(f"  ✓ Revolut Requisition ID konfiguriert")
            if C24_REQUISITION_ID:
                print(f"  ✓ C24 Requisition ID konfiguriert")

            if not REVOLUT_REQUISITION_ID and not C24_REQUISITION_ID:
                print(f"  ⚠ Keine Bank-Verbindungen eingerichtet")
                print(f"  → Führe 'python setup_bank.py' aus")

            return True
        else:
            print(f"  ✗ Authentifizierung fehlgeschlagen")
            return False

    except Exception as e:
        print(f"  ✗ Fehler: {e}")
        print(f"  → Prüfe SECRET_ID und SECRET_KEY in config.py")
        return False

def main():
    print("="*60)
    print("API Credentials Test")
    print("="*60)

    bitpanda_ok = test_bitpanda()
    gocardless_ok = test_gocardless()

    print("\n" + "="*60)
    print("Zusammenfassung:")
    print("="*60)

    if bitpanda_ok:
        print("✓ Bitpanda: Bereit")
    else:
        print("✗ Bitpanda: Nicht konfiguriert oder fehlerhaft")

    if gocardless_ok is True:
        print("✓ GoCardless: Bereit")
    elif gocardless_ok is False:
        print("✗ GoCardless: Fehlerhaft")
    else:
        print("⊘ GoCardless: Nicht konfiguriert")

    print("\nNächste Schritte:")
    if not bitpanda_ok:
        print("1. Bitpanda API Key in config.py eintragen")
    if gocardless_ok is False:
        print("2. GoCardless Credentials in config.py korrigieren")
    if gocardless_ok is None:
        print("2. GoCardless Account erstellen und Credentials eintragen")
        print("3. Bank verbinden mit: python setup_bank.py")
    if gocardless_ok is True and not (REVOLUT_REQUISITION_ID or C24_REQUISITION_ID):
        print("2. Bank verbinden mit: python setup_bank.py")

    if bitpanda_ok and (gocardless_ok is True) and (REVOLUT_REQUISITION_ID or C24_REQUISITION_ID):
        print("\n🎉 Alles bereit! Starte die Pipeline mit: python etl_pipeline.py")

if __name__ == "__main__":
    main()
