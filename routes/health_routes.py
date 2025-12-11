# routes/health_routes.py
from flask import Blueprint, jsonify, current_app
from models import db
from datetime import datetime
import psutil
import os

health_bp = Blueprint('health', __name__, url_prefix='/api')

@health_bp.route('/health', methods=['GET'])
def health_check():
    """Basic health check endpoint"""
    try:
        # Test database connection
        db.session.execute(db.text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    # Get system metrics
    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    health_status = {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": db_status,
        "memory_mb": round(memory_usage, 2),
        "environment": os.getenv('FLASK_ENV', 'unknown')
    }
    
    status_code = 200 if health_status["status"] == "healthy" else 503
    return jsonify(health_status), status_code

@health_bp.route('/status', methods=['GET'])
def status_check():
    """Detailed status endpoint"""
    try:
        # Database health
        start_time = datetime.now()
        db.session.execute(db.text("SELECT 1"))
        db_response_time = (datetime.now() - start_time).total_seconds() * 1000
        
        # System metrics
        process = psutil.Process()
        memory_info = process.memory_info()
        
        status = {
            "status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "services": {
                "database": {
                    "status": "healthy",
                    "response_time_ms": round(db_response_time, 2)
                },
                "application": {
                    "status": "healthy",
                    "memory_usage_mb": round(memory_info.rss / 1024 / 1024, 2),
                    "cpu_percent": psutil.cpu_percent()
                }
            },
            "metadata": {
                "environment": os.getenv('FLASK_ENV', 'unknown'),
                "debug": current_app.debug,
                "version": "1.0.0"
            }
        }
        
        return jsonify(status), 200
        
    except Exception as e:
        error_status = {
            "status": "error",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }
        return jsonify(error_status), 503

@health_bp.route('/ready', methods=['GET'])
def readiness_check():
    """Readiness probe for container orchestration"""
    try:
        # Check critical dependencies
        db.session.execute(db.text("SELECT 1"))
        
        return jsonify({
            "status": "ready",
            "timestamp": datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "not_ready",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }), 503

@health_bp.route('/live', methods=['GET'])
def liveness_check():
    """Liveness probe for container orchestration"""
    return jsonify({
        "status": "alive",
        "timestamp": datetime.utcnow().isoformat()
    }), 200
