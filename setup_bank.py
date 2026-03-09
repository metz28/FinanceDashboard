# setup_bank.py
# Nutze dieses Skript um eine neue Bank zu verbinden

from gocardless_connector import setup_bank

print("=== Bank-Verbindung einrichten ===\n")
print("Verfügbare Banken:")
print("1. Revolut (REVOLUT_REVOGB21)")
print("2. C24 (C24_HYVEDEMM488)")
print("3. N26 (N26_NTSBDEB1)")
print("4. DKB (DKB_BYLADEM1001)")
print("5. ING (ING_INGDDEFF)")
print("6. Sparkasse (SPARKASSE_SPUEDE2UXXX)")
print("\nVollständige Liste: https://ob.nordigen.com/api/institutions/\n")

institution_id = input("Institution ID eingeben: ").strip()
name = input("Name für diese Verbindung (z.B. 'revolut'): ").strip()

print(f"\nVerbinde mit {name}...")
requisition_id = setup_bank(institution_id, name)

print("\n" + "="*50)
print("✓ Bank erfolgreich autorisiert!")
print("="*50)
print(f"\nFüge diese Zeile in config.py ein:")
print(f"{name.upper()}_REQUISITION_ID = \"{requisition_id}\"")
print("\nUnd in etl_pipeline.py:")
print(f"({name.upper()}_REQUISITION_ID, \"{name.title()}\")")
