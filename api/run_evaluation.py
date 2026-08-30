import json
import requests

API_URL = "http://127.0.0.1:8000/tickets"


def run_evaluation():
    with open("eval_dataset.json", "r") as f:
        dataset = json.load(f)

    results = []
    category_correct = 0
    urgency_correct = 0

    print(f"Running evaluation on {len(dataset)} test tickets...\n")

    for ticket in dataset:
        response = requests.post(
            API_URL,
            data={
                "sender": ticket["sender"],
                "subject": ticket["subject"],
                "body": ticket["body"]
            }
        )
        response_data = response.json()

        predicted_category = response_data.get("category")
        predicted_urgency = response_data.get("urgency")
        expected_category = ticket["expected_category"]
        expected_urgency = ticket["expected_urgency"]

        cat_ok = predicted_category == expected_category
        urg_ok = predicted_urgency == expected_urgency

        if cat_ok:
            category_correct += 1
        if urg_ok:
            urgency_correct += 1

        results.append({
            "id": ticket["id"],
            "subject": ticket["subject"],
            "expected_category": expected_category,
            "predicted_category": predicted_category,
            "category_correct": cat_ok,
            "expected_urgency": expected_urgency,
            "predicted_urgency": predicted_urgency,
            "urgency_correct": urg_ok
        })

        cat_status = "PASS" if cat_ok else "FAIL"
        urg_status = "PASS" if urg_ok else "FAIL"
        print(f"Ticket {ticket['id']}: category [{cat_status}] expected='{expected_category}' got='{predicted_category}' | urgency [{urg_status}] expected='{expected_urgency}' got='{predicted_urgency}'")

    total = len(dataset)
    print(f"\n--- Summary ---")
    print(f"Category accuracy: {category_correct}/{total} ({category_correct/total*100:.1f}%)")
    print(f"Urgency accuracy: {urgency_correct}/{total} ({urgency_correct/total*100:.1f}%)")

    with open("eval_results.json", "w") as f:
        json.dump({
            "category_accuracy_percent": category_correct / total * 100,
            "urgency_accuracy_percent": urgency_correct / total * 100,
            "total": total,
            "results": results
        }, f, indent=2)

    print("\nFull results saved to eval_results.json")


if __name__ == "__main__":
    run_evaluation()
    