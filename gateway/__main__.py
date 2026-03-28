import argparse

from gateway import SemanticGateway


def main() -> None:
    parser = argparse.ArgumentParser(
        description="ACE Semantic Gateway CLI"
    )
    parser.add_argument("prompt", help="Input prompt to evaluate")
    parser.add_argument(
        "--ace-threshold",
        type=float,
        default=0.35,
        help="Threshold below which the gateway answers directly",
    )
    parser.add_argument(
        "--deep-threshold",
        type=float,
        default=0.65,
        help="Threshold below which the gateway returns clarify",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose gateway logs",
    )

    args = parser.parse_args()

    gateway = SemanticGateway(
        ace_threshold=args.ace_threshold,
        deep_threshold=args.deep_threshold,
        verbose=args.verbose,
    )

    result = gateway.process_request(prompt=args.prompt)

    print("ACE Semantic Gateway")
    print("--------------------")
    print("Decision:", result.decision)
    print("Path:", result.path)
    print("Score:", result.score)
    print("Response:", result.response)
    print("Metadata:", result.metadata)


if __name__ == "__main__":
    main()