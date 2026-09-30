"""
Data Logger Module

Handles logging and storage of vehicle telemetry and monitoring data.
Supports real-time logging and historical data queries.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import numpy as np


class DataLogger:
    """
    Logs vehicle telemetry data to file and database.
    """

    def __init__(
        self,
        vehicle_id: str,
        log_dir: str = "logs",
        db_path: str = "data/vehicle_telemetry.db",
    ):
        """
        Initialize the data logger.

        Args:
            vehicle_id: Vehicle identifier
            log_dir: Directory for log files
            db_path: Path to SQLite database
        """
        self.vehicle_id = vehicle_id
        self.log_dir = Path(log_dir)
        self.db_path = Path(db_path)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._initialize_database()

    def _initialize_database(self) -> None:
        """Initialize database schema if not exists."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                gross_weight REAL,
                payload REAL,
                load_balance REAL,
                payload_utilization REAL,
                is_overloaded BOOLEAN,
                session_id TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS axle_loads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                axle_id INTEGER NOT NULL,
                load REAL,
                load_percentage REAL,
                session_id TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                sensor_id TEXT NOT NULL,
                sensor_type TEXT,
                value REAL,
                accuracy REAL,
                status TEXT,
                session_id TEXT
            )
        """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                vehicle_id TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                event_type TEXT NOT NULL,
                severity TEXT,
                description TEXT,
                session_id TEXT
            )
        """
        )

        conn.commit()
        conn.close()

    def log_telemetry(self, data: Dict[str, Any]) -> None:
        """Log vehicle telemetry data to database."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO telemetry
            (vehicle_id, timestamp, gross_weight, payload, load_balance,
             payload_utilization, is_overloaded, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.vehicle_id,
                datetime.now(),
                data.get("gross_weight"),
                data.get("payload"),
                data.get("load_balance"),
                data.get("payload_utilization"),
                data.get("is_overloaded"),
                self.session_id,
            ),
        )

        conn.commit()
        conn.close()

    def log_axle_loads(self, axle_data: List[Dict[str, Any]]) -> None:
        """Log individual axle load data."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        for axle in axle_data:
            cursor.execute(
                """
                INSERT INTO axle_loads
                (vehicle_id, timestamp, axle_id, load, load_percentage, session_id)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    self.vehicle_id,
                    datetime.now(),
                    axle["id"],
                    axle["current_load"],
                    axle["load_percentage"],
                    self.session_id,
                ),
            )

        conn.commit()
        conn.close()

    def log_sensor_reading(self, sensor_data: Dict[str, Any]) -> None:
        """Log individual sensor reading."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO sensor_readings
            (vehicle_id, timestamp, sensor_id, sensor_type, value, accuracy, status, session_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                self.vehicle_id,
                datetime.now(),
                sensor_data.get("sensor_id"),
                sensor_data.get("sensor_type"),
                sensor_data.get("value"),
                sensor_data.get("accuracy"),
                sensor_data.get("status"),
                self.session_id,
            ),
        )

        conn.commit()
        conn.close()

    def log_event(
        self, event_type: str, severity: str, description: str
    ) -> None:
        """Log a monitoring event (alert, warning, error, etc.)."""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO events
            (vehicle_id, timestamp, event_type, severity, description, session_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                self.vehicle_id,
                datetime.now(),
                event_type,
                severity,
                description,
                self.session_id,
            ),
        )

        conn.commit()
        conn.close()

    def get_telemetry_history(
        self, limit: int = 100, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieve telemetry history."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM telemetry WHERE vehicle_id = ?"
        params = [self.vehicle_id]

        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def get_events(
        self,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Retrieve logged events with optional filtering."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        query = "SELECT * FROM events WHERE vehicle_id = ?"
        params = [self.vehicle_id]

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        if severity:
            query += " AND severity = ?"
            params.append(severity)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor.execute(query, params)
        rows = cursor.fetchall()
        conn.close()

        return [dict(row) for row in rows]

    def export_session_data(self, output_path: str) -> None:
        """Export all session data to JSON file."""
        data = {
            "vehicle_id": self.vehicle_id,
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "telemetry": self.get_telemetry_history(limit=10000),
            "events": self.get_events(limit=10000),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2, default=str)
