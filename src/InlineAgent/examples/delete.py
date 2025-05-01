import asyncio
import json

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


def handle_trace_event(event):
    """トレースイベントの処理を行う"""
    if "orchestrationTrace" not in event["trace"]["trace"]:
        return

    trace = event["trace"]["trace"]["orchestrationTrace"]

    # 「モデル入力」トレースの表示
    if "modelInvocationInput" in trace:
        input_trace = trace["modelInvocationInput"]["text"]
        try:
            print("入力")
            print(json.loads(input_trace))
        except json.JSONDecodeError:
            print(input_trace)

    # 「モデル出力」トレースの表示
    if "modelInvocationOutput" in trace:
        output_trace = trace["modelInvocationOutput"]["rawResponse"]["content"]
        print("出力")
        print(output_trace)

    # 「根拠」トレースの表示
    if "rationale" in trace:
        print("根拠")
        print(trace["rationale"]["text"])

    # 「ツール呼び出し」トレースの表示
    if "invocationInput" in trace:
        # invocation_type = trace["invocationInput"]["type"]
        print("ツール呼び出し")
        print(trace["invocationInput"]["actionGroupInvocationInput"])
        # if invocation_type == "ACTION_GROUP":
        #     print(trace["invocationInput"]["actionGroupInvocationInput"])
        # else:
        #     pass

    # 「観察」トレースの表示
    if "observation" in trace:
        print(trace["observation"]["type"])


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
print(agent.action_groups)


# Step 4: Invoke agent
async def main():
    agent_answer = ""
    session_id = "112"
    session_state = {}

    while not agent_answer:
        response = await agent.invoke(
            input_text="What is the weather of NY and SF? Please search twice.",
            session_id=session_id,
            session_state=session_state,
            process_response=False,
            # end_session=True,
        )

        event_stream = response["completion"]
        for event in event_stream:
            # トレース情報の処理
            # print("=== Event Stream ===")
            # print(event)
            print("========================")
            if "trace" in event:
                handle_trace_event(event)
            if "returnControl" in event:
                session_state = await ProcessROC.process_roc(
                    inlineSessionState={},
                    roc_event=event["returnControl"],
                    tool_map=agent.tool_map,
                )
                print("=== Session State ===")
                print("Return Control Result")
                print(
                    session_state["returnControlInvocationResults"][0][
                        "functionResult"
                    ]["responseBody"]["TEXT"]["body"]
                )
                print("========================")
            # Get Final Answer
            if "chunk" in event:
                agent_answer = event["chunk"]["bytes"].decode("utf8")
                print("=== Agent Answer ===")
                print(agent_answer)
                print("========================")
                break

    return agent_answer


# メイン処理の実行
if __name__ == "__main__":
    result = asyncio.run(main())
    print("\nFinal Answer:", result)
