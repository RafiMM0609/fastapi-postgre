
# TK/0 (Tidak Kawin, tanpa tanggungan): Rp54.000.000.
# K/0 (Kawin, tanpa tanggungan): Rp58.500.000.
# K/1 (Kawin, 1 tanggungan): Rp63.000.000.
# K/2 (Kawin, 2 tanggungan): Rp67.500.000.
# K/3 (Kawin, 3 tanggungan): Rp72.000.000.

from typing import Optional


def calculate_ppn_12_based_on_excel(
    agency_fee:float,
):
    return 0.12 * (agency_fee * 11/12)
def calculate_pph21_with_ter(monthly_salary, pension_contribution, ptkp):
    # Biaya Jabatan: 5% dari penghasilan bruto, maksimal Rp500.000
    job_expense = min(monthly_salary * 0.05, 500_000)

    # Penghasilan Neto Bulanan
    net_monthly_income = monthly_salary - job_expense - pension_contribution

    # Penghasilan Neto Tahunan
    annual_net_income = net_monthly_income * 12

    # Penghasilan Kena Pajak (PKP)
    pkp = max(annual_net_income - ptkp, 0)

    # Perhitungan Pajak Progresif
    tax = 0
    if pkp <= 50_000_000:
        tax = pkp * 0.05
    elif pkp <= 250_000_000:
        tax = (50_000_000 * 0.05) + ((pkp - 50_000_000) * 0.15)
    elif pkp <= 500_000_000:
        tax = (50_000_000 * 0.05) + (200_000_000 * 0.15) + ((pkp - 250_000_000) * 0.25)
    else:
        tax = (50_000_000 * 0.05) + (200_000_000 * 0.15) + (250_000_000 * 0.25) + ((pkp - 500_000_000) * 0.30)

    # Hitung Tarif Efektif Rata-rata (TER)
    ter = tax / pkp if pkp > 0 else 0

    # Pajak Bulanan
    monthly_tax = ter * (annual_net_income / 12)
    return round(monthly_tax, 2)

def calculate_ppn(dpp, tarif_ppn=0.11):
    """
    Hitung PPN berdasarkan DPP dan tarif PPN.
    Args:
        dpp (float): Dasar Pengenaan Pajak (nilai sebelum PPN).
        tarif_ppn (float): Tarif PPN (default 0.11 untuk 11%).
    Returns:
        float: Nilai PPN.
    """
    return round(dpp * tarif_ppn, 2)

def calculate_custom_ppn(
    fee:float,
    tarif_ppn:Optional[float]=0.12,
):
    formula = tarif_ppn * (fee * 11/12)
    return formula

def calculate_custom_pph_23(
    fee:float,
    tarif_pph:Optional[float]=0.02,
):
    """
    fee adalah nilai agency fee
    """
    formula = fee * tarif_pph
    return formula

def calculate_pkp(monthly_salary, ptkp, pension_contribution=0):
    """
    Hitung Penghasilan Kena Pajak (PKP) setahun.
    Args:
        monthly_salary (float): Gaji bulanan (bruto).
        ptkp (float): Penghasilan Tidak Kena Pajak (PTKP).
        pension_contribution (float): Iuran pensiun bulanan (opsional).
    Returns:
        float: PKP setahun (dibulatkan ke ribuan terdekat sesuai aturan).
    """
    # Penghasilan bruto setahun
    annual_gross = monthly_salary * 12

    # Biaya jabatan: 5% dari bruto setahun, maksimal 6.000.000 per tahun
    job_expense = min(annual_gross * 0.05, 6_000_000)

    # Iuran pensiun setahun
    annual_pension = pension_contribution * 12

    # Penghasilan neto setahun
    annual_net = annual_gross - job_expense - annual_pension

    # PKP
    pkp = annual_net - ptkp

    # PKP tidak boleh negatif
    pkp = max(pkp, 0)

    # PKP dibulatkan ke ribuan terdekat ke bawah (sesuai aturan)
    pkp = (pkp // 1000) * 1000

    return pkp

def calculate_pph21_without_pension(monthly_salary, ptkp):
    # Biaya Jabatan: 5% dari penghasilan bruto, maksimal Rp500.000
    job_expense = min(monthly_salary * 0.05, 500_000)

    # Penghasilan Neto Bulanan
    net_monthly_income = monthly_salary - job_expense

    # Penghasilan Neto Tahunan
    annual_net_income = net_monthly_income * 12

    # Penghasilan Kena Pajak (PKP)
    pkp = max(annual_net_income - ptkp, 0)

    # Perhitungan Pajak Progresif
    tax = 0
    if pkp <= 50_000_000:
        tax = pkp * 0.05
    elif pkp <= 250_000_000:
        tax = (50_000_000 * 0.05) + ((pkp - 50_000_000) * 0.15)
    elif pkp <= 500_000_000:
        tax = (50_000_000 * 0.05) + (200_000_000 * 0.15) + ((pkp - 250_000_000) * 0.25)
    else:
        tax = (50_000_000 * 0.05) + (200_000_000 * 0.15) + (250_000_000 * 0.25) + ((pkp - 500_000_000) * 0.30)

    # Hitung Tarif Efektif Rata-rata (TER)
    ter = tax / pkp if pkp > 0 else 0

    # Pajak Bulanan
    monthly_tax = ter * (annual_net_income / 12)
    return round(monthly_tax, 2)


def calculate_pph21_excel_style(pkp):
    """
    Hitung pajak progresif sesuai rumus Excel:
    - 5% untuk PKP sampai 60 juta
    - 15% untuk PKP di atas 60 juta sampai 250 juta
    - 25% untuk PKP di atas 250 juta sampai 500 juta
    - 30% untuk PKP di atas 500 juta
    """
    if pkp <= 60_000_000:
        pajak = pkp * 0.05
    elif pkp <= 250_000_000:
        pajak = 3_000_000 + (pkp - 60_000_000) * 0.15
    elif pkp <= 500_000_000:
        pajak = 31_500_000 + (pkp - 250_000_000) * 0.25
    else:
        pajak = 94_000_000 + (pkp - 500_000_000) * 0.30
    return pajak