from agentops_starter import Agent, AgentConfig, FakeModelProvider, default_tool_registry


def test_agent_completes_with_tool_context() -> None:
    agent = Agent(
        model=FakeModelProvider(),
        tools=default_tool_registry(),
        config=AgentConfig(max_steps=4),
    )

    result = agent.run("Summarize this research note")

    assert result.success is True
    assert result.final_answer == "Completed the task using available tools."
    assert any(event.kind == "tool_call" for event in result.trace.events)
    assert result.trace.total_cost_usd > 0


def test_agent_stops_when_budget_exceeded() -> None:
    agent = Agent(
        model=FakeModelProvider(),
        tools=default_tool_registry(),
        config=AgentConfig(max_steps=4, budget_usd=0.0),
    )

    result = agent.run("Summarize this research note")

    assert result.success is False
    assert "budget" in result.final_answer.lower()
