from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from infrastructure.mongodb.repository import MongoDBLogRepository
#from ..infrastructure.mongodb.repository import MongoDBLogRepository


class MongoLogQueryService:
    """Servicio de consultas avanzadas OPTIMIZADO para MongoDB"""
    
    def __init__(self, repository: MongoDBLogRepository):
        self.repository = repository
    
    def get_user_timeline(self, user_id: str, days: int = 7) -> Dict[str, Any]:
        """Timeline completo de usuario con agregaciones"""
        since = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            {"$match": {
                "user_id": user_id,
                "timestamp": {"$gte": since}
            }},
            {"$sort": {"timestamp": 1}},
            {"$group": {
                "_id": {
                    "date": {"$dateToString": {"format": "%Y-%m-%d", "date": "$timestamp"}},
                    "hour": {"$hour": "$timestamp"}
                },
                "count": {"$sum": 1},
                "actions": {"$push": "$action"},
                "ips": {"$addToSet": "$ip"}
            }},
            {"$sort": {"_id.date": -1, "_id.hour": -1}}
        ]
        
        results = self.repository.aggregate(pipeline)
        
        return {
            "user_id": user_id,
            "period": f"{days}d",
            "timeline": results
        }
    
    def detect_brute_force_ongoing(self, threshold: int = 10) -> List[Dict]:
        """Detecta ataques de fuerza bruta EN VIVO"""
        five_min_ago = datetime.utcnow() - timedelta(minutes=5)
        
        pipeline = [
            {"$match": {
                "category": "security",
                "action": {"$regex": "FAILED"},
                "timestamp": {"$gte": five_min_ago}
            }},
            {"$group": {
                "_id": "$ip",
                "attempts": {"$sum": 1},
                "users_targeted": {"$addToSet": "$user_id"},
                "last_attempt": {"$max": "$timestamp"}
            }},
            {"$match": {
                "attempts": {"$gte": threshold}
            }},
            {"$sort": {"attempts": -1}}
        ]
        
        return self.repository.aggregate(pipeline)
    
    def get_security_dashboard(self) -> Dict[str, Any]:
        """Dashboard de seguridad en tiempo real"""
        now = datetime.utcnow()
        one_hour_ago = now - timedelta(hours=1)
        one_day_ago = now - timedelta(days=1)
        
        # Pipeline paralelo con $facet
        pipeline = [
            {"$match": {
                "category": "security",
                "timestamp": {"$gte": one_day_ago}
            }},
            {"$facet": {
                "last_hour": [
                    {"$match": {"timestamp": {"$gte": one_hour_ago}}},
                    {"$count": "count"}
                ],
                "by_ip": [
                    {"$group": {
                        "_id": "$ip",
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"count": -1}},
                    {"$limit": 10}
                ],
                "by_action": [
                    {"$group": {
                        "_id": "$action",
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"count": -1}}
                ],
                "timeline": [
                    {"$group": {
                        "_id": {
                            "hour": {"$hour": "$timestamp"}
                        },
                        "count": {"$sum": 1}
                    }},
                    {"$sort": {"_id.hour": 1}}
                ]
            }}
        ]
        
        result = self.repository.aggregate(pipeline)
        if result:
            return result[0]
        return {}