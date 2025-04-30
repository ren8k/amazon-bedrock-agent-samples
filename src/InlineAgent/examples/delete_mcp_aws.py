from mcp import StdioServerParameters

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent
from InlineAgent.tools import MCPStdio

# Step 1: Define MCP stdio parameters
server_params = StdioServerParameters(
    command="uvx",
    args=["awslabs.aws-documentation-mcp-server@latest"],
    env={"FASTMCP_LOG_LEVEL": "ERROR"},
)


async def main():
    # Step 2: Create MCP Client
    time_mcp_client = await MCPStdio.create(server_params=server_params)

    try:
        # Step 3: Define an action group
        time_action_group = ActionGroup(
            name="AwsDocSurveyActionGroup",
            description="Helps user survey aws doc.",
            mcp_clients=[time_mcp_client],
            # argument_key="Args:",
        )
        print("time_action_group", time_action_group)

        # Step 4: Invoke agent
        agent = InlineAgent(
            # Step 4.1: Provide the model
            foundation_model="us.anthropic.claude-3-5-sonnet-20241022-v2:0",
            # Step 4.2: Concise instruction
            instruction="""You are a friendly assistant that is responsible for resolving user queries. """,
            # Step 4.3: Provide the agent name and action group
            agent_name="aws_doc_agent",
            action_groups=[time_action_group],
        )
        print("#" * 100)
        # print(time_action_group)
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

        await agent.invoke(
            input_text="AWS Bedrock Inline Agentについて，具体的にサンプル実装を書いて下さい．"
        )

    finally:
        await time_mcp_client.cleanup()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
