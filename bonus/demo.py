"""Demo script for Bonus Challenge: HybridMemoryAgent.

Demonstrates 5 distinct memory retrieval patterns combining episodic memories and Feast profile features.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add repo root to sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from bonus.agent import HybridMemoryAgent


def main() -> int:
    print("=" * 70)
    print("DEMO: HybridMemoryAgent (Episodic Vector Memory + Feast Feature Store)")
    print("=" * 70)

    agent = HybridMemoryAgent()

    user_id = "u_001"
    print(f"\n1. Ingesting user reading history & episodic notes for {user_id}...")

    sample_memories = [
        "Đã đọc bài viết về Kubernetes Ingress Controller và cấu hình TLS cert-manager trên EKS cluster.",
        "Đã ghi chú về kiến trúc microservices: nên dùng gRPC cho inter-service communication và Kafka cho event-driven.",
        "Đã nghiên cứu giải pháp Auto Scaling: Horizontal Pod Autoscaler (HPA) kết hợp Cluster Autoscaler giúp tối ưu chi phí hạ tầng.",
        "Đã đọc tài liệu bảo mật đám mây: nguyên tắc Least Privilege, mã hoá KMS AES-256 cho S3 bucket và IAM role cho ServiceAccount.",
        "Đã hoàn thành khoá học về CI/CD pipeline với GitHub Actions và ArgoCD triển khai GitOps.",
    ]

    for mem in sample_memories:
        agent.remember(mem, user_id=user_id)
    print(f"   -> Successfully ingested {len(sample_memories)} episodic memory notes.\n")

    queries = [
        ("Query 1 (Direct Episodic Hit)", "Tôi đã đọc gì về Kubernetes?"),
        ("Query 2 (Profile-Guided Recommendation)", "Recommend đọc gì tiếp"),
        ("Query 3 (Activity & Velocity Aware)", "Tôi đang quan tâm gì gần đây?"),
        ("Query 4 (Paraphrase Semantic Match)", "Tài liệu về tự động mở rộng hạ tầng?"),
        ("Query 5 (Mixed Hybrid & Security Context)", "Cho tôi summary cloud security"),
    ]

    for tag, q in queries:
        print("-" * 70)
        print(f"[{tag}]")
        print(f"Query: \"{q}\"")
        res = agent.recall(q, user_id=user_id, top_k=2)
        print("\n[Assembled Context Generated for LLM]:")
        print(res["assembled_prompt"])
        print()

    print("=" * 70)
    print("DEMO COMPLETED SUCCESSFULLY (Exit Code 0)")
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
