import asyncio

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from InlineAgent.agent.process_roc import ProcessROC


# Step 1: Define tools with Docstring
def get_current_weather(location: str, state: str, unit: str = "fahrenheit") -> dict:
    """
    Get the current weather in a given location.

    Parameters:
        location: The city, e.g., San Francisco
        state: The state eg CA
        unit: The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"
    """
    return "Weather is 70 fahrenheit"


# Step 2: Logically group tools together
weather_action_group = ActionGroup(
    name="WeatherActionGroup",
    description="This is action group to get weather",
    tools=[get_current_weather],
)

# Step 3: Define agent
agent = InlineAgent(
    foundation_model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
    instruction="You are a friendly assistant that is responsible for getting the current weather.",
    action_groups=[weather_action_group],
    agent_name="MockAgent",
)


# Step 4: Invoke agent
async def main():
    agent_answer = ""
    session_id = "123"
    session_state = {}

    while not agent_answer:
        response = await agent.invoke(
            input_text="What is the weather of NY? ",
            session_id=session_id,
            session_state=session_state,
            process_response=False,
        )

        event_stream = response["completion"]
        for event in event_stream:
            print("=== Event Stream ===")
            print(event)
            print("========================")
            if "returnControl" in event:
                session_state = await ProcessROC.process_roc(
                    inlineSessionState={},
                    roc_event=event["returnControl"],
                    tool_map=agent.tool_map,
                )
                print("=== Session State ===")
                print(session_state)
                print("========================")
            # Get Final Answer
            if "chunk" in event:
                agent_answer = event["chunk"]["bytes"].decode("utf8")
                print("=== Agent Answer ===")
                print(agent_answer)
                print("========================")
                break

    return agent_answer


if __name__ == "__main__":
    result = asyncio.run(main())
    print("\nFinal Answer:", result)
