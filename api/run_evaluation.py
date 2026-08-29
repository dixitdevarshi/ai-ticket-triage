import json
import requests

API_URL = "http://127.0.0.1:8000/tickets"


def run_evaluation():
    with open("eval_dataset.json", "r") as f:
        dataset = json.load(f)

    results = []
    correct = 0

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

        predicted = response_data.get("category")
        expected = ticket["expected_category"]
        is_correct = predicted == expected

        if is_correct:
            correct += 1

        results.append({
            "id": ticket["id"],
            "subject": ticket["subject"],
            "expected": expected,
            "predicted": predicted,
            "correct": is_correct
        })

        status = "PASS" if is_correct else "FAIL"
        print(f"[{status}] Ticket {ticket['id']}: expected='{expected}', got='{predicted}'")

    accuracy = (correct / len(dataset)) * 100

    print(f"\n--- Summary ---")
    print(f"Accuracy: {correct}/{len(dataset)} ({accuracy:.1f}%)")

    with open("eval_results.json", "w") as f:
        json.dump({
            "accuracy_percent": accuracy,
            "correct": correct,
            "total": len(dataset),
            "results": results
        }, f, indent=2)

    print("\nFull results saved to eval_results.json")


if __name__ == "__main__":
    run_evaluation()