from pydantic import BaseModel, Field
from typing import Optional, Literal, Dict, Any, List
from enum import Enum
from datetime import datetime

class UserRole(str, Enum):
    USER = "user"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    MODERATOR = "moderator"
    SUPPORT = "support"

class UserSession(BaseModel):
    user_id: str
    username: str
    email: str
    role: UserRole
    session_id: str
    login_time: datetime
    last_activity: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    is_active: bool = True

class WSMessageSchema(BaseModel):
    type: str = Field(..., description="Tipo de mensaje")
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.now)
    channel: Optional[str] = None
    target_user_id: Optional[str] = None
    message_id: Optional[str] = None

class AuthMessageSchema(WSMessageSchema):
    token: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    client_version: Optional[str] = None

class NotificationSchema(BaseModel):
    title: str
    message: str
    notification_type: Literal["info", "warning", "error", "success", "alert"]
    priority: Literal["low", "medium", "high", "critical"]
    data: Optional[Dict[str, Any]] = None
    expires_at: Optional[datetime] = None
    action_url: Optional[str] = None
    category: Optional[str] = None

class SystemHealthStatus(BaseModel):
    status: Literal["healthy", "degraded", "unhealthy", "maintenance"]
    total_connections: int
    active_channels: int
    uptime_hours: float
    message_throughput: int
    connection_success_rate: float
    timestamp: datetime = Field(default_factory=datetime.now)
    details: Optional[Dict[str, Any]] = None
    warnings: Optional[List[str]] = None
    errors: Optional[List[str]] = None

class ConnectionMetrics(BaseModel):
    total_connections: int
    failed_connections: int
    messages_processed: int
    messages_failed: int
    channels_created: int
    timestamp: datetime = Field(default_factory=datetime.now)
    period_start: datetime
    period_end: datetime

class ErrorReportSchema(BaseModel):
    error_type: str
    message: str
    stack_trace: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    severity: Literal["low", "medium", "high", "critical"]
    component: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class BroadcastRequest(BaseModel):
    message: Dict[str, Any]
    target_channels: Optional[List[str]] = None
    target_roles: Optional[List[UserRole]] = None
    exclude_users: Optional[List[str]] = None
    priority: Literal["low", "medium", "high"] = "medium"
    expires_at: Optional[datetime] = None

class UserActivitySchema(BaseModel):
    user_id: str
    activity_type: str
    details: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.now)
    channel: Optional[str] = None
    ip_address: Optional[str] = None

class HeartbeatSchema(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    client_id: Optional[str] = None
    latency_ms: Optional[float] = None

class DisconnectNoticeSchema(BaseModel):
    reason: str
    code: Optional[int] = None
    reconnect_after: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)

class AdminCommandSchema(BaseModel):
    command: str
    parameters: Dict[str, Any]
    requester_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    requires_confirmation: bool = False

class BulkOperationResult(BaseModel):
    operation_id: str
    successful: int
    failed: int
    errors: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    duration_ms: float

class PerformanceMetrics(BaseModel):
    connections_per_minute: float
    message_throughput: int
    avg_response_time_ms: float
    error_rate: float
    memory_usage_mb: float
    timestamp: datetime = Field(default_factory=datetime.now)