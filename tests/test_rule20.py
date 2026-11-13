from src.part2_agent import agent_hooks, agent_prompt


def test_role_holder_rule_is_in_the_agent_and_the_critic_prompts():
    for text in (agent_prompt.SYSTEM_TASK, agent_hooks.CRITIC_SYSTEM):
        assert "Registers of people or role holders" in text and "entity.date_registered" in text
    assert "rule 20) is BLOCKING" in agent_hooks.CRITIC_SYSTEM
