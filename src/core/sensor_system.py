"""
Sensor System Module

Defines sensors for monitoring vehicle loads, dynamics, and environmental conditions.
Simulates real sensor data with noise and accuracy parameters.
"""

import numpy as np
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum
from datetime import datetime


class SensorType(Enum):
    """Enum for different sensor types."""
    LOAD_CELL = "load_cell"
    ACCELEROMETER = "accelerometer"
    GYROSCOPE = "gyroscope"
    GPS = "gps"
    TEMPERATURE = "temperature"
    PRESSURE = "pressure"
    TILT = "tilt"


class SensorStatus(Enum):
    """Enum for sensor operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"
    CALIBRATING = "calibrating"


@dataclass
class SensorReading:
    """Represents a single sensor reading."""
    timestamp: datetime
    sensor_id: str
    sensor_type: SensorType
    raw_value: float
    processed_value: float
    status: SensorStatus
    accuracy: float  # 0-100%
    unit: str

    def to_dict(self) -> Dict:
        """Convert reading to dictionary."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "sensor_id": self.sensor_id,
            "sensor_type": self.sensor_type.value,
            "raw_value": self.raw_value,
            "processed_value": self.processed_value,
            "status": self.status.value,
            "accuracy": self.accuracy,
            "unit": self.unit,
        }


class Sensor:
    """
    Base sensor class for all vehicle sensors.
    """

    def __init__(
        self,
        sensor_id: str,
        sensor_type: SensorType,
        location: str,
        accuracy: float = 95.0,
        noise_level: float = 0.5,
    ):
        """
        Initialize a sensor.

        Args:
            sensor_id: Unique identifier for the sensor
            sensor_type: Type of sensor
            location: Physical location on vehicle
            accuracy: Sensor accuracy percentage (0-100)
            noise_level: Sensor noise standard deviation
        """
        self.sensor_id = sensor_id
        self.sensor_type = sensor_type
        self.location = location
        self.accuracy = accuracy
        self.noise_level = noise_level
        self.status = SensorStatus.INACTIVE
        self.readings: List[SensorReading] = []
        self.calibration_offset = 0.0
        self.last_reading_time = None

    def activate(self) -> None:
        """Activate the sensor."""
        self.status = SensorStatus.ACTIVE

    def deactivate(self) -> None:
        """Deactivate the sensor."""
        self.status = SensorStatus.INACTIVE

    def calibrate(self, reference_value: float) -> None:
        """Calibrate sensor with reference value."""
        if self.readings:
            last_raw = self.readings[-1].raw_value
            self.calibration_offset = reference_value - last_raw
            self.status = SensorStatus.ACTIVE

    def generate_reading(self, actual_value: float) -> SensorReading:
        """Generate a sensor reading with realistic noise and accuracy."""
        noise = np.random.normal(0, self.noise_level)
        raw_value = actual_value + noise
        processed_value = raw_value + self.calibration_offset
        accuracy_factor = self.accuracy / 100.0

        reading = SensorReading(
            timestamp=datetime.now(),
            sensor_id=self.sensor_id,
            sensor_type=self.sensor_type,
            raw_value=raw_value,
            processed_value=processed_value,
            status=self.status,
            accuracy=self.accuracy * accuracy_factor,
            unit=self._get_unit(),
        )
        self.readings.append(reading)
        self.last_reading_time = reading.timestamp
        return reading

    def _get_unit(self) -> str:
        """Get unit of measurement for this sensor type."""
        units = {
            SensorType.LOAD_CELL: "kg",
            SensorType.ACCELEROMETER: "m/s²",
            SensorType.GYROSCOPE: "deg/s",
            SensorType.GPS: "m",
            SensorType.TEMPERATURE: "°C",
            SensorType.PRESSURE: "Pa",
            SensorType.TILT: "degrees",
        }
        return units.get(self.sensor_type, "unknown")

    def get_latest_reading(self) -> Optional[SensorReading]:
        """Get the most recent sensor reading."""
        return self.readings[-1] if self.readings else None

    def get_average_reading(self, count: int = 10) -> float:
        """Get average of last N readings."""
        if not self.readings:
            return 0.0
        recent_readings = self.readings[-count:]
        return np.mean([r.processed_value for r in recent_readings])

    def clear_readings(self) -> None:
        """Clear all stored readings."""
        self.readings.clear()


class SensorSystem:
    """
    Manages all sensors on a vehicle.
    """

    def __init__(self, vehicle_id: str):
        """
        Initialize the sensor system.

        Args:
            vehicle_id: Vehicle identifier this sensor system belongs to
        """
        self.vehicle_id = vehicle_id
        self.sensors: Dict[str, Sensor] = {}
        self.is_active = False

    def add_sensor(self, sensor: Sensor) -> None:
        """Add a sensor to the system."""
        self.sensors[sensor.sensor_id] = sensor

    def activate_all(self) -> None:
        """Activate all sensors."""
        for sensor in self.sensors.values():
            sensor.activate()
        self.is_active = True

    def deactivate_all(self) -> None:
        """Deactivate all sensors."""
        for sensor in self.sensors.values():
            sensor.deactivate()
        self.is_active = False

    def get_sensor(self, sensor_id: str) -> Optional[Sensor]:
        """Get a specific sensor by ID."""
        return self.sensors.get(sensor_id)

    def get_sensors_by_type(self, sensor_type: SensorType) -> List[Sensor]:
        """Get all sensors of a specific type."""
        return [s for s in self.sensors.values() if s.sensor_type == sensor_type]

    def get_all_readings(self) -> Dict[str, List[Dict]]:
        """Get all readings from all sensors."""
        readings = {}
        for sensor_id, sensor in self.sensors.items():
            readings[sensor_id] = [r.to_dict() for r in sensor.readings]
        return readings

    def get_active_sensors(self) -> List[Sensor]:
        """Get all active sensors."""
        return [s for s in self.sensors.values() if s.status == SensorStatus.ACTIVE]

    def calibrate_all(self, reference_values: Dict[str, float]) -> None:
        """Calibrate all sensors with reference values."""
        for sensor_id, ref_value in reference_values.items():
            if sensor_id in self.sensors:
                self.sensors[sensor_id].calibrate(ref_value)

    def get_health_report(self) -> Dict:
        """Get health status report for all sensors."""
        total_sensors = len(self.sensors)
        active_sensors = len(self.get_active_sensors())
        error_sensors = len(
            [s for s in self.sensors.values() if s.status == SensorStatus.ERROR]
        )

        return {
            "vehicle_id": self.vehicle_id,
            "total_sensors": total_sensors,
            "active_sensors": active_sensors,
            "inactive_sensors": total_sensors - active_sensors - error_sensors,
            "error_sensors": error_sensors,
            "system_status": "OK" if error_sensors == 0 else "WARNING",
            "availability": (active_sensors / total_sensors * 100) if total_sensors > 0 else 0,
        }
