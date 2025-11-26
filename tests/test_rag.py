import os
import sys

# Add the project root to the python path so imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent.rag.retrieval import retrieve_docs, retriever


def test_rag():
    print("=== 🔎 Testing RAG Retrieval ===")

    # Test 1: Policy Question
    q1 = "How many days for returning beverages?"
    print(f"\nQuery: {q1}")
    results = retriever.retrieve(q1, k=1)

    if results:
        top_hit = results[0]
        print(f"✅ Top Hit ID: {top_hit['id']}")
        print(f"   Content: {top_hit['content'][:50]}...")
        print(f"   Score: {top_hit['score']:.4f}")

        # Verification based on your docs/product_policy.md
        if "Beverages" in top_hit["content"] and "14 days" in top_hit["content"]:
            print("   -> Accuracy Check: PASSED")
        else:
            print("   -> Accuracy Check: FAILED (Did not find beverage policy)")
    else:
        print("❌ No results found")

    # Test 2: Formatting for LLM
    print("\n--- Testing String Formatting ---")
    formatted = retrieve_docs("Summer Beverages 1997")
    print(formatted)


if __name__ == "__main__":
    test_rag()
