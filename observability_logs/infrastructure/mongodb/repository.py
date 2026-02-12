from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pymongo.collection import Collection
from pymongo import ASCENDING, DESCENDING
from bson import ObjectId

from observability_logs.domain.entities import LogEntry
from observability_logs.infrastructure.mongodb.connection import mongodb_connection


class MongoDBLogRepository:
    """
    Repositorio para MongoDB
    ✅ SIN SQL
    ✅ SIN Esquema rígido
    ✅ Escalable horizontalmente
    ✅ TTL automático
    """
    def is_connected(self) -> bool:
        try:
            if not mongodb_connection._client or not mongodb_connection._db:
                return False
            mongodb_connection._client.admin.command("ping")
            return True
        except Exception:
            return False

    def __init__(self):
        # 🔥 USAR conexión inicializada
        self.collection: Collection = mongodb_connection.logs

    def save(self, log: LogEntry) -> LogEntry:
        """Guarda un log en MongoDB"""
        log_dict = {
            "trace_id": log.trace_id,
            "level": log.level,
            "category": log.category,
            "action": log.action,
            "message": log.message,
            "user_id": log.user_id,
            "role": log.role,
            "ip": log.ip,
            "endpoint": log.endpoint,
            "metadata": log.metadata,
            "timestamp": log.timestamp,
            "created_at": datetime.utcnow()
        }

        result = self.collection.insert_one(log_dict)
        log.id = str(result.inserted_id)

        return log

    def save_many(self, logs: List[LogEntry]) -> List[LogEntry]:
        if not logs:
            return []

        docs = []
        for log in logs:
            docs.append({
                "trace_id": log.trace_id,
                "level": log.level,
                "category": log.category,
                "action": log.action,
                "message": log.message,
                "user_id": log.user_id,
                "role": log.role,
                "ip": log.ip,
                "endpoint": log.endpoint,
                "metadata": log.metadata,
                "timestamp": log.timestamp,
                "created_at": datetime.utcnow()
            })

        result = self.collection.insert_many(docs)

        for log, _id in zip(logs, result.inserted_ids):
            log.id = str(_id)

        return logs

    def find_by_trace_id(self, trace_id: str) -> List[LogEntry]:
        cursor = self.collection.find(
            {"trace_id": trace_id}
        ).sort("timestamp", ASCENDING)

        return [self._document_to_entity(doc) for doc in cursor]

    def find_by_user(self, user_id: str, since: Optional[datetime] = None) -> List[LogEntry]:
        query = {"user_id": user_id}
        if since:
            query["timestamp"] = {"$gte": since}

        cursor = self.collection.find(query).sort("timestamp", DESCENDING)
        return [self._document_to_entity(doc) for doc in cursor]

    def find_by_ip(self, ip: str, since: Optional[datetime] = None) -> List[LogEntry]:
        query = {"ip": ip}
        if since:
            query["timestamp"] = {"$gte": since}

        cursor = self.collection.find(query).sort("timestamp", DESCENDING)
        return [self._document_to_entity(doc) for doc in cursor]

    def get_since(self, since: datetime) -> List[LogEntry]:
        cursor = self.collection.find(
            {"timestamp": {"$gte": since}}
        ).sort("timestamp", DESCENDING)

        return [self._document_to_entity(doc) for doc in cursor]

    def search(self, query: Dict[str, Any], limit: int = 100) -> List[LogEntry]:
        cursor = self.collection.find(query).sort("timestamp", DESCENDING).limit(limit)
        return [self._document_to_entity(doc) for doc in cursor]

    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict]:
        return list(self.collection.aggregate(pipeline))

    def count_by_category(self, since: datetime) -> Dict[str, int]:
        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$group": {"_id": "$category", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}}
        ]

        return {doc["_id"]: doc["count"] for doc in self.collection.aggregate(pipeline)}

    def get_stats(self, days: int = 7) -> Dict[str, Any]:
        since = datetime.utcnow() - timedelta(days=days)

        pipeline = [
            {"$match": {"timestamp": {"$gte": since}}},
            {"$facet": {
                "by_level": [
                    {"$group": {"_id": "$level", "count": {"$sum": 1}}}
                ],
                "by_category": [
                    {"$group": {"_id": "$category", "count": {"$sum": 1}}}
                ],
                "top_users": [
                    {"$group": {"_id": "$user_id", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ],
                "top_ips": [
                    {"$group": {"_id": "$ip", "count": {"$sum": 1}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ],
                "errors": [
                    {"$match": {"level": {"$in": ["error", "critical"]}}},
                    {"$count": "count"}
                ],
                "total": [
                    {"$count": "count"}
                ]
            }}
        ]

        result = next(self.collection.aggregate(pipeline), {})

        return {
            "period_days": days,
            "total": result.get("total", [{}])[0].get("count", 0),
            "errors": result.get("errors", [{}])[0].get("count", 0),
            "by_level": {i["_id"]: i["count"] for i in result.get("by_level", [])},
            "by_category": {i["_id"]: i["count"] for i in result.get("by_category", [])},
            "top_users": result.get("top_users", []),
            "top_ips": result.get("top_ips", [])
        }

    def _document_to_entity(self, doc: Dict) -> LogEntry:
        return LogEntry(
            id=str(doc["_id"]),
            trace_id=doc["trace_id"],
            level=doc["level"],
            category=doc["category"],
            action=doc["action"],
            message=doc["message"],
            user_id=doc.get("user_id"),
            role=doc.get("role"),
            ip=doc.get("ip"),
            endpoint=doc.get("endpoint"),
            metadata=doc.get("metadata", {}),
            timestamp=doc["timestamp"]
        )
