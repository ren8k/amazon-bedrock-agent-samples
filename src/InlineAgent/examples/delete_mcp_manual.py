from mcp import StdioServerParameters

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from InlineAgent.agent.process_roc import ProcessROC
from InlineAgent.tools import MCPStdio


def handle_trace_event(event):
    """トレースイベントの処理を行う"""
    if "orchestrationTrace" not in event["trace"]["trace"]:
        return

    trace = event["trace"]["trace"]["orchestrationTrace"]

    # 「モデル入力」トレースの表示 (多分不要)
    # if "modelInvocationInput" in trace:
    #     input_trace = trace["modelInvocationInput"]["text"]
    #     try:
    #         print("入力")
    #         print(json.loads(input_trace))
    #     except json.JSONDecodeError:
    #         print(input_trace)

    # 「モデル出力」トレースの表示（多分不要）
    # if "modelInvocationOutput" in trace:
    #     output_trace = trace["modelInvocationOutput"]["rawResponse"]["content"]
    #     print("出力")
    #     print(output_trace)

    # 「根拠」トレースの表示
    if "rationale" in trace:
        print("Thinking")
        print(trace["rationale"]["text"])

    # 「ツール呼び出し」トレースの表示
    if "invocationInput" in trace:
        # invocation_type = trace["invocationInput"]["type"]
        print("Use Tool")
        print(trace["invocationInput"]["actionGroupInvocationInput"])
        # if invocation_type == "ACTION_GROUP":
        #     print(trace["invocationInput"]["actionGroupInvocationInput"])
        # else:
        #     pass

    # 「観察」トレースの表示
    if "observation" in trace:
        print(trace["observation"]["type"])


# Step 1: Define MCP stdio parameters
server_params = StdioServerParameters(
    command="uvx",
    args=["awslabs.aws-documentation-mcp-server@latest"],
    env={"FASTMCP_LOG_LEVEL": "ERROR"},
)


async def main() -> None:
    # Step 2: Create MCP Client
    time_mcp_client = await MCPStdio.create(server_params=server_params)

    try:
        # Step 3: Define an action group
        aws_doc_action_group = ActionGroup(
            name="AwsDocSurveyActionGroup",
            description="Helps user survey aws doc.",
            mcp_clients=[time_mcp_client],
            # argument_key="Args:",
        )
        print("aws_doc_action_group", aws_doc_action_group)

        # Step 4: Invoke agent
        agent = InlineAgent(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            # Step 4.2: Concise instruction
            instruction="""You are a friendly assistant that is responsible for resolving user queries. """,
            # Step 4.3: Provide the agent name and action group
            agent_name="aws_doc_agent",
            action_groups=[aws_doc_action_group],
        )
        print("#" * 100)
        print(agent.action_groups[0].get("functionSchema"))
        print("#" * 100)

        # ここから修正部分 - descriptionの長さチェックと切り詰め
        function_schema = agent.action_groups[0].get("functionSchema")

        # 各schemaをチェックして長すぎるdescriptionを切り詰める
        for schema in function_schema["functions"]:
            original_description = schema["description"]
            print(schema["name"])

            # descriptionが1200文字を超える場合、切り詰める
            if len(original_description) > 1200:
                # 1196文字まで切り取り、末尾に「...」を追加
                truncated_description = original_description[:1196] + "..."
                schema["description"] = truncated_description
                print(
                    f"Description truncated from {len(original_description)} to 1200 characters"
                )

            print(schema)
            print(len(schema["description"]))
            print(schema["parameters"])
            print("#" * 100)

        # 修正したfunction_schemaをaction_groupsに戻す
        agent.action_groups[0]["functionSchema"] = function_schema

        agent_answer = ""
        session_id = "112"  # TODO: uuidにしたほうが良いかも
        session_state = {}
        while not agent_answer:
            response = await agent.invoke(
                input_text="AWS Bedrock Inline Agentについて，具体的にサンプル実装を書いて下さい．",
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
                # print("========================")
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

    finally:
        await time_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
    asyncio.run(main())
