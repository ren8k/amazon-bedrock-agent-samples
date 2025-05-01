# Qiita memo

- `self.session.list_tools()`を実行すると，MCP サーバーの Tool の情報を全て取得できるっぽい．
  - https://github.com/ren8k/amazon-bedrock-agent-samples/blob/9ad5be807191afdaf19d70830448f67dbb971db8/src/InlineAgent/src/InlineAgent/tools/mcp.py#L155
  - https://www.gradio.app/guides/building-an-mcp-client-with-gradio
- Return Control を利用する場合，ActionGroup の customControl 値として RETURN_COTROL を指定する必要あり
  - https://docs.aws.amazon.com/bedrock/latest/userguide/agents-returncontrol.html
- Action Group の定義は以下で実行している．
  - https://github.com/ren8k/amazon-bedrock-agent-samples/blob/e82882ee0f8070a9c60a10a3c480e0f4242c869b/src/InlineAgent/src/InlineAgent/action_group/action_group.py#L275
