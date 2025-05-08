# Qiita memo

- `self.session.list_tools()`を実行すると，MCP サーバーの Tool の情報を全て取得できるっぽい．
  - https://github.com/ren8k/amazon-bedrock-agent-samples/blob/9ad5be807191afdaf19d70830448f67dbb971db8/src/InlineAgent/src/InlineAgent/tools/mcp.py#L155
  - https://www.gradio.app/guides/building-an-mcp-client-with-gradio
- Return Control を利用する場合，`ActionGroup` の `customControl` 値として `RETURN_COTROL` を指定する必要あり
  - https://docs.aws.amazon.com/bedrock/latest/userguide/agents-returncontrol.html
- `ActionGroup` の定義は以下で実行している．
  - https://github.com/ren8k/amazon-bedrock-agent-samples/blob/e82882ee0f8070a9c60a10a3c480e0f4242c869b/src/InlineAgent/src/InlineAgent/action_group/action_group.py#L275
- Return Control により返却されたツールは以下で実行される．

  - https://github.com/ren8k/amazon-bedrock-agent-samples/blob/e82882ee0f8070a9c60a10a3c480e0f4242c869b/src/InlineAgent/src/InlineAgent/agent/process_roc.py#L94
  - 加え，Tool の実行は以下で行っている．
    - [本ステート](https://github.com/ren8k/amazon-bedrock-agent-samples/blob/515712c1b525f1d4fe40c67df06ea4234a09acee/src/InlineAgent/examples/delete_mcp_manual.py#L61)で，`MCPStdio.create`を実行する
    - すると，[本ステート](https://github.com/ren8k/amazon-bedrock-agent-samples/blob/9ad5be807191afdaf19d70830448f67dbb971db8/src/InlineAgent/src/InlineAgent/tools/mcp.py#L215)が実行される
    - すると，`await self.session.call_tool`を実行する関数`create_callable`がセットされる．
      - https://github.com/ren8k/amazon-bedrock-agent-samples/blob/9ad5be807191afdaf19d70830448f67dbb971db8/src/InlineAgent/src/InlineAgent/tools/mcp.py#L107
    - すると，以下で実行されるツールが選択される
      - https://github.com/ren8k/amazon-bedrock-agent-samples/blob/e82882ee0f8070a9c60a10a3c480e0f4242c869b/src/InlineAgent/src/InlineAgent/agent/process_roc.py#L75

- Amazon Bedrock Agent の lambda の payload サイズは最大 25MB
  - https://docs.aws.amazon.com/ja_jp/bedrock/latest/userguide/agents-lambda.html
  - MCP で画像生成する場合，Agent のレスポンスに画像を含めると，トークンサイズが大きすぎてエラーになる（加えてトークンの無駄遣いになる．）
  - Bedrock Agent では，画像生成結果を S3 などに保存し，その結果を表示することが推奨かも．
  - https://qiita.com/harusamet/items/7310d5983dab8f1a4b8a
