"""Define and register a custom eval suite, then run an agent against it."""

from __future__ import annotations

from agentbench.suites.base import EvalSuite, EvalTask

# Define your own tasks. The framework only requires id / input / expected_output.
my_suite = EvalSuite(
    name="my_custom_suite",
    version="0.1.0",
    description="A toy suite for demonstration.",
    tasks=[
        EvalTask(
            id="custom-1",
            input={"question": "What is 2 + 2?"},
            expected_output="4",
            difficulty="easy",
            scorer_type="exact",
        ),
        EvalTask(
            id="custom-2",
            input={"question": "Capital of France?"},
            expected_output="Paris",
            difficulty="easy",
            scorer_type="exact",
        ),
    ],
)


if __name__ == "__main__":
    from agentbench.runner import EvalRunner
    from agentbench.suites import register_suite
    from examples.simple_agent import agent

    register_suite(my_suite)
    report = EvalRunner(agent, my_suite).run()
    print(report.model_dump_json(indent=2))
