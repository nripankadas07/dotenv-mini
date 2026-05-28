        # Project Brief

        dotenv-mini exists to solve a narrow, inspectable developer-tooling problem:
        Strict, predictable .env reader/writer for Python; no $VAR interpolation, full quoting/escape round-trip. Zero dependencies.

        ## Portfolio Role

        This repository is part of the local-first engineering portfolio around
        agentic AI infrastructure, evaluation, parsing, safety boundaries, and
        small tools that can be understood from a fresh source checkout. It is not
        here to inflate repository count; it should either provide a reusable
        primitive, a benchmark surface, or a concrete local workflow.

        Topics: config, dotenv, env-file, python, zero-dependencies

        ## Current Gates

        - Latest completed CI: success
        - Source files counted by audit: 2
        - Test files counted by audit: 3
        - Latest release: not release-tracked yet
        - License: MIT

        ## Upgrade Path

        - Add adversarial conformance fixtures and malformed-input cases.
- Generate metamorphic tests with SpecMutate for round-trip, idempotence, and normalization invariants.
- Document resource limits, error taxonomy, and any intentionally unsupported parts of the format.

        ## Reviewer Contract

        A serious reviewer should be able to clone the repository, read the
        README and this brief, run the tests, and understand exactly what is
        claimed. Future work should prefer deeper correctness, better fixtures,
        clearer limits, and stronger local demos over broad feature lists.
