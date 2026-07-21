"""
MCP工具协议服务端 — Model Context Protocol实现
遵循Anthropic MCP标准，通过JSON-RPC 2.0提供工具注册/发现/调用能力。
支持动态工具扩展，Agent通过统一接口调用外部系统。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable
from datetime import datetime


@dataclass
class ToolDefinition:
    """MCP工具定义"""
    name: str
    description: str
    input_schema: dict[str, Any]
    handler: Callable[..., Awaitable[Any]]
    category: str = "general"
    requires_auth: bool = False


@dataclass
class ToolCallResult:
    """工具调用结果"""
    tool_name: str
    success: bool
    result: Any = None
    error: str | None = None
    duration_ms: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class MCPToolServer:
    """
    MCP工具服务端。

    实现 Model Context Protocol 的核心功能：
    1. 工具注册 (Tool Registration)
    2. 工具发现 (Tool Discovery) - Agent可查询可用工具列表
    3. 工具调用 (Tool Invocation) - 通过JSON-RPC 2.0协议调用
    4. 结果返回 (Result Delivery)

    遵循MCP规范：
    - 使用JSON-RPC 2.0消息格式
    - 支持工具的inputSchema声明
    - 提供标准化的错误码
    """

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}
        self._call_log: list[ToolCallResult] = []
        self._callbacks: list[Callable[[ToolCallResult, dict], Awaitable[None]]] = []

    def register_callback(self, callback: Callable[[ToolCallResult, dict], Awaitable[None]]) -> None:
        """注册工具调用回调"""
        self._callbacks.append(callback)

    def register_tool(self, tool: ToolDefinition) -> None:
        """注册一个MCP工具"""
        self._tools[tool.name] = tool

    def register(
        self,
        name: str,
        description: str,
        input_schema: dict[str, Any],
        category: str = "general",
        requires_auth: bool = False,
    ) -> Callable:
        """工具注册装饰器"""
        def decorator(func: Callable[..., Awaitable[Any]]) -> Callable:
            tool = ToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema,
                handler=func,
                category=category,
                requires_auth=requires_auth,
            )
            self._tools[name] = tool
            return func
        return decorator

    def list_tools(self, category: str | None = None) -> list[dict]:
        """
        工具发现：列出所有可用工具。
        对应MCP的 tools/list 方法。
        """
        tools = []
        for tool in self._tools.values():
            if category and tool.category != category:
                continue
            tools.append({
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema,
                "category": tool.category,
            })
        return tools

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> ToolCallResult:
        """
        工具调用：执行指定工具。
        对应MCP的 tools/call 方法。
        """
        import time

        tool = self._tools.get(name)
        if tool is None:
            result = ToolCallResult(
                tool_name=name,
                success=False,
                error=f"Tool '{name}' not found. Available: {list(self._tools.keys())}",
            )
            self._call_log.append(result)
            return result

        start = time.time()
        try:
            output = await tool.handler(**arguments)
            duration_ms = (time.time() - start) * 1000

            result = ToolCallResult(
                tool_name=name,
                success=True,
                result=output,
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = (time.time() - start) * 1000
            result = ToolCallResult(
                tool_name=name,
                success=False,
                error=str(e),
                duration_ms=duration_ms,
            )

        self._call_log.append(result)
        
        for callback in self._callbacks:
            await callback(result, arguments)
        
        return result

    async def handle_jsonrpc(self, request: dict) -> dict:
        """
        处理JSON-RPC 2.0请求。
        MCP协议传输层实现。
        """
        method = request.get("method", "")
        params = request.get("params", {})
        req_id = request.get("id", 1)

        try:
            if method == "tools/list":
                result = self.list_tools(category=params.get("category"))
            elif method == "tools/call":
                tool_name = params.get("name", "")
                arguments = params.get("arguments", {})
                call_result = await self.call_tool(tool_name, arguments)
                result = {
                    "success": call_result.success,
                    "result": call_result.result,
                    "error": call_result.error,
                }
            elif method == "ping":
                result = {"status": "ok"}
            else:
                return {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": f"Method not found: {method}"},
                    "id": req_id,
                }

            return {"jsonrpc": "2.0", "result": result, "id": req_id}

        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "error": {"code": -32603, "message": str(e)},
                "id": req_id,
            }

    def get_call_log(self, last_n: int = 100) -> list[dict]:
        """获取最近的工具调用日志"""
        return [
            {
                "tool": r.tool_name,
                "success": r.success,
                "duration_ms": r.duration_ms,
                "timestamp": r.timestamp,
                "error": r.error,
            }
            for r in self._call_log[-last_n:]
        ]


def create_default_tools(server: MCPToolServer) -> MCPToolServer:
    """注册默认的MCP工具集"""

    @server.register(
        name="product_query",
        description="查询产品信息、收益率等",
        input_schema={
            "type": "object",
            "properties": {
                "product_name": {"type": "string", "description": "产品名称"},
                "product_id": {"type": "string", "description": "产品ID"},
            },
        },
        category="product",
    )
    async def product_query(product_name: str = "", product_id: str = "") -> dict:
        products = {
            "理财产品A": {
                "product_id": "PRD-A001",
                "name": "稳健增值理财A",
                "type": "固定收益",
                "yield_rate": "3.5%-5.2%",
                "min_amount": 10000,
                "term": "6个月-3年",
                "risk_level": "R2",
                "description": "适合稳健型投资者，风险较低，收益稳定",
                "risk_warning": "理财非存款，产品有风险，投资须谨慎",
            },
            "理财产品B": {
                "product_id": "PRD-B001",
                "name": "成长优选理财B",
                "type": "混合型",
                "yield_rate": "4.2%-7.8%",
                "min_amount": 50000,
                "term": "1年-5年",
                "risk_level": "R3",
                "description": "适合进取型投资者，追求较高收益",
                "risk_warning": "理财非存款，产品有风险，投资须谨慎",
            },
            "基金产品C": {
                "product_id": "PRD-C001",
                "name": "指数增强基金C",
                "type": "基金",
                "yield_rate": "浮动收益",
                "min_amount": 1000,
                "term": "灵活申赎",
                "risk_level": "R4",
                "description": "跟踪沪深300指数，追求超额收益",
                "risk_warning": "基金有风险，投资需谨慎",
            },
        }
        
        if product_name:
            return products.get(product_name, {
                "error": f"未找到产品: {product_name}",
                "available_products": list(products.keys()),
            })
        if product_id:
            for p in products.values():
                if p["product_id"] == product_id:
                    return p
            return {"error": f"未找到产品ID: {product_id}"}
        return {"available_products": list(products.keys()), "count": len(products)}

    @server.register(
        name="account_query",
        description="查询账户信息、余额等",
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "用户ID"},
                "account_id": {"type": "string", "description": "账户ID"},
            },
        },
        category="account",
    )
    async def account_query(user_id: str = "", account_id: str = "") -> dict:
        return {
            "user_id": user_id or "U10001",
            "account_id": account_id or "ACC-8888",
            "username": "尊贵用户",
            "total_balance": 128500.50,
            "available_balance": 86200.00,
            "frozen_balance": 42300.50,
            "currency": "CNY",
            "account_type": "理财账户",
            "risk_level": "R2",
            "last_trade_date": "2026-07-19",
            "registered_date": "2025-03-15",
        }

    @server.register(
        name="policy_interpretation",
        description="解读相关政策和规则",
        input_schema={
            "type": "object",
            "properties": {
                "policy_topic": {"type": "string", "description": "政策主题"},
            },
            "required": ["policy_topic"],
        },
        category="policy",
    )
    async def policy_interpretation(policy_topic: str) -> dict:
        policies = {
            "退款政策": {
                "topic": "退款政策",
                "summary": "用户在购买后7天内可申请无理由退款",
                "details": [
                    "购买后7天内可申请无理由退款",
                    "超过7天需提供合理原因",
                    "退款将在3-5个工作日内原路退回",
                    "理财产品到期前赎回可能收取手续费",
                ],
                "effective_date": "2026-01-01",
            },
            "开户流程": {
                "topic": "开户流程",
                "summary": "线上开户仅需3步，全程约5分钟",
                "details": [
                    "准备身份证和银行卡",
                    "填写个人信息并上传证件",
                    "完成风险测评",
                    "审核通过后即可交易",
                ],
                "effective_date": "2026-01-01",
            },
            "隐私保护": {
                "topic": "隐私保护",
                "summary": "严格保护用户个人信息安全",
                "details": [
                    "采用银行级加密传输",
                    "个人信息仅用于业务办理",
                    "不向第三方泄露用户数据",
                    "用户有权查询和删除个人数据",
                ],
                "effective_date": "2026-01-01",
            },
            "合规要求": {
                "topic": "合规要求",
                "summary": "严格遵守金融监管要求",
                "details": [
                    "所有理财产品需标注风险等级",
                    "不得承诺保本保息",
                    "需充分揭示投资风险",
                    "定期向监管部门报送数据",
                ],
                "effective_date": "2026-01-01",
            },
        }
        
        return policies.get(policy_topic, {
            "error": f"未找到相关政策: {policy_topic}",
            "available_topics": list(policies.keys()),
        })

    @server.register(
        name="finance_calculator",
        description="理财计算、收益计算等",
        input_schema={
            "type": "object",
            "properties": {
                "principal": {"type": "number", "description": "本金"},
                "amount": {"type": "number", "description": "投资金额"},
                "rate": {"type": "number", "description": "年化收益率(%)"},
                "years": {"type": "number", "description": "投资年限"},
                "days": {"type": "number", "description": "投资天数"},
                "period": {"type": "number", "description": "投资周期(年)"},
                "compound": {"type": "boolean", "description": "是否复利"},
            },
            "required": ["principal", "rate", "years"],
        },
        category="calculator",
    )
    async def finance_calculator(**kwargs) -> dict:
        principal = kwargs.get("principal") or kwargs.get("amount") or 0
        rate = kwargs.get("rate") or 0
        
        years = kwargs.get("years") or kwargs.get("period") or 0
        if years == 0:
            days = kwargs.get("days") or 0
            if days > 0:
                years = days / 365
        
        compound = kwargs.get("compound", True)
        
        rate_decimal = rate / 100
        
        if compound:
            total_amount = principal * (1 + rate_decimal) ** years
        else:
            total_amount = principal * (1 + rate_decimal * years)
        
        interest = total_amount - principal
        monthly_interest = interest / (years * 12) if years > 0 else 0
        
        return {
            "principal": round(principal, 2),
            "annual_rate": rate,
            "years": round(years, 4),
            "compound": compound,
            "total_amount": round(total_amount, 2),
            "total_interest": round(interest, 2),
            "monthly_interest": round(monthly_interest, 2),
            "return_rate": round((interest / principal) * 100, 2) if principal > 0 else 0,
            "risk_warning": "以上计算仅供参考，实际收益可能因市场波动而有所不同",
        }

    @server.register(
        name="order_query",
        description="查询订单信息，支持按订单号或用户ID查询",
        input_schema={
            "type": "object",
            "properties": {
                "order_id": {"type": "string", "description": "订单号"},
                "user_id": {"type": "string", "description": "用户ID"},
            },
        },
        category="order",
    )
    async def order_query(order_id: str = "", user_id: str = "") -> dict:
        return {
            "order_id": order_id or "ORD-20260401-001",
            "status": "shipped",
            "amount": 299.00,
            "product": "智能理财产品A",
            "created_at": "2026-04-01T10:00:00",
        }

    @server.register(
        name="knowledge_search",
        description="搜索企业知识库，返回相关文档片段",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索查询"},
                "top_k": {"type": "integer", "description": "返回数量", "default": 3},
            },
            "required": ["query"],
        },
        category="knowledge",
    )
    async def knowledge_search(query: str, top_k: int = 3) -> list[dict]:
        return [
            {"content": f"关于'{query}'的知识库文档片段", "source": "FAQ.md", "score": 0.95},
        ]

    @server.register(
        name="ticket_create",
        description="创建客服工单",
        input_schema={
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "description": {"type": "string"},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "category": {"type": "string"},
                "user_id": {"type": "string"},
                "username": {"type": "string"},
            },
            "required": ["title", "description"],
        },
        category="ticket",
    )
    async def ticket_create(title: str, description: str, priority: str = "medium", category: str = "general", user_id: str = "", username: str = "") -> dict:
        import uuid
        return {
            "ticket_id": f"TK-{uuid.uuid4().hex[:8].upper()}",
            "title": title,
            "status": "created",
            "priority": priority,
            "category": category,
        }

    @server.register(
        name="ticket_update",
        description="更新客服工单状态",
        input_schema={
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string", "description": "工单号"},
                "status": {"type": "string", "enum": ["created", "processing", "pending_review", "resolved", "closed", "escalated"]},
                "priority": {"type": "string", "enum": ["low", "medium", "high", "urgent"]},
                "assignee": {"type": "string", "description": "处理人"},
                "note": {"type": "string", "description": "处理备注"},
            },
            "required": ["ticket_id"],
        },
        category="ticket",
    )
    async def ticket_update(ticket_id: str, status: str | None = None, priority: str | None = None, assignee: str | None = None, note: str = "") -> dict:
        updates = {}
        if status:
            updates["status"] = status
        if priority:
            updates["priority"] = priority
        if assignee:
            updates["assignee"] = assignee
        
        return {
            "ticket_id": ticket_id,
            "success": True,
            "updated_fields": updates,
            "note": note,
        }

    @server.register(
        name="risk_check",
        description="风控接口 — 检查交易/操作的风险等级",
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "action": {"type": "string"},
                "amount": {"type": "number"},
            },
            "required": ["user_id", "action"],
        },
        category="compliance",
    )
    async def risk_check(user_id: str, action: str, amount: float = 0.0) -> dict:
        risk_level = "low"
        if amount > 50000:
            risk_level = "high"
        elif amount > 10000:
            risk_level = "medium"

        return {
            "user_id": user_id,
            "action": action,
            "risk_level": risk_level,
            "requires_manual_review": risk_level == "high",
        }

    @server.register(
        name="user_profile",
        description="查询用户画像信息",
        input_schema={
            "type": "object",
            "properties": {
                "user_id": {"type": "string", "description": "用户ID"},
                "fields": {"type": "array", "items": {"type": "string"}, "description": "需要查询的字段列表"},
            },
            "required": ["user_id"],
        },
        category="user",
        requires_auth=True,
    )
    async def user_profile(user_id: str, fields: list[str] | None = None) -> dict:
        profile = {
            "user_id": user_id,
            "username": f"user_{user_id[-4:]}",
            "real_name": "用户",
            "phone": "138****8888",
            "email": f"user{user_id[-4:]}@example.com",
            "account_level": "normal",
            "total_spent": 12800.00,
            "registered_at": "2026-01-15T10:00:00",
            "last_login_at": "2026-07-15T14:30:00",
        }

        if fields:
            return {k: v for k, v in profile.items() if k in fields}
        return profile

    @server.register(
        name="kb_search",
        description="知识库全文搜索，返回相关文档片段",
        input_schema={
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "搜索关键词"},
                "top_k": {"type": "integer", "description": "返回数量", "default": 5},
                "category": {"type": "string", "description": "文档分类"},
            },
            "required": ["query"],
        },
        category="knowledge",
    )
    async def kb_search(query: str, top_k: int = 5, category: str | None = None) -> list[dict]:
        docs = []
        for i in range(min(top_k, 3)):
            docs.append({
                "id": f"doc_{i+1}",
                "title": f"关于'{query}'的知识库文档",
                "content": f"这是与'{query}'相关的知识库内容片段...\n\n详细信息请参考官方文档。",
                "source": "FAQ.md",
                "category": category or "general",
                "score": round(0.95 - i * 0.05, 2),
            })
        return docs

    return server
