"""
FastAPI入口 — 提供REST API + SSE流式响应
"""

from __future__ import annotations

import os
import uuid
import json
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Any

from dotenv import load_dotenv
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func
from passlib.context import CryptContext
from jose import JWTError, jwt
from captcha.image import ImageCaptcha

from agents.supervisor import create_supervisor_graph
from memory.working_memory import WorkingMemory
from memory.short_term import ShortTermMemory
from memory.long_term import LongTermMemory
from mcp.mcp_server import MCPToolServer, create_default_tools
from tracing.otel_config import init_tracer, AgentMetrics
from db.database import get_db, init_db
from db.models import User, ChatSession, ChatMessage, Tool, SystemMetric, ToolCallLog, Ticket
from datetime import datetime

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
DEBUG = os.getenv("DEBUG", "false").lower() == "true"


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def generate_captcha_code(length: int = 4) -> str:
    chars = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghjkmnpqrstuvwxyz23456789'
    return ''.join(__import__('random').choice(chars) for _ in range(length))


def generate_captcha_image(code: str) -> bytes:
    from PIL import Image, ImageDraw, ImageFont
    import random
    import io

    width, height = 160, 50
    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    try:
        font = ImageFont.truetype('arial.ttf', 32)
    except:
        font = ImageFont.load_default()

    chars = code
    char_width = width // len(chars)
    for i, char in enumerate(chars):
        x = i * char_width + random.randint(2, 6)
        y = random.randint(5, height - 30)
        color = (random.randint(50, 150), random.randint(50, 150), random.randint(50, 150))
        draw.text((x, y), char, font=font, fill=color)

    for _ in range(30):
        x = random.randint(0, width)
        y = random.randint(0, height)
        color = (random.randint(180, 255), random.randint(180, 255), random.randint(180, 255))
        draw.point((x, y), fill=color)

    for _ in range(2):
        x1 = random.randint(0, width)
        y1 = random.randint(0, height)
        x2 = random.randint(0, width)
        y2 = random.randint(0, height)
        color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
        draw.line((x1, y1, x2, y2), fill=color, width=1)

    buf = io.BytesIO()
    image.save(buf, format='PNG')
    return buf.getvalue()


class ApiResponse(BaseModel):
    code: int
    message: str
    data: Any = None

    model_config = {"arbitrary_types_allowed": True}


def success_response(data: Any = None, message: str = "操作成功") -> ApiResponse:
    return ApiResponse(code=200, message=message, data=data)


def error_response(code: int, message: str) -> ApiResponse:
    return ApiResponse(code=code, message=message, data=None)


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    captcha_id: str
    captcha_code: str
    role: str = "user"


class LoginData(BaseModel):
    token: str
    username: str
    role: str


working_memory = WorkingMemory()
short_term_memory = ShortTermMemory(redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"))
long_term_memory = LongTermMemory(index_path=os.getenv("FAISS_INDEX_PATH", "./vector_store/faiss_index"))
mcp_server = create_default_tools(MCPToolServer())
metrics = AgentMetrics()
graph = None
has_api_key = bool(os.getenv("DEEPSEEK_API_KEY") or os.getenv("OPENAI_API_KEY"))


async def log_tool_call(result: Any, arguments: dict) -> None:
    """工具调用回调：记录到数据库"""
    try:
        db = next(get_db())
        log_entry = ToolCallLog(
            tool_name=result.tool_name,
            success=result.success,
            duration_ms=result.duration_ms,
            input_params=json.dumps(arguments),
            output_result=json.dumps(result.result) if result.result else None,
            error_message=result.error,
        )
        db.add(log_entry)
        db.commit()
        db.close()
    except Exception as e:
        print(f"[工具调用日志记录失败] {e}")


mcp_server.register_callback(log_tool_call)


def init_default_data(db: Session):
    """初始化默认数据"""
    if db.query(User).count() == 0:
        import hashlib
        admin_user = User(
            username="admin",
            password_hash=hashlib.sha256("admin123".encode()).hexdigest(),
            role="admin",
        )
        db.add(admin_user)
        db.commit()
        print("✅ 初始化默认用户完成")

    if db.query(Tool).count() == 0:
        tools = [
            Tool(name="产品查询", tool_code="product_query", description="查询产品信息、收益率等", icon="DataBoard", available=True),
            Tool(name="账户查询", tool_code="account_query", description="查询账户信息、余额等", icon="User", available=True),
            Tool(name="政策解读", tool_code="policy_interpretation", description="解读相关政策和规则", icon="Files", available=True),
            Tool(name="计算工具", tool_code="finance_calculator", description="理财计算、收益计算等", icon="DataAnalysis", available=True),
        ]
        db.add_all(tools)
        db.commit()
        print("✅ 初始化工具数据完成")

    if db.query(SystemMetric).count() == 0:
        metrics = [
            SystemMetric(metric_type="daily_sessions", value=128.0, value_str="128", label="今日会话数"),
            SystemMetric(metric_type="daily_tool_calls", value=356.0, value_str="356", label="今日工具调用"),
            SystemMetric(metric_type="compliance_rate", value=98.6, value_str="98.6%", label="合规通过率"),
            SystemMetric(metric_type="avg_response_time", value=1.2, value_str="1.2s", label="平均响应时间"),
        ]
        db.add_all(metrics)
        db.commit()
        print("✅ 初始化系统指标完成")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global graph

    init_tracer(
        service_name=os.getenv("OTEL_SERVICE_NAME", "smart-cs-multi-agent"),
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
    )

    init_db()
    with next(get_db()) as db:
        init_default_data(db)

    long_term_memory.add_document(
        content="我们的理财产品A年化收益率为3.5%-5.2%，投资期限为6个月至3年，最低投资金额10000元。注意：理财非存款，产品有风险，投资须谨慎。",
        source="product_faq.md",
    )
    long_term_memory.add_document(
        content="退款政策：用户在购买后7天内可申请无理由退款，超过7天需提供合理原因。退款将在3-5个工作日内原路退回。",
        source="refund_policy.md",
    )
    long_term_memory.add_document(
        content="开户流程：1.准备身份证原件 2.填写开户申请表 3.进行视频认证 4.设置交易密码 5.完成风险评估问卷。整个流程约需15-30分钟。",
        source="account_guide.md",
    )

    if has_api_key:
        graph = create_supervisor_graph(
            working_memory=working_memory,
            short_term_memory=short_term_memory,
            long_term_memory=long_term_memory,
        )
        print("✅ 已连接OpenAI API，启用完整多Agent功能")
    else:
        print("⚠️ 未配置OPENAI_API_KEY，使用模拟模式运行")

    yield


app = FastAPI(
    title="智能客服多Agent系统",
    description="基于LangGraph的Supervisor编排多Agent智能客服系统",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def add_cors_headers(response: JSONResponse) -> JSONResponse:
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Credentials"] = "true"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    print(f"[HTTP异常] {request.method} {request.url} - {exc.status_code}: {exc.detail}")
    response = JSONResponse(
        content=error_response(exc.status_code, exc.detail).dict(),
        status_code=exc.status_code,
    )
    return add_cors_headers(response)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"[参数校验异常] {request.method} {request.url} - {exc.errors()}")
    response = JSONResponse(
        content=error_response(400, "参数校验失败").dict(),
        status_code=400,
    )
    return add_cors_headers(response)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    print(f"[全局异常] {request.method} {request.url} - {str(exc)}")
    response = JSONResponse(
        content=error_response(500, str(exc) if DEBUG else "系统内部错误，请稍后重试").dict(),
        status_code=500,
    )
    return add_cors_headers(response)


class ChatRequest(BaseModel):
    message: str
    user_id: str = "anonymous"
    session_id: str | None = None


class ChatData(BaseModel):
    response: str
    session_id: str
    intent: str
    compliance_passed: bool
    compliance_risk_level: str = "low"
    compliance_violations: list[str] = []


@app.post("/api/chat")
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    """主聊天接口"""
    import time
    start_time = time.time()
    
    session_id = request.session_id or str(uuid.uuid4())

    await short_term_memory.add_message(session_id, "user", request.message)

    db_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not db_session:
        db_session = ChatSession(
            session_id=session_id,
            user_id=request.user_id,
            username=request.user_id,
        )
        db.add(db_session)
        db.commit()

    db_user_message = ChatMessage(
        session_id=session_id,
        role="user",
        content=request.message,
    )
    db.add(db_user_message)
    db.commit()

    if graph is None:
        mock_response = "您好！这是智能客服系统的模拟回复。由于未配置OpenAI API密钥，当前使用离线模式运行。\n\n您可以询问以下问题：\n- 理财产品收益率\n- 退款政策\n- 开户流程\n\n如需启用完整AI功能，请在 .env 文件中配置 OPENAI_API_KEY。"
        await short_term_memory.add_message(session_id, "assistant", mock_response)

        response_time_ms = (time.time() - start_time) * 1000

        db_assistant_message = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=mock_response,
            intent="knowledge_rag",
            compliance_passed=True,
            response_time_ms=response_time_ms,
        )
        db.add(db_assistant_message)
        db.commit()

        return success_response(
            data=ChatData(
                response=mock_response,
                session_id=session_id,
                intent="knowledge_rag",
                compliance_passed=True,
            ),
            message="消息发送成功",
        )

    from langchain_core.messages import HumanMessage

    initial_state = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": request.user_id,
        "session_id": session_id,
        "intent": "",
        "sub_results": {},
        "compliance_passed": True,
        "final_response": "",
        "current_agent": "",
        "retry_count": 0,
        "db_session": db,
    }

    config = {"configurable": {"thread_id": session_id}}

    try:
        result = await graph.ainvoke(initial_state, config=config)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理失败: {str(e)}")

    final_response = result.get("final_response", "系统处理异常，请稍后重试")
    intent = result.get("intent", "unknown")
    compliance_passed = result.get("compliance_passed", True)

    sub_results = result.get("sub_results", {})
    compliance_info = sub_results.get("compliance", {})
    compliance_risk_level = compliance_info.get("risk_level", "low")
    compliance_violations = compliance_info.get("violations", [])

    response_time_ms = (time.time() - start_time) * 1000

    await short_term_memory.add_message(session_id, "assistant", final_response)

    db_assistant_message = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=final_response,
        intent=intent,
        compliance_passed=compliance_passed,
        response_time_ms=response_time_ms,
    )
    db.add(db_assistant_message)
    db.commit()

    return success_response(
        data=ChatData(
            response=final_response,
            session_id=session_id,
            intent=intent,
            compliance_passed=compliance_passed,
            compliance_risk_level=compliance_risk_level,
            compliance_violations=compliance_violations,
        ),
        message="消息发送成功",
    )


@app.get("/api/history/{session_id}")
async def get_history(session_id: str, db: Session = Depends(get_db)):
    """获取对话历史"""
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at).all()

    history_data = [{
        "id": str(msg.id),
        "role": msg.role,
        "content": msg.content,
        "intent": msg.intent,
        "compliance_passed": msg.compliance_passed,
        "timestamp": msg.created_at.strftime("%Y-%m-%d %H:%M:%S") if msg.created_at else "",
    } for msg in messages]

    return success_response(
        data={"session_id": session_id, "messages": history_data},
        message="获取历史成功",
    )


@app.get("/api/chat-sessions")
async def list_chat_sessions(user_id: str | None = None, db: Session = Depends(get_db)):
    """获取用户会话列表"""
    query = db.query(ChatSession)
    if user_id:
        query = query.filter(ChatSession.user_id == user_id)
    
    sessions = query.order_by(ChatSession.updated_at.desc()).limit(20).all()
    
    sessions_data = [{
        "id": s.session_id,
        "user_id": s.user_id,
        "username": s.username,
        "status": s.status,
        "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S") if s.created_at else "",
        "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M:%S") if s.updated_at else "",
    } for s in sessions]
    
    return success_response(data=sessions_data, message="获取会话列表成功")


@app.put("/api/chat-sessions/{session_id}")
async def update_chat_session(session_id: str, request: dict, db: Session = Depends(get_db)):
    """更新会话信息（重命名）"""
    db_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    new_name = request.get("name")
    if new_name:
        db_session.username = new_name
        db.commit()
    
    return success_response(data={"session_id": session_id, "name": db_session.username}, message="更新成功")


@app.delete("/api/chat-sessions/{session_id}")
async def delete_chat_session(session_id: str, db: Session = Depends(get_db)):
    """删除会话"""
    db_session = db.query(ChatSession).filter(ChatSession.session_id == session_id).first()
    if not db_session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    db.query(ChatMessage).filter(ChatMessage.session_id == session_id).delete()
    db.delete(db_session)
    db.commit()
    
    await short_term_memory.clear(session_id)
    
    return success_response(data={"session_id": session_id}, message="删除成功")


@app.get("/api/tools")
async def list_tools(db: Session = Depends(get_db)):
    """获取工具列表"""
    tools = db.query(Tool).all()
    
    tools_data = [{
        "id": t.id,
        "name": t.name,
        "tool_code": t.tool_code,
        "description": t.description,
        "icon": t.icon,
        "available": t.available,
    } for t in tools]
    
    return success_response(data=tools_data, message="获取工具列表成功")


@app.post("/api/tools/call")
async def call_tool(request: dict, db: Session = Depends(get_db)):
    """MCP工具调用接口"""
    import json
    result = await mcp_server.call_tool(
        name=request.get("name", ""),
        arguments=request.get("arguments", {}),
    )

    log = ToolCallLog(
        tool_name=request.get("name", ""),
        session_id=request.get("session_id"),
        user_id=request.get("user_id"),
        input_params=json.dumps(request.get("arguments", {})),
        output_result=json.dumps(result.result) if result.result else None,
        error_message=result.error,
        success=result.success,
        duration_ms=result.duration_ms,
    )
    db.add(log)
    db.commit()

    return success_response(
        data={
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "duration_ms": result.duration_ms,
        },
        message="工具调用成功" if result.success else "工具调用失败",
    )


@app.get("/api/metrics")
async def get_metrics(db: Session = Depends(get_db)):
    """获取系统指标"""
    today = datetime.utcnow().date()
    
    sessions = db.query(ChatSession).all()
    daily_sessions = sum(1 for s in sessions if s.created_at and s.created_at.date() == today)
    
    tool_calls = db.query(ToolCallLog).all()
    daily_tool_calls = sum(1 for c in tool_calls if c.created_at and c.created_at.date() == today)
    
    total_messages = db.query(ChatMessage).filter(
        ChatMessage.role == "assistant",
        ChatMessage.compliance_passed.isnot(None)
    ).count()
    
    passed_messages = db.query(ChatMessage).filter(
        ChatMessage.role == "assistant",
        ChatMessage.compliance_passed == True
    ).count()
    
    compliance_rate = (passed_messages / total_messages * 100) if total_messages > 0 else 100
    
    avg_response_result = db.query(func.avg(ChatMessage.response_time_ms)).filter(
        ChatMessage.role == "assistant",
        ChatMessage.response_time_ms.isnot(None)
    ).first()
    avg_response_time = avg_response_result[0] if avg_response_result[0] else 0
    
    metrics_data = [
        {
            "id": 1,
            "label": "今日会话数",
            "value": str(daily_sessions),
            "metric_type": "daily_sessions",
        },
        {
            "id": 2,
            "label": "今日工具调用",
            "value": str(daily_tool_calls),
            "metric_type": "daily_tool_calls",
        },
        {
            "id": 3,
            "label": "合规通过率",
            "value": f"{compliance_rate:.1f}%",
            "metric_type": "compliance_rate",
        },
        {
            "id": 4,
            "label": "平均响应时间",
            "value": f"{avg_response_time/1000:.1f}s",
            "metric_type": "avg_response_time",
        },
    ]

    recent_calls = db.query(ToolCallLog).order_by(
        ToolCallLog.created_at.desc()
    ).limit(10).all()

    recent_calls_data = [{
        "id": c.id,
        "name": c.tool_name,
        "time": c.created_at.strftime("%H:%M:%S") if c.created_at else "",
        "success": c.success,
    } for c in recent_calls]

    return success_response(
        data={
            "metrics": metrics_data,
            "recent_calls": recent_calls_data,
        },
        message="获取指标成功",
    )


@app.get("/api/chat-history")
async def get_chat_history(user_id: str | None = None, limit: int = 10, offset: int = 0, db: Session = Depends(get_db)):
    """获取对话历史记录（Dashboard用）"""
    base_query = db.query(
        ChatMessage.session_id,
        ChatMessage.content,
        ChatMessage.created_at,
        ChatMessage.role,
        ChatSession.username,
    ).join(ChatSession, ChatSession.session_id == ChatMessage.session_id)
    
    if user_id:
        base_query = base_query.filter(ChatSession.user_id == user_id)
    
    base_query = base_query.filter(ChatMessage.role == "user")
    
    total = base_query.count()
    
    history = base_query.order_by(
        ChatMessage.created_at.desc()
    ).offset(offset).limit(limit).all()
    
    history_data = [{
        "id": f"{h.session_id}_{hash(h.content)}",
        "session_id": h.session_id,
        "content": h.content,
        "time": h.created_at.strftime("%H:%M") if h.created_at else "",
        "username": h.username,
    } for h in history]
    
    return success_response(data={"list": history_data, "total": total}, message="获取历史记录成功")


@app.get("/api/tool-call-logs")
async def get_tool_call_logs(
    tool_name: str | None = None,
    session_id: str | None = None,
    success: bool | None = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """获取工具调用日志"""
    query = db.query(ToolCallLog).order_by(ToolCallLog.created_at.desc())
    
    if tool_name:
        query = query.filter(ToolCallLog.tool_name == tool_name)
    if session_id:
        query = query.filter(ToolCallLog.session_id == session_id)
    if success is not None:
        query = query.filter(ToolCallLog.success == success)
    
    total = query.count()
    
    logs = query.offset(offset).limit(limit).all()
    
    logs_data = [{
        "id": log.id,
        "tool_name": log.tool_name,
        "session_id": log.session_id or "",
        "user_id": log.user_id or "",
        "input_params": log.input_params or "",
        "output_result": log.output_result or "",
        "error_message": log.error_message or "",
        "success": log.success,
        "duration_ms": log.duration_ms,
        "created_at": log.created_at.strftime("%Y-%m-%d %H:%M:%S") if log.created_at else "",
    } for log in logs]
    
    return success_response(data={"data": logs_data, "total": total}, message="获取工具调用日志成功")


@app.post("/api/tool-call-logs")
async def create_tool_call_log(
    request: dict,
    db: Session = Depends(get_db),
):
    """记录工具调用日志"""
    log_entry = ToolCallLog(
        tool_name=request.get("tool_name"),
        session_id=request.get("session_id"),
        user_id=request.get("user_id"),
        input_params=request.get("input_params"),
        output_result=request.get("output_result"),
        error_message=request.get("error_message"),
        success=request.get("success"),
        duration_ms=request.get("duration_ms"),
    )
    db.add(log_entry)
    db.commit()
    
    return success_response(data={"id": log_entry.id}, message="日志记录成功")


captcha_store: dict[str, str] = {}

@app.get("/api/captcha")
async def get_captcha():
    """获取图形验证码"""
    captcha_id = str(uuid.uuid4())
    captcha_code = generate_captcha_code()
    image_bytes = generate_captcha_image(captcha_code)

    try:
        r = await short_term_memory._get_redis()
        if r is not None:
            await r.ping()
            await r.setex(f"captcha:{captcha_id}", 300, captcha_code)
        else:
            captcha_store[captcha_id] = captcha_code
    except Exception:
        captcha_store[captcha_id] = captcha_code

    print(f"[验证码生成] ID: {captcha_id[:8]}..., Code: {captcha_code}")

    import base64
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    image_data_url = f"data:image/png;base64,{image_base64}"

    return success_response(
        data={"captcha_id": captcha_id, "image": image_data_url},
        message="获取验证码成功",
    )


@app.post("/api/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """用户登录接口"""
    print(f"[登录请求] 用户名: {request.username}, 密码长度: {len(request.password)}")

    user = db.query(User).filter(User.username == request.username).first()
    if not user:
        msg = "用户不存在" if DEBUG else "用户名或密码错误"
        print(f"[登录失败] 用户不存在: {request.username}")
        raise HTTPException(status_code=401, detail=msg)

    if not verify_password(request.password, user.password_hash):
        msg = "密码错误" if DEBUG else "用户名或密码错误"
        print(f"[登录失败] 密码验证失败: {request.username}")
        raise HTTPException(status_code=401, detail=msg)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    print(f"[登录成功] 用户: {request.username}, 角色: {user.role}")
    return success_response(
        data=LoginData(token=access_token, username=user.username, role=user.role),
        message="登录成功",
    )


@app.post("/api/register")
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """用户注册接口"""
    print(f"[注册请求] 用户名: {request.username}, 角色: {request.role}")

    stored_code = None

    try:
        r = await short_term_memory._get_redis()
        if r is not None:
            await r.ping()
            stored_code = await r.get(f"captcha:{request.captcha_id}")
            if stored_code:
                await r.delete(f"captcha:{request.captcha_id}")
    except Exception:
        pass

    if stored_code is None:
        stored_code = captcha_store.pop(request.captcha_id, None)

    if not stored_code:
        print(f"[注册失败] 验证码已过期: {request.captcha_id[:8]}...")
        raise HTTPException(status_code=400, detail="验证码已过期，请刷新重试")

    if stored_code.lower() != request.captcha_code.lower():
        print(f"[注册失败] 验证码错误: {request.captcha_code} vs {stored_code}")
        raise HTTPException(status_code=400, detail="验证码错误")

    existing_user = db.query(User).filter(User.username == request.username).first()
    if existing_user:
        print(f"[注册失败] 用户已存在: {request.username}")
        raise HTTPException(status_code=400, detail="用户名已存在")

    if len(request.password) < 6:
        print(f"[注册失败] 密码过短: {request.username}")
        raise HTTPException(status_code=400, detail="密码长度至少6位")

    hashed_password = pwd_context.hash(request.password)
    new_user = User(
        username=request.username,
        password_hash=hashed_password,
        role=request.role,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": new_user.username, "role": new_user.role},
        expires_delta=access_token_expires,
    )

    print(f"[注册成功] 用户: {request.username}, 角色: {request.role}")
    return success_response(
        data=LoginData(token=access_token, username=new_user.username, role=new_user.role),
        message="注册成功",
    )


@app.get("/api/tickets")
async def list_tickets(
    user_id: str | None = None,
    status: str | None = None,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取工单列表"""
    query = db.query(Ticket)
    if user_id:
        query = query.filter(Ticket.user_id == user_id)
    if status:
        query = query.filter(Ticket.status == status)
    
    tickets = query.order_by(Ticket.created_at.desc()).limit(limit).all()
    
    return success_response(
        data=[{
            "id": t.id,
            "ticket_id": t.ticket_id,
            "type": t.type,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "status": t.status,
            "user_id": t.user_id,
            "username": t.username,
            "assignee": t.assignee,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "updated_at": t.updated_at.isoformat() if t.updated_at else None,
        } for t in tickets],
        message="获取成功",
    )


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """获取单个工单详情"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    return success_response(
        data={
            "id": ticket.id,
            "ticket_id": ticket.ticket_id,
            "type": ticket.type,
            "title": ticket.title,
            "description": ticket.description,
            "priority": ticket.priority,
            "status": ticket.status,
            "user_id": ticket.user_id,
            "username": ticket.username,
            "assignee": ticket.assignee,
            "created_at": ticket.created_at.isoformat() if ticket.created_at else None,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        },
        message="获取成功",
    )


@app.post("/api/tickets")
async def create_ticket(request: dict, db: Session = Depends(get_db)):
    """创建工单"""
    ticket_id = f"TK-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    
    new_ticket = Ticket(
        ticket_id=ticket_id,
        type=request.get("type", "general"),
        title=request.get("title", ""),
        description=request.get("description", ""),
        priority=request.get("priority", "medium"),
        status="created",
        user_id=request.get("user_id", ""),
        username=request.get("username", ""),
    )
    
    db.add(new_ticket)
    db.commit()
    db.refresh(new_ticket)
    
    return success_response(
        data={
            "ticket_id": new_ticket.ticket_id,
            "type": new_ticket.type,
            "title": new_ticket.title,
            "priority": new_ticket.priority,
            "status": new_ticket.status,
            "created_at": new_ticket.created_at.isoformat() if new_ticket.created_at else None,
        },
        message="工单创建成功",
    )


@app.put("/api/tickets/{ticket_id}")
async def update_ticket(ticket_id: str, request: dict, db: Session = Depends(get_db)):
    """更新工单"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    if "status" in request:
        ticket.status = request["status"]
    if "priority" in request:
        ticket.priority = request["priority"]
    if "assignee" in request:
        ticket.assignee = request["assignee"]
    if "title" in request:
        ticket.title = request["title"]
    if "description" in request:
        ticket.description = request["description"]
    
    db.commit()
    db.refresh(ticket)
    
    return success_response(
        data={
            "ticket_id": ticket.ticket_id,
            "status": ticket.status,
            "priority": ticket.priority,
            "assignee": ticket.assignee,
            "updated_at": ticket.updated_at.isoformat() if ticket.updated_at else None,
        },
        message="工单更新成功",
    )


@app.delete("/api/tickets/{ticket_id}")
async def delete_ticket(ticket_id: str, db: Session = Depends(get_db)):
    """删除工单"""
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="工单不存在")
    
    db.delete(ticket)
    db.commit()
    
    return success_response(
        data={"ticket_id": ticket_id},
        message="工单删除成功",
    )


@app.get("/health")
async def health_check():
    return success_response(
        data={"status": "healthy", "version": "1.0.0"},
        message="服务正常",
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=True,
    )
