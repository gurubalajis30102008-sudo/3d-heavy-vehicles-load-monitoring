"""Core module for vehicle models and sensor systems."""

from .vehicle_model import VehicleModel, VehicleType, Axle, CargoCompartment
from .sensor_system import SensorSystem, Sensor, SensorType, SensorStatus, SensorReading

__all__ = [
    "VehicleModel",
    "VehicleType",
    "Axle",
    "CargoCompartment",
    "SensorSystem",
    "Sensor",
    "SensorType",
    "SensorStatus",
    "SensorReading",
]
