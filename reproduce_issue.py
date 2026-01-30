import pandas as pd
import requests
import json

BENEFICIARY_MAP = {
    2: "Pregnant Women",
    3: "Children 5-9 Months",
    4: "Children Aged 5-9 Years  (60 Months)",
    5: "Adolescent Girls 10-19 Years",
    6: "Adolescent Boys 10-19 Years",
    7: "Women Of Reproductive Age"
}

def classify_anemia_who(hgb, age, gender, beneficiary):
    if pd.isna(hgb) or hgb is None: return "incomplete"
    try: hgb = float(hgb)
    except: return "incomplete"
    beneficiary_str = str(beneficiary).lower().strip() if not pd.isna(beneficiary) else ""
    if "pregnant" in beneficiary_str:
        if hgb >= 11.0: return "normal"
        elif hgb >= 10.0: return "mild"
        elif hgb >= 7.0: return "moderate"
        else: return "severe"
    # Simplified for the sake of reproduction
    return "normal" if hgb >= 11 else "mild"

def load_data_sim():
    DATA_SOURCE_URL = "https://script.google.com/macros/s/AKfycbxfqwdEiWRaSUpfSQoE5V_WBbCT74vM3Wj9F1rNM354EieRMYsMWtGnU_sRegLua50Ycg/exec"
    r = requests.get(DATA_SOURCE_URL, timeout=10)
    data_json = r.json()
    if isinstance(data_json, dict) and 'data' in data_json:
        df = pd.DataFrame(data_json['data'])
    else:
        df = pd.DataFrame(data_json)
    
    df.columns = df.columns.str.strip()
    
    if "HGB" in df.columns:
        df["HGB"] = pd.to_numeric(df["HGB"], errors="coerce")
    
    if "Benificiery" in df.columns:
        df["Benificiery"] = pd.to_numeric(df["Benificiery"], errors='coerce')
        df["Benificiery"] = df["Benificiery"].map(BENEFICIARY_MAP).fillna(df["Benificiery"])
        df["Benificiery"] = df["Benificiery"].astype(str).str.title()

    if "HGB" in df.columns:
        df["anemia_category"] = df.apply(
            lambda row: classify_anemia_who(
                row.get("HGB"),
                row.get("Age"),
                row.get("Gender"),
                row.get("Benificiery")
            ),
            axis=1
        )
    return df

def test_filtering():
    print("Fetching data...")
    df_full = load_data_sim()
    print(f"Total records fetched: {len(df_full)}")
    print("Unique Beneficiaries:", df_full["Benificiery"].unique())
    print("Unique Anemia Categories (before filter):", df_full["anemia_category"].unique())

    # Simulate filtering
    benificiery = ["Pregnant Women"] # Example
    anemia = ["mild"] # Example (dropdown values are lowercase in value but label is capitalized)

    print(f"\nApplying filters: Beneficiary={benificiery}, Anemia={anemia}")
    
    df = df_full.copy()
    if benificiery:
        df = df[df["Benificiery"].isin(benificiery)]
        print(f"After Beneficiary filter: {len(df)}")
    
    if anemia:
        df = df[df["anemia_category"].isin(anemia)]
        print(f"After Anemia filter: {len(df)}")

    print("\nResulting Anemia Categories in filtered set:", df["anemia_category"].unique())
    print("Resulting Beneficiaries in filtered set:", df["Benificiery"].unique())

    if len(df["anemia_category"].unique()) > 1 and anemia:
        print("BUG REPRODUCED: Filter failed to limit anemia categories!")
    elif len(df) == 0:
        print("Notice: No records match the criteria.")
    else:
        print("Logic seems correct in this isolation test.")

if __name__ == "__main__":
    test_filtering()
