"""
工具调用Agent — 动态工具选择与执行
负责查询数据库中的可用工具，分析用户意图，选择合适的工具执行。
支持MCP协议调用外部工具，实现真正的工具调用能力。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from db.models import Tool, ToolCallLog
from mcp.mcp_server import MCPToolServer, create_default_tools
from tracing.otel_config import trace_agent_call


TOOL_CALL_SYSTEM_PROMPT = """你是一个智能工具调度Agent，负责分析用户问题并选择合适的工具执行。

当前可用工具列表：
{tool_list}

分析步骤：
1. 理解用户的问题意图
2. 从工具列表中选择最匹配的工具
3. 提取工具所需的参数
4. 返回工具编码(tool_code)和参数

返回格式（JSON）：
{{
    "tool_code": "工具编码",
    "arguments": {{参数名: 值}},
    "reason": "选择该工具的原因"
}}

如果没有合适的工具，返回：
{{
    "tool_code": "none",
    "arguments": {{}},
    "reason": "无需调用工具"
}}
"""


class ToolCallerAgent:
    """工具调用Agent - 实现动态工具选择与执行"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.mcp_server = create_default_tools(MCPToolServer())

    def _get_tool_list_prompt(self, db_session) -> str:
        """从数据库获取工具列表并格式化为prompt"""
        tools = db_session.query(Tool).filter(Tool.available == True).all()
        if not tools:
            return "无可用工具"
        
        tool_descriptions = []
        for tool in tools:
            tool_descriptions.append(f"- 工具名称: {tool.name}, 工具编码(tool_code): {tool.tool_code}, 描述: {tool.description}")
        
        return "\n".join(tool_descriptions)

    def _get_mcp_tool_info(self, tool_name: str) -> dict | None:
        """获取MCP工具的详细信息"""
        tools = self.mcp_server.list_tools()
        return next((t for t in tools if t["name"] == tool_name or t["name"].lower() == tool_name.lower()), None)

    @trace_agent_call("tool_selection")
    async def select_tool(self, user_message: str, db_session) -> dict:
        """分析用户问题，选择合适的工具"""
        tool_list = self._get_tool_list_prompt(db_session)
        
        messages = [
            SystemMessage(content=TOOL_CALL_SYSTEM_PROMPT.format(tool_list=tool_list)),
            HumanMessage(content=f"用户问题: {user_message}"),
        ]

        response = await self.llm.ainvoke(messages)

        try:
            result = json.loads(response.content)
            return {
                "tool_code": result.get("tool_code", result.get("tool_name", "none")),
                "arguments": result.get("arguments", {}),
                "reason": result.get("reason", "选择工具"),
            }
        except json.JSONDecodeError:
            return {
                "tool_code": "none",
                "arguments": {},
                "reason": "解析失败",
            }

    @trace_agent_call("tool_execution")
    async def execute_tool(self, tool_code: str, arguments: dict, db_session, user_id: str, session_id: str) -> str:
        """执行MCP工具"""
        mcp_tool = self._get_mcp_tool_info(tool_code)
        
        if not mcp_tool:
            return f"工具 '{tool_code}' 暂未实现，请联系管理员。"

        result = await self.mcp_server.call_tool(tool_code, arguments)

        if db_session:
            log_entry = ToolCallLog(
                tool_name=tool_code,
                session_id=session_id,
                user_id=user_id,
                input_params=json.dumps(arguments),
                output_result=json.dumps({"result": result.result, "error": result.error}),
                success=result.success,
                duration_ms=result.duration_ms,
                created_at=datetime.now(),
            )
            db_session.add(log_entry)
            db_session.commit()

        if result.success:
            return self._format_tool_result(tool_code, result.result)
        else:
            return f"工具执行失败: {result.error}"

    def _format_tool_result(self, tool_code: str, result: dict) -> str:
        """将工具返回结果格式化为用户友好的自然语言"""
        if tool_code == "finance_calculator":
            return (
                f"💰 理财计算结果：\n\n"
                f"📊 投资本金：¥{result.get('principal', 0):,.2f}\n"
                f"📈 年化收益率：{result.get('annual_rate', 0)}%\n"
                f"⏱️ 投资期限：{result.get('years', 0)}年\n"
                f"🔄 复利计算：{'是' if result.get('compound') else '否'}\n"
                f"---\n"
                f"🏦 到期本息：¥{result.get('total_amount', 0):,.2f}\n"
                f"💵 总收益：¥{result.get('total_interest', 0):,.2f}\n"
                f"📉 月均收益：¥{result.get('monthly_interest', 0):,.2f}\n"
                f"📋 收益率：{result.get('return_rate', 0)}%\n"
                f"\n⚠️ {result.get('risk_warning', '')}"
            )
        elif tool_code == "product_query":
            if "error" in result:
                return f"❌ {result.get('error', '')}\n\n可用产品：{', '.join(result.get('available_products', []))}"
            return (
                f"📦 产品信息：\n\n"
                f"🏷️ 产品名称：{result.get('name', '')}\n"
                f"🆔 产品ID：{result.get('product_id', '')}\n"
                f"📊 产品类型：{result.get('type', '')}\n"
                f"📈 预期收益率：{result.get('yield_rate', '')}\n"
                f"💰 起投金额：¥{result.get('min_amount', 0):,.2f}\n"
                f"⏱️ 投资期限：{result.get('term', '')}\n"
                f"🎯 风险等级：{result.get('risk_level', '')}\n"
                f"📝 产品描述：{result.get('description', '')}\n"
                f"\n⚠️ {result.get('risk_warning', '')}"
            )
        elif tool_code == "account_query":
            return (
                f"👤 账户信息：\n\n"
                f"🏦 账户类型：{result.get('account_type', '')}\n"
                f"💰 总资产：¥{result.get('total_balance', 0):,.2f}\n"
                f"💳 可用余额：¥{result.get('available_balance', 0):,.2f}\n"
                f"🔒 冻结金额：¥{result.get('frozen_balance', 0):,.2f}\n"
                f"🎯 风险等级：{result.get('risk_level', '')}\n"
                f"📅 注册日期：{result.get('registered_date', '')}\n"
                f"📅 最近交易：{result.get('last_trade_date', '')}\n"
                f"💱 货币类型：{result.get('currency', '')}"
            )
        elif tool_code == "policy_interpretation":
            if "error" in result:
                return f"❌ {result.get('error', '')}\n\n可用政策：{', '.join(result.get('available_topics', []))}"
            details = "\n".join(f"  • {d}" for d in result.get("details", []))
            return (
                f"📜 政策解读：\n\n"
                f"🏷️ 政策主题：{result.get('topic', '')}\n"
                f"📋 政策摘要：{result.get('summary', '')}\n"
                f"🔍 详细说明：\n{details}\n"
                f"📅 生效日期：{result.get('effective_date', '')}"
            )
        else:
            result_str = json.dumps(result, ensure_ascii=False, indent=2)
            return f"工具执行成功:\n\n{result_str}"

    @trace_agent_call("tool_caller_process")
    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """作为Graph节点处理状态"""
        messages = state.get("messages", [])
        db_session = state.get("db_session")
        user_id = state.get("user_id", "anonymous")
        session_id = state.get("session_id", "")

        if not messages:
            return state

        last_message = messages[-1].content

        selection = await self.select_tool(last_message, db_session)
        tool_code = selection.get("tool_code", "none")

        if tool_code == "none":
            return {
                **state,
                "sub_results": {
                    **state.get("sub_results", {}),
                    "tool_caller": "无需调用工具，将由知识库Agent处理。",
                },
            }

        arguments = selection.get("arguments", {})
        execution_result = await self.execute_tool(tool_code, arguments, db_session, user_id, session_id)

        return {
            **state,
            "sub_results": {
                **state.get("sub_results", {}),
                "tool_caller": execution_result,
            },
        }
