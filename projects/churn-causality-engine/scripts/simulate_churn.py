"""Demo driver for churn analysis."""
import argparse
import httpx

CUSTOMERS = [
    ("cus_at_risk_01", "Stalled onboarding + failed payment"),
    ("cus_healthy_02", "Healthy long-tenure customer"),
    ("cus_slipping_03", "Disengaged after first value"),
]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8001")
    args = parser.parse_args()

    for cid, label in CUSTOMERS:
        print(f"\n=== {label} ({cid}) ===")
        try:
            r = httpx.get(f"{args.url.rstrip('/')}/analyze/{cid}", timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as exc:
            print(f"  ! {exc}")
            continue
        print(f"  risk       : {data['risk_level']} ({data['churn_risk_score']})")
        print(f"  mrr        : ${data['mrr_usd']}")
        for cause in data.get("root_causes", [])[:2]:
            print(f"  cause      : {cause['title']} — {cause['explanation'][:80]}...")
    print(f"\nDashboard: {args.url}/")


if __name__ == "__main__":
    main()
