import sys

from gateway import SemanticGateway


def main() -> None:
    if len(sys.argv) < 2:
        print('Usage: python -m gateway "your prompt here"')
        raise SystemExit(1)

    prompt = sys.argv[1]

    gateway = SemanticGateway()
    result = gateway.process_request(prompt=prompt)

    print("ACE Semantic Gateway")
    print("--------------------")
    print("Decision:", result.decision)
    print("Path:", result.path)
    print("Score:", result.score)
    print("Response:", result.response)
    print("Metadata:", result.metadata)


if __name__ == "__main__":
    main()
