from datetime import date

from ledgerline.models import Invoice, LineItem
from ledgerline.validation import check_duplicate, check_tax_type, check_totals, is_valid_gstin

SITARA_GSTIN = "27AAKCS4821M1ZW"
NARMADA_GSTIN = "24AAOFN2207Q1ZX"


def make_invoice(**overrides) -> Invoice:
    fields = dict(
        document_type="invoice",
        supplier_name="Sitara Industrial Supplies Pvt. Ltd.",
        supplier_gstin=SITARA_GSTIN,
        invoice_number="SIS/26-27/0042",
        invoice_date=date(2026, 4, 25),
        currency="INR",
        subtotal=100.0,
        cgst=9.0,
        sgst=9.0,
        igst=0.0,
        round_off=0.0,
        total=118.0,
        bank_account=None,
        ifsc=None,
        po_number=None,
        notes=None,
        line_items=[LineItem("Widget", 1.0, 100.0, 100.0)],
    )
    fields.update(overrides)
    return Invoice(**fields)


def test_valid_gstin_accepted():
    assert is_valid_gstin(SITARA_GSTIN)


def test_short_gstin_rejected():
    assert not is_valid_gstin("27AAKCS4821M")


def test_missing_gstin_rejected():
    assert not is_valid_gstin(None)


def test_inter_state_igst_is_fine():
    invoice = make_invoice(supplier_gstin=NARMADA_GSTIN, cgst=0.0, sgst=0.0, igst=18.0)
    assert check_tax_type(invoice) == []


def test_totals_match():
    assert check_totals(make_invoice()) == []


def test_totals_mismatch_detected():
    assert check_totals(make_invoice(total=150.0)) == ["totals_mismatch"]


def test_duplicate_of_paid_invoice(conn, ref):
    invoice = make_invoice(invoice_number="SIS/26-27/0018")
    assert check_duplicate(conn, ref, invoice) == ["duplicate"]


def test_new_invoice_is_not_a_duplicate(conn, ref):
    assert check_duplicate(conn, ref, make_invoice()) == []


def test_intra_state_cgst_sgst_is_fine():
    # Sitara (state 27) charging CGST+SGST to Meridian (state 27) is correct
    assert check_tax_type(make_invoice()) == []


def test_intra_state_igst_is_a_mismatch():
    # dev_004: Maharashtra supplier charging IGST
    invoice = make_invoice(cgst=0.0, sgst=0.0, igst=18.0)
    assert check_tax_type(invoice) == ["tax_type_mismatch"]

def test_totals_include_round_off():
    # dev_001 pattern: 100 + 9 + 9 - 0.40 = 117.60
    assert check_totals(make_invoice(round_off=-0.40, total=117.60)) == []


def test_totals_difference_of_exactly_one_rupee_is_within_tolerance():
    assert check_totals(make_invoice(total=119.00)) == []


def test_totals_difference_over_one_rupee_is_a_mismatch():
    assert check_totals(make_invoice(total=119.01)) == ["totals_mismatch"]