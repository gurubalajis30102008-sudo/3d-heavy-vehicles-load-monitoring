"""
Vehicle Model Module

Defines the 3D vehicle structure, geometry, and properties.
Handles vehicle configuration and component management.
"""

import numpy as np
from dataclasses import dataclass
from typing import List, Dict, Tuple
from enum import Enum


class VehicleType(Enum):
    """Enum for different vehicle types."""
    TRUCK = "truck"
    TANKER = "tanker"
    FLATBED = "flatbed"
    CONTAINER = "container"
    DUMP_TRUCK = "dump_truck"


@dataclass
class Axle:
    """Represents a vehicle axle with load capacity."""
    id: int
    position: Tuple[float, float, float]  # (x, y, z) coordinates
    max_load: float  # kg
    wheel_count: int
    current_load: float = 0.0
    load_history: List[float] = None

    def __post_init__(self):
        if self.load_history is None:
            self.load_history = []

    def add_load(self, weight: float) -> bool:
        """Add load to axle, return True if within capacity."""
        if self.current_load + weight <= self.max_load:
            self.current_load += weight
            self.load_history.append(self.current_load)
            return True
        return False

    def get_load_percentage(self) -> float:
        """Get load as percentage of max capacity."""
        return (self.current_load / self.max_load) * 100 if self.max_load > 0 else 0


@dataclass
class CargoCompartment:
    """Represents a cargo storage area."""
    id: int
    name: str
    position: Tuple[float, float, float]
    dimensions: Tuple[float, float, float]  # length, width, height in meters
    max_capacity: float  # kg
    current_load: float = 0.0
    load_distribution: Dict[str, float] = None

    def __post_init__(self):
        if self.load_distribution is None:
            self.load_distribution = {}

    def get_volume(self) -> float:
        """Calculate cargo compartment volume in cubic meters."""
        return self.dimensions[0] * self.dimensions[1] * self.dimensions[2]

    def get_load_percentage(self) -> float:
        """Get load as percentage of max capacity."""
        return (self.current_load / self.max_capacity) * 100 if self.max_capacity > 0 else 0


class VehicleModel:
    """
    Main vehicle model class representing the 3D structure and properties
    of a heavy vehicle.
    """

    def __init__(
        self,
        vehicle_id: str,
        vehicle_type: VehicleType,
        length: float,
        width: float,
        height: float,
        tare_weight: float,
        max_gross_weight: float,
    ):
        """
        Initialize a vehicle model.

        Args:
            vehicle_id: Unique identifier for the vehicle
            vehicle_type: Type of vehicle (truck, tanker, etc.)
            length: Vehicle length in meters
            width: Vehicle width in meters
            height: Vehicle height in meters
            tare_weight: Empty vehicle weight in kg
            max_gross_weight: Maximum allowed total weight in kg
        """
        self.vehicle_id = vehicle_id
        self.vehicle_type = vehicle_type
        self.dimensions = (length, width, height)
        self.tare_weight = tare_weight
        self.max_gross_weight = max_gross_weight
        self.max_payload = max_gross_weight - tare_weight

        self.axles: List[Axle] = []
        self.cargo_compartments: List[CargoCompartment] = []
        self.position = np.array([0.0, 0.0, 0.0])
        self.rotation = np.array([0.0, 0.0, 0.0])  # Euler angles in degrees
        self.velocity = np.array([0.0, 0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0, 0.0])

    def add_axle(
        self,
        axle_id: int,
        position: Tuple[float, float, float],
        max_load: float,
        wheel_count: int,
    ) -> Axle:
        """Add an axle to the vehicle."""
        axle = Axle(
            id=axle_id,
            position=position,
            max_load=max_load,
            wheel_count=wheel_count,
        )
        self.axles.append(axle)
        return axle

    def add_cargo_compartment(
        self,
        compartment_id: int,
        name: str,
        position: Tuple[float, float, float],
        dimensions: Tuple[float, float, float],
        max_capacity: float,
    ) -> CargoCompartment:
        """Add a cargo compartment to the vehicle."""
        compartment = CargoCompartment(
            id=compartment_id,
            name=name,
            position=position,
            dimensions=dimensions,
            max_capacity=max_capacity,
        )
        self.cargo_compartments.append(compartment)
        return compartment

    def get_total_current_load(self) -> float:
        """Calculate total current load from all axles and compartments."""
        axle_load = sum(axle.current_load for axle in self.axles)
        cargo_load = sum(compartment.current_load for compartment in self.cargo_compartments)
        return axle_load + cargo_load

    def get_gross_weight(self) -> float:
        """Get total vehicle weight (tare + cargo)."""
        return self.tare_weight + self.get_total_current_load()

    def get_load_balance_ratio(self) -> float:
        """Calculate load balance ratio (0 = perfectly balanced, >0 = imbalanced)."""
        if not self.axles:
            return 0.0

        loads = [axle.current_load for axle in self.axles]
        mean_load = np.mean(loads)
        variance = np.var(loads)
        return variance / (mean_load ** 2) if mean_load > 0 else 0.0

    def is_overloaded(self) -> bool:
        """Check if vehicle exceeds maximum gross weight."""
        return self.get_gross_weight() > self.max_gross_weight

    def get_payload_utilization(self) -> float:
        """Get payload utilization percentage."""
        current_payload = self.get_total_current_load()
        return (current_payload / self.max_payload) * 100 if self.max_payload > 0 else 0

    def update_position(self, delta_time: float) -> None:
        """Update vehicle position based on velocity."""
        self.position += self.velocity * delta_time

    def update_velocity(self, delta_time: float) -> None:
        """Update vehicle velocity based on acceleration."""
        self.velocity += self.acceleration * delta_time

    def get_info(self) -> Dict:
        """Get comprehensive vehicle information."""
        return {
            "vehicle_id": self.vehicle_id,
            "type": self.vehicle_type.value,
            "dimensions": self.dimensions,
            "tare_weight": self.tare_weight,
            "max_gross_weight": self.max_gross_weight,
            "current_gross_weight": self.get_gross_weight(),
            "total_load": self.get_total_current_load(),
            "payload_utilization": self.get_payload_utilization(),
            "load_balance_ratio": self.get_load_balance_ratio(),
            "is_overloaded": self.is_overloaded(),
            "position": self.position.tolist(),
            "rotation": self.rotation.tolist(),
            "velocity": self.velocity.tolist(),
            "num_axles": len(self.axles),
            "num_compartments": len(self.cargo_compartments),
        }
