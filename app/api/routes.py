import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.models.request import ChatRequest
from app.models.response import ChatResponse, HistoryResponse, HistoryMessage, ResponseType
from app.services.intent_recognition import IntentRecognition
from app.services.query_rewrite import QueryRewrite
from app.services.table_retrieval import TableRetrieval
from app.services.permission import PermissionService
from app.services.nl2sql import NL2SQLService
from app.services.sql_executor import SQLExecutor
from app.services.result_summary import ResultSummaryService
from app.services.history import HistoryService
from app.services.chat import ChatService
import logging
import json
import asyncio

logger = logging.getLogger(__name__)

router = APIRouter()

_intent_recognition = None
_query_rewrite = None
_table_retrieval = None
_permission_service = None
_nl2sql_service = None
_sql_executor = None
_history_service = None
_result_summary_service = None
_chat_service = None


def get_intent_recognition():
    global _intent_recognition
    if _intent_recognition is None:
        _intent_recognition = IntentRecognition()
    return _intent_recognition


def get_chat_service():
    global _chat_service
    if _chat_service is None:
        _chat_service = ChatService()
    return _chat_service


def get_query_rewrite():
    global _query_rewrite
    if _query_rewrite is None:
        _query_rewrite = QueryRewrite()
    return _query_rewrite


def get_table_retrieval():
    global _table_retrieval
    if _table_retrieval is None:
        _table_retrieval = TableRetrieval()
    return _table_retrieval


def get_permission_service():
    global _permission_service
    if _permission_service is None:
        _permission_service = PermissionService()
    return _permission_service


def get_nl2sql_service():
    global _nl2sql_service
    if _nl2sql_service is None:
        _nl2sql_service = NL2SQLService()
    return _nl2sql_service


def get_sql_executor():
    global _sql_executor
    if _sql_executor is None:
        _sql_executor = SQLExecutor()
    return _sql_executor


def get_history_service():
    global _history_service
    if _history_service is None:
        _history_service = HistoryService()
    return _history_service


def get_result_summary_service():
    global _result_summary_service
    if _result_summary_service is None:
        _result_summary_service = ResultSummaryService()
    return _result_summary_service


async def generate_stream_response(content: str):
    for char in content:
        yield f"data: {json.dumps({'content': char})}\n\n"
        await asyncio.sleep(0.02)
    yield f"data: {json.dumps({'done': True})}\n\n"


@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    logger.info(f"Received stream chat request: session_id={request.session_id}, user_id={request.user_id}")
    
    intent_recognition = get_intent_recognition()
    query_rewrite = get_query_rewrite()
    table_retrieval = get_table_retrieval()
    permission_service = get_permission_service()
    nl2sql_service = get_nl2sql_service()
    sql_executor = get_sql_executor()
    history_service = get_history_service()
    result_summary_service = get_result_summary_service()
    
    try:
        rewritten_question = request.question
        
        has_history = await history_service.get_recent_history(
            request.session_id, request.user_id, 1
        )
        
        if has_history:
            rewritten_question = await query_rewrite.rewrite(
                request.session_id, request.user_id, request.question
            )
            logger.info(f"问题改写: {request.question} -> {rewritten_question}")
        
        intent = await intent_recognition.recognize(rewritten_question)
        logger.info(f"Intent recognized: {intent}")
        
        if intent == "chat":
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            chat_service = get_chat_service()
            response_content = await chat_service.chat(rewritten_question)
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", response_content
            )
            return StreamingResponse(
                generate_stream_response(response_content),
                media_type="text/event-stream"
            )
        
        table_descriptions = await table_retrieval.retrieve(rewritten_question)
        
        if not table_descriptions:
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            response_content = "抱歉，当前没有找到与您问题相关的表结构数据。请联系管理员确认向量索引是否已构建。"
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", response_content
            )
            return StreamingResponse(
                generate_stream_response(response_content),
                media_type="text/event-stream"
            )
        
        logger.info(f"Retrieved {len(table_descriptions)} table descriptions")
        
        sql = await nl2sql_service.generate(table_descriptions, rewritten_question)
        logger.info(f"Generated SQL: {sql}")
        
        has_permission, error_msg = permission_service.check_permission(request.user_id, sql)
        if not has_permission:
            logger.warning(f"Permission denied: {error_msg}")
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", error_msg, sql
            )
            return StreamingResponse(
                generate_stream_response(error_msg),
                media_type="text/event-stream"
            )
        
        success, sql_result, executed_sql = await sql_executor.execute(sql)
        
        if not success:
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", sql_result, executed_sql
            )
            return StreamingResponse(
                generate_stream_response(sql_result),
                media_type="text/event-stream"
            )
        
        logger.info(f"SQL executed successfully, summarizing result...")
        
        summarized_content = await result_summary_service.summarize(request.question, sql_result)
        
        await history_service.add_message(
            request.session_id, request.user_id, "user", request.question
        )
        await history_service.add_message(
            request.session_id, request.user_id, "assistant", summarized_content, executed_sql
        )
        
        return StreamingResponse(
            generate_stream_response(summarized_content),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        error_content = f"抱歉，发生了错误: {str(e)}"
        return StreamingResponse(
            generate_stream_response(error_content),
            media_type="text/event-stream"
        )


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    logger.info(f"Received chat request: session_id={request.session_id}, user_id={request.user_id}")
    
    intent_recognition = get_intent_recognition()
    query_rewrite = get_query_rewrite()
    table_retrieval = get_table_retrieval()
    permission_service = get_permission_service()
    nl2sql_service = get_nl2sql_service()
    sql_executor = get_sql_executor()
    history_service = get_history_service()
    result_summary_service = get_result_summary_service()
    
    try:
        rewritten_question = request.question
        
        has_history = await history_service.get_recent_history(
            request.session_id, request.user_id, 1
        )
        
        if has_history:
            rewritten_question = await query_rewrite.rewrite(
                request.session_id, request.user_id, request.question
            )
            logger.info(f"问题改写: {request.question} -> {rewritten_question}")
        
        intent = await intent_recognition.recognize(rewritten_question)
        logger.info(f"Intent recognized: {intent}")
        
        if intent == "chat":
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            chat_service = get_chat_service()
            response_content = await chat_service.chat(rewritten_question)
            response = ChatResponse(
                session_id=request.session_id,
                type=ResponseType.CHAT,
                content=response_content
            )
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", response.content
            )
            return response
        
        table_descriptions = await table_retrieval.retrieve(rewritten_question)
        
        if not table_descriptions:
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            no_table_response = ChatResponse(
                session_id=request.session_id,
                type=ResponseType.ERROR,
                content="抱歉，当前没有找到与您问题相关的表结构数据。请联系管理员确认向量索引是否已构建。"
            )
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", no_table_response.content
            )
            return no_table_response
        
        logger.info(f"Retrieved {len(table_descriptions)} table descriptions")
        
        sql = await nl2sql_service.generate(table_descriptions, rewritten_question)
        logger.info(f"Generated SQL: {sql}")
        
        has_permission, error_msg = permission_service.check_permission(request.user_id, sql)
        if not has_permission:
            logger.warning(f"Permission denied: {error_msg}")
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", error_msg, sql
            )
            return ChatResponse(
                session_id=request.session_id,
                type=ResponseType.ERROR,
                content=error_msg,
                sql=None
            )
        
        success, sql_result, executed_sql = await sql_executor.execute(sql)
        
        if not success:
            await history_service.add_message(
                request.session_id, request.user_id, "user", request.question
            )
            await history_service.add_message(
                request.session_id, request.user_id, "assistant", sql_result, executed_sql
            )
            return ChatResponse(
                session_id=request.session_id,
                type=ResponseType.ERROR,
                content=sql_result,
                sql=None
            )
        
        logger.info(f"SQL executed successfully, summarizing result...")
        
        summarized_content = await result_summary_service.summarize(request.question, sql_result)
        
        await history_service.add_message(
            request.session_id, request.user_id, "user", request.question
        )
        await history_service.add_message(
            request.session_id, request.user_id, "assistant", summarized_content, executed_sql
        )
        
        return ChatResponse(
            session_id=request.session_id,
            type=ResponseType.QUERY,
            content=summarized_content,
            sql=None
        )
        
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"服务器内部错误: {str(e)}")


@router.get("/history", response_model=HistoryResponse)
async def get_history(
    session_id: str = Query(..., description="会话ID"),
    user_id: str = Query(..., description="用户ID"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    logger.info(f"Get history: session_id={session_id}, user_id={user_id}, limit={limit}")
    
    history_service = get_history_service()
    messages = await history_service.get_history(session_id, user_id, limit)
    
    return HistoryResponse(
        session_id=session_id,
        messages=[
            HistoryMessage(
                role=m["role"],
                content=m["content"],
                sql=m.get("sql"),
                created_at=m["created_at"]
            )
            for m in messages
        ]
    )
