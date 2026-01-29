#!/usr/bin/env python
"""
CUSTOS RQ Worker

Start background task workers for processing AI jobs.

Usage:
    # Start a single worker (all queues)
    python scripts/worker.py
    
    # Start worker for specific queues
    python scripts/worker.py --queues custos_high,custos
    
    # Start with custom burst mode (process queue then exit)
    python scripts/worker.py --burst
"""

import sys
import os
import argparse
import logging

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rq import Worker, Queue
from redis import Redis

from app.core.config import settings


def setup_logging():
    """Configure logging for worker."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )


def get_redis():
    """Get Redis connection."""
    redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
    return Redis.from_url(redis_url)


def main():
    parser = argparse.ArgumentParser(description="CUSTOS RQ Worker")
    parser.add_argument(
        "--queues",
        default="custos_high,custos,custos_ai,custos_low",
        help="Comma-separated list of queues to process (in priority order)",
    )
    parser.add_argument(
        "--burst",
        action="store_true",
        help="Run in burst mode (process queue then exit)",
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Worker name (default: auto-generated)",
    )
    
    args = parser.parse_args()
    
    setup_logging()
    logger = logging.getLogger("custos.worker")
    
    redis_conn = get_redis()
    
    # Test Redis connection
    try:
        redis_conn.ping()
        logger.info("Connected to Redis")
    except Exception as e:
        logger.error(f"Cannot connect to Redis: {e}")
        sys.exit(1)
    
    # Parse queue names
    queue_names = [q.strip() for q in args.queues.split(",")]
    queues = [Queue(name, connection=redis_conn) for name in queue_names]
    
    logger.info(f"Starting worker for queues: {queue_names}")
    
    # Create and start worker
    worker = Worker(
        queues,
        connection=redis_conn,
        name=args.name,
    )
    
    worker.work(burst=args.burst)


if __name__ == "__main__":
    main()
