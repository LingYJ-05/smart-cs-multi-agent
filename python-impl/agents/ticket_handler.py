"""
工单处理Agent — 工单CRUD与流转
负责创建、查询、更新工单，对接工单系统，处理退款/理赔/开户等业务办理类需求。
通过MCP工具协议调用外部工单系统。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from db.models import Ticket
from tracing.otel_config import trace_agent_call


class TicketStatus(str, Enum):
    CREATED = "created"
    PROCESSING = "processing"
    PENDING_REVIEW = "pending_review"
    RESOLVED = "resolved"
    CLOSED = "closed"
    ESCALATED = "escalated"


class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


TICKET_SYSTEM_PROMPT = """你是一个专业的工单处理Agent，负责处理客户的业务办理请求。

你的职责：
1. 分析用户需求，判断是否需要创建工单
2. 提取工单关键信息（类型、优先级、描述）
3. 创建工单并返回工单号
4. 查询现有工单状态

工单类型：
- refund: 退款申请
- claim: 理赔申请
- account_open: 开户申请
- account_change: 账户变更
- complaint: 投诉工单
- general: 通用工单

优先级判断规则：
- urgent: 资金安全、账户被盗
- high: 退款超时、理赔争议
- medium: 常规业务办理
- low: 信息咨询类

请以JSON格式返回工单信息：
{
    "action": "create|query|update",
    "ticket_type": "refund|claim|account_open|...",
    "priority": "low|medium|high|urgent",
    "summary": "工单摘要",
    "details": "详细描述"
}
"""


class DatabaseTicketStore:
    """基于SQLite数据库的工单存储"""

    def __init__(self, db_session):
        self.db = db_session

    def create(self, ticket_type: str, priority: str, summary: str, details: str, user_id: str, username: str = "") -> dict:
        ticket_id = f"TK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        
        db_ticket = Ticket(
            ticket_id=ticket_id,
            type=ticket_type,
            title=summary,
            description=details,
            priority=priority,
            status=TicketStatus.CREATED.value,
            user_id=user_id,
            username=username,
        )
        
        self.db.add(db_ticket)
        self.db.commit()
        self.db.refresh(db_ticket)
        
        return {
            "ticket_id": db_ticket.ticket_id,
            "type": db_ticket.type,
            "priority": db_ticket.priority,
            "status": db_ticket.status,
            "summary": db_ticket.title,
            "details": db_ticket.description,
            "user_id": db_ticket.user_id,
            "username": db_ticket.username,
            "created_at": db_ticket.created_at.isoformat() if db_ticket.created_at else "",
            "updated_at": db_ticket.updated_at.isoformat() if db_ticket.updated_at else "",
        }

    def query(self, ticket_id: str) -> dict | None:
        db_ticket = self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if not db_ticket:
            return None
        
        return {
            "ticket_id": db_ticket.ticket_id,
            "type": db_ticket.type,
            "priority": db_ticket.priority,
            "status": db_ticket.status,
            "summary": db_ticket.title,
            "details": db_ticket.description,
            "user_id": db_ticket.user_id,
            "username": db_ticket.username,
            "assignee": db_ticket.assignee,
            "created_at": db_ticket.created_at.isoformat() if db_ticket.created_at else "",
            "updated_at": db_ticket.updated_at.isoformat() if db_ticket.updated_at else "",
        }

    def query_by_user(self, user_id: str) -> list[dict]:
        tickets = self.db.query(Ticket).filter(Ticket.user_id == user_id).order_by(Ticket.created_at.desc()).all()
        return [
            {
                "ticket_id": t.ticket_id,
                "type": t.type,
                "priority": t.priority,
                "status": t.status,
                "summary": t.title,
                "details": t.description,
                "user_id": t.user_id,
                "created_at": t.created_at.isoformat() if t.created_at else "",
                "updated_at": t.updated_at.isoformat() if t.updated_at else "",
            }
            for t in tickets
        ]

    def update_status(self, ticket_id: str, status: str) -> dict | None:
        db_ticket = self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if db_ticket:
            db_ticket.status = status
            self.db.commit()
            self.db.refresh(db_ticket)
            return self.query(ticket_id)
        return None

    def update(self, ticket_id: str, **kwargs) -> dict | None:
        db_ticket = self.db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
        if db_ticket:
            for key, value in kwargs.items():
                if hasattr(db_ticket, key):
                    setattr(db_ticket, key, value)
            self.db.commit()
            self.db.refresh(db_ticket)
            return self.query(ticket_id)
        return None

    def list_all(self, limit: int = 50) -> list[dict]:
        tickets = self.db.query(Ticket).order_by(Ticket.created_at.desc()).limit(limit).all()
        return [
            {
                "ticket_id": t.ticket_id,
                "type": t.type,
                "priority": t.priority,
                "status": t.status,
                "summary": t.title,
                "user_id": t.user_id,
                "username": t.username,
                "assignee": t.assignee,
                "created_at": t.created_at.isoformat() if t.created_at else "",
                "updated_at": t.updated_at.isoformat() if t.updated_at else "",
            }
            for t in tickets
        ]


class TicketHandlerAgent:
    """工单处理Agent"""

    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self.ticket_store = None

    @trace_agent_call("ticket_analyze")
    async def analyze_request(self, user_message: str) -> dict:
        """分析用户需求，提取工单信息"""
        messages = [
            SystemMessage(content=TICKET_SYSTEM_PROMPT),
            HumanMessage(content=f"用户消息: {user_message}"),
        ]

        response = await self.llm.ainvoke(messages)

        import json
        try:
            return json.loads(response.content)
        except json.JSONDecodeError:
            return {
                "action": "create",
                "ticket_type": "general",
                "priority": "medium",
                "summary": user_message[:100],
                "details": user_message,
            }

    @trace_agent_call("ticket_create")
    async def create_ticket(self, ticket_info: dict, user_id: str) -> str:
        """创建工单"""
        ticket = self.ticket_store.create(
            ticket_type=ticket_info.get("ticket_type", "general"),
            priority=ticket_info.get("priority", "medium"),
            summary=ticket_info.get("summary", ""),
            details=ticket_info.get("details", ""),
            user_id=user_id,
        )

        priority_label = {
            "low": "普通", "medium": "中等", "high": "高", "urgent": "紧急"
        }.get(ticket["priority"], "中等")

        return (
            f"工单已创建成功！\n\n"
            f"📋 工单号: {ticket['ticket_id']}\n"
            f"📝 类型: {ticket['type']}\n"
            f"⚡ 优先级: {priority_label}\n"
            f"📄 摘要: {ticket['summary']}\n"
            f"🕐 创建时间: {ticket['created_at']}\n\n"
            f"我们将尽快处理您的请求，请保存好工单号以便后续查询。"
        )

    @trace_agent_call("ticket_query")
    async def query_ticket(self, ticket_id: str) -> str:
        """查询工单状态"""
        ticket = self.ticket_store.query(ticket_id)
        if not ticket:
            return f"未找到工单号 {ticket_id}，请确认工单号是否正确。"

        status_label = {
            "created": "已创建",
            "processing": "处理中",
            "pending_review": "待审核",
            "resolved": "已解决",
            "closed": "已关闭",
            "escalated": "已升级",
        }.get(ticket["status"], ticket["status"])

        return (
            f"工单查询结果：\n\n"
            f"📋 工单号: {ticket['ticket_id']}\n"
            f"📊 状态: {status_label}\n"
            f"📝 类型: {ticket['type']}\n"
            f"📄 摘要: {ticket['summary']}\n"
            f"🕐 创建时间: {ticket['created_at']}\n"
            f"🔄 更新时间: {ticket['updated_at']}"
        )

    @trace_agent_call("ticket_update")
    async def update_ticket(self, ticket_info: dict) -> str:
        """更新工单状态"""
        ticket_id = ticket_info.get("ticket_id")
        ticket = self.ticket_store.query(ticket_id)
        if not ticket:
            return f"未找到工单号 {ticket_id}，请确认工单号是否正确。"

        updates = {}
        if "status" in ticket_info:
            updates["status"] = ticket_info["status"]
        if "priority" in ticket_info:
            updates["priority"] = ticket_info["priority"]
        if "assignee" in ticket_info:
            updates["assignee"] = ticket_info["assignee"]

        if updates:
            updated_ticket = self.ticket_store.update(ticket_id, **updates)
        else:
            updated_ticket = ticket

        status_label = {
            "created": "已创建",
            "processing": "处理中",
            "pending_review": "待审核",
            "resolved": "已解决",
            "closed": "已关闭",
            "escalated": "已升级",
        }.get(updated_ticket["status"], updated_ticket["status"])

        priority_label = {
            "low": "普通", "medium": "中等", "high": "高", "urgent": "紧急"
        }.get(updated_ticket["priority"], "中等")

        return (
            f"工单已更新成功！\n\n"
            f"📋 工单号: {updated_ticket['ticket_id']}\n"
            f"📊 状态: {status_label}\n"
            f"⚡ 优先级: {priority_label}\n"
            f"👤 处理人: {updated_ticket.get('assignee', '未分配')}\n"
            f"🔄 更新时间: {updated_ticket['updated_at']}"
        )

    @trace_agent_call("ticket_handler_process")
    async def process(self, state: dict[str, Any]) -> dict[str, Any]:
        """作为Graph节点处理状态"""
        messages = state.get("messages", [])
        user_id = state.get("user_id", "anonymous")
        db_session = state.get("db_session")
        session_id = state.get("session_id", "")

        if not messages:
            return state

        if not db_session:
            return {
                **state,
                "sub_results": {
                    **state.get("sub_results", {}),
                    "ticket_handler": "抱歉，工单系统暂时不可用，请稍后再试。",
                },
            }

        self.ticket_store = DatabaseTicketStore(db_session)

        last_message = messages[-1].content
        ticket_info = await self.analyze_request(last_message)

        action = ticket_info.get("action", "create")
        tool_name = f"ticket_{action}"
        
        import json
        from db.models import ToolCallLog
        from datetime import datetime

        if action == "query" and "ticket_id" in ticket_info:
            result = await self.query_ticket(ticket_info["ticket_id"])
        elif action == "update" and "ticket_id" in ticket_info:
            result = await self.update_ticket(ticket_info)
        else:
            result = await self.create_ticket(ticket_info, user_id)

        log_entry = ToolCallLog(
            tool_name=tool_name,
            session_id=session_id,
            user_id=user_id,
            input_params=json.dumps(ticket_info),
            output_result=json.dumps({"result": result[:500]}),
            success=True,
            duration_ms=0,
            created_at=datetime.now(),
        )
        db_session.add(log_entry)
        db_session.commit()

        return {
            **state,
            "sub_results": {
                **state.get("sub_results", {}),
                "ticket_handler": result,
            },
        }
