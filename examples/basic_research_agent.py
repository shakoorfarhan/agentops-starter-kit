"""Run a deterministic research-style agent without API keys."""

from agentops_starter import Agent, AgentConfig, FakeModelProvider, default_tool_registry


def main() -> None:
    agent = Agent(
        model=FakeModelProvider(),
        tools=default_tool_registry(),
        config=AgentConfig(max_steps=4, budget_usd=0.05),
    )

    result = agent.run("Research AI agent reliability patterns and save a short note")
    print(result.final_answer)
    print(result.trace.summary())


if __name__ == "__main__":
    main()
