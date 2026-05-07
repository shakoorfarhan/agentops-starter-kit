from agentops_starter import (
    Agent,
    AgentConfig,
    EvalCase,
    FakeModelProvider,
    default_tool_registry,
    run_eval,
)


def test_run_eval_scores_cases() -> None:
    agent = Agent(
        model=FakeModelProvider(),
        tools=default_tool_registry(),
        config=AgentConfig(max_steps=4),
    )

    result = run_eval(
        agent,
        [
            EvalCase(
                name="uses-tools",
                task="Research agent testing and save notes",
                assert_result=lambda run: run.success and "Completed" in run.final_answer,
            )
        ],
    )

    assert result.total == 1
    assert result.passed == 1
    assert result.score == 1.0
