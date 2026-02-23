"""
审计日志工具：全链路操作留痕、可追溯、可导出
ESG合规核心工具：所有操作永久留存
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from src.core_config.paths import SQLITE_DB_DIR
from src.utils.hash_utils import generate_sha256_hash
from src.utils.exception_utils import AuditException


# 审计日志数据库路径
AUDIT_DB_PATH = SQLITE_DB_DIR / "audit_log.db"


def init_audit_db() -> None:
    """初始化审计日志数据库（仅在第一次运行时执行）"""
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        # 创建审计日志表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                operation_type TEXT NOT NULL,
                operator TEXT NOT NULL,
                operation_detail TEXT NOT NULL,
                status TEXT NOT NULL,
                error_info TEXT,
                log_hash TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()
    except Exception as e:
        raise AuditException(f"审计日志数据库初始化失败: {str(e)}", original_exception=e) from e


def write_audit_log(
    operation_type: str,
    operator: str,
    operation_detail: Dict[str, Any],
    status: str = "success",
    error_info: Optional[str] = None,
) -> None:
    """
    写入审计日志（自动生成哈希值，防止篡改）
    :param operation_type: 操作类型（如CORPUS_UPLOAD, EXTRACTION, REVIEW等）
    :param operator: 操作人（如admin, user1）
    :param operation_detail: 操作详情（字典，自动转JSON）
    :param status: 操作状态（success/failed/pending）
    :param error_info: 错误信息（仅status为failed时填写）
    """
    # 确保数据库已初始化
    if not AUDIT_DB_PATH.exists():
        init_audit_db()
    
    try:
        # 生成日志内容（用于哈希计算）
        log_content = {
            "timestamp": datetime.utcnow().isoformat(),
            "operation_type": operation_type,
            "operator": operator,
            "operation_detail": operation_detail,
            "status": status,
            "error_info": error_info,
        }
        log_json = json.dumps(log_content, sort_keys=True, ensure_ascii=False)
        log_hash = generate_sha256_hash(log_json)
        
        # 写入数据库
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO audit_log (
                timestamp, operation_type, operator, operation_detail, 
                status, error_info, log_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            log_content["timestamp"],
            operation_type,
            operator,
            json.dumps(operation_detail, ensure_ascii=False),
            status,
            error_info,
            log_hash,
        ))
        conn.commit()
        conn.close()
    except Exception as e:
        raise AuditException(f"审计日志写入失败: {str(e)}", original_exception=e) from e


def query_audit_logs(
    operation_type: Optional[str] = None,
    operator: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    查询审计日志
    :param operation_type: 操作类型过滤
    :param operator: 操作人过滤
    :param start_time: 开始时间过滤（ISO格式）
    :param end_time: 结束时间过滤（ISO格式）
    :param limit: 返回数量限制
    :return: 审计日志列表
    """
    try:
        conn = sqlite3.connect(AUDIT_DB_PATH)
        cursor = conn.cursor()
        
        # 构建查询SQL
        sql = "SELECT * FROM audit_log WHERE 1=1"
        params = []
        if operation_type:
            sql += " AND operation_type = ?"
            params.append(operation_type)
        if operator:
            sql += " AND operator = ?"
            params.append(operator)
        if start_time:
            sql += " AND timestamp >= ?"
            params.append(start_time)
        if end_time:
            sql += " AND timestamp <= ?"
            params.append(end_time)
        sql += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(sql, params)
        rows = cursor.fetchall()
        
        # 转换为字典
        columns = [desc[0] for desc in cursor.description]
        logs = []
        for row in rows:
            log = dict(zip(columns, row))
            log["operation_detail"] = json.loads(log["operation_detail"])
            logs.append(log)
        
        conn.close()
        return logs
    except Exception as e:
        raise AuditException(f"审计日志查询失败: {str(e)}", original_exception=e) from e
