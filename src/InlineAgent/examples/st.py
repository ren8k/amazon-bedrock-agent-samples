import asyncio
import json
import uuid

import streamlit as st

from InlineAgent.action_group import ActionGroup
from InlineAgent.agent import InlineAgent

# ストリームリットのUIを設定
st.set_page_config(page_title="Bedrock Agent Visualizer", layout="wide")
st.title("AWS Bedrock Agent Visualizer")

# セッション状態の初期化
if "session_id" not in st.session_state:
    st.session_state.session_id = None
if "agent" not in st.session_state:
    st.session_state.agent = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "processing" not in st.session_state:
    st.session_state.processing = False
if "input_to_process" not in st.session_state:
    st.session_state.input_to_process = None


# カスタム関数でトレースを処理してStreamlitに表示するためのラッパー
def get_current_weather(location: str, state: str, unit: str = "fahrenheit") -> dict:
    """
    Get the current weather in a given location.

    Parameters:
        location: The city, e.g., San Francisco
        state: The state eg CA
        unit: The unit to use, e.g., fahrenheit or celsius. Defaults to "fahrenheit"
    """
    return f"Weather for {location}, {state} is 70 {unit}"


# エージェント初期化
def initialize_agent():
    # アクショングループの定義
    weather_action_group = ActionGroup(
        name="WeatherActionGroup",
        description="This is action group to get weather",
        tools=[get_current_weather],
    )

    # エージェントの定義
    agent = InlineAgent(
        foundation_model="us.anthropic.claude-3-5-haiku-20241022-v1:0",
        instruction="You are a friendly assistant that is responsible for getting the current weather.",
        action_groups=[weather_action_group],
        agent_name="WeatherAgent",
    )

    return agent


# トレース情報を取得・表示するためのカスタムinvoke関数
async def process_user_input(agent, input_text):
    # 処理中フラグをセット
    st.session_state.processing = True

    # ユーザー入力をメッセージリストに追加
    st.session_state.messages.append({"role": "user", "content": input_text})

    # 進捗状況を表示
    progress_placeholder = st.empty()
    with progress_placeholder.status("エージェントが処理中..."):
        try:
            # セッションIDを生成または再利用
            session_id = (
                st.session_state.session_id
                if st.session_state.session_id
                else str(uuid.uuid4())
            )
            st.session_state.session_id = session_id

            # トレース情報を取得するために生のレスポンスを取得
            response = await agent.invoke(
                input_text=input_text,
                enable_trace=True,
                session_id=session_id,
                process_response=False,
            )

            agent_answer = ""
            thought_captured = False

            # イベントストリームを処理
            event_stream = response["completion"]
            for event in event_stream:
                # トレース情報の処理
                print("=== Event Stream ===")
                print(event)
                print("========================")
                if "trace" in event and "trace" in event["trace"]:
                    trace_data = event["trace"]["trace"]

                    # 思考過程の取得
                    if (
                        "orchestrationTrace" in trace_data
                        and "rationale" in trace_data["orchestrationTrace"]
                    ):
                        thought = trace_data["orchestrationTrace"]["rationale"]["text"]
                        if not thought_captured:
                            st.session_state.messages.append(
                                {"role": "thought", "content": thought}
                            )
                            thought_captured = True

                    # ツール使用情報の取得
                    if (
                        "orchestrationTrace" in trace_data
                        and "invocationInput" in trace_data["orchestrationTrace"]
                    ):
                        if (
                            "actionGroupInvocationInput"
                            in trace_data["orchestrationTrace"]["invocationInput"]
                        ):
                            try:
                                tool = trace_data["orchestrationTrace"][
                                    "invocationInput"
                                ]["actionGroupInvocationInput"]["function"]
                                params = trace_data["orchestrationTrace"][
                                    "invocationInput"
                                ]["actionGroupInvocationInput"]["parameters"]
                                tool_use = f"ツール: {tool}、パラメータ: {json.dumps(params, ensure_ascii=False)}"
                                st.session_state.messages.append(
                                    {"role": "tool_use", "content": tool_use}
                                )
                            except (KeyError, TypeError):
                                pass

                    # ツール出力の取得
                    if (
                        "orchestrationTrace" in trace_data
                        and "observation" in trace_data["orchestrationTrace"]
                    ):
                        if (
                            "actionGroupInvocationOutput"
                            in trace_data["orchestrationTrace"]["observation"]
                        ):
                            try:
                                output = trace_data["orchestrationTrace"][
                                    "observation"
                                ]["actionGroupInvocationOutput"]["text"]
                                st.session_state.messages.append(
                                    {"role": "tool_output", "content": output}
                                )
                            except (KeyError, TypeError):
                                pass

                # 最終回答の取得
                if "chunk" in event:
                    data = event["chunk"]["bytes"]
                    agent_answer += data.decode("utf8")

            # エージェントの回答をメッセージリストに追加
            if agent_answer:
                st.session_state.messages.append(
                    {"role": "agent", "content": agent_answer}
                )
                print(agent_answer)

        except Exception as e:
            # エラーメッセージをメッセージリストに追加
            error_message = f"エラーが発生しました: {str(e)}"
            st.session_state.messages.append(
                {"role": "error", "content": error_message}
            )

        finally:
            # 処理状態をリセット
            st.session_state.processing = False
            st.session_state.input_to_process = None
            # プレースホルダーを消去
            progress_placeholder.empty()
            st.rerun()


# アプリケーション起動時に自動的にエージェントを初期化
if "agent" not in st.session_state or st.session_state.agent is None:
    with st.spinner("エージェントを初期化中..."):
        st.session_state.agent = initialize_agent()
    st.success("エージェントが初期化されました!")


# サイドバーに追加機能を実装
st.sidebar.title("コントロールパネル")

# エージェント再初期化ボタン
if st.sidebar.button("エージェントを再初期化"):
    with st.spinner("エージェントを再初期化中..."):
        st.session_state.agent = initialize_agent()
        st.session_state.session_id = None
    st.sidebar.success("エージェントが再初期化されました!")

# チャット履歴クリアボタン
if st.sidebar.button("チャット履歴をクリア"):
    st.session_state.messages = []
    st.sidebar.success("チャット履歴がクリアされました!")

# 表示設定
display_settings = st.sidebar.expander("表示設定", expanded=False)
with display_settings:
    show_thought = st.checkbox("思考プロセスを表示", value=True)
    show_tool_use = st.checkbox("ツール使用情報を表示", value=True)
    show_tool_output = st.checkbox("ツール出力を表示", value=True)


# メッセージの表示
chat_container = st.container()
with chat_container:
    for i, message in enumerate(st.session_state.messages):
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])

        elif message["role"] == "agent":
            st.chat_message("assistant").write(message["content"])

        elif message["role"] == "thought" and show_thought:
            with st.chat_message("assistant", avatar="🧠"):
                st.info(f"**思考プロセス:**\n{message['content']}")

        elif message["role"] == "tool_use" and show_tool_use:
            with st.chat_message("assistant", avatar="🔧"):
                st.warning(f"**ツール使用:**\n{message['content']}")

        elif message["role"] == "tool_output" and show_tool_output:
            with st.chat_message("system", avatar="📊"):
                st.success(f"**ツール出力:**\n{message['content']}")

        elif message["role"] == "error":
            st.error(message["content"])


# ユーザー入力の処理
if st.session_state.input_to_process and not st.session_state.processing:
    input_to_process = st.session_state.input_to_process
    asyncio.run(process_user_input(st.session_state.agent, input_to_process))


# ユーザー入力領域
user_input = st.chat_input(
    "エージェントに質問する", disabled=st.session_state.processing
)
if user_input and not st.session_state.processing:
    st.session_state.input_to_process = user_input
    st.rerun()


# ページ下部に利用情報を表示
st.markdown("---")
st.caption(
    f"セッションID: {st.session_state.session_id if st.session_state.session_id else '未設定'}"
)
st.caption("AWS Bedrock Agent Visualizer | 開発版")
