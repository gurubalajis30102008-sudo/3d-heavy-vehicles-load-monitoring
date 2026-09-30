"""
Load Simulator Module

Simulates realistic load scenarios for testing and demonstration.
Generates dynamic load patterns across axles and compartments.
"""

import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta

from src.core.vehicle_model import VehicleModel, VehicleType
from src.core.sensor_system import SensorSystem, Sensor, SensorType


class LoadProfile(Enum):
    """Predefined load scenarios."""
    EMPTY = "empty"
    PARTIAL_LOAD = "partial_load"
    FULL_LOAD = "full_load"
    OVERLOAD = "overload"
    UNBALANCED = "unbalanced"
    DYNAMIC = "dynamic"
    ACCELERATION = "acceleration"
    CORNERING = "cornering"


@dataclass
class LoadEvent:
    """Represents a load change event."""
    timestamp: datetime
    event_type: str  # 'load', 'unload', 'shift'
    axle_id: Optional[int]
    compartment_id: Optional[int]
    weight_change: float
    description: str


class LoadSimulator:
    """
    Simulates realistic load scenarios for vehicles.
    """

    def __init__(self, vehicle: VehicleModel, sensor_system: SensorSystem):
        """
        Initialize the load simulator.

        Args:
            vehicle: Vehicle model to simulate
            sensor_system: Associated sensor system
        """
        self.vehicle = vehicle
        self.sensor_system = sensor_system
        self.events: List[LoadEvent] = []
        self.current_time = datetime.now()
        self.simulation_speed = 1.0  # Real-time multiplier

    def apply_load_profile(
        self, profile: LoadProfile, distribution: str = "balanced"
    ) -> None:
        """
        Apply a predefined load profile to the vehicle.

        Args:
            profile: Type of load profile to apply
            distribution: How to distribute load ('balanced', 'front', 'rear', 'random')
        """
        if profile == LoadProfile.EMPTY:
            self._clear_all_loads()
        elif profile == LoadProfile.PARTIAL_LOAD:
            self._apply_partial_load(distribution)
        elif profile == LoadProfile.FULL_LOAD:
            self._apply_full_load(distribution)
        elif profile == LoadProfile.OVERLOAD:
            self._apply_overload(distribution)
        elif profile == LoadProfile.UNBALANCED:
            self._apply_unbalanced_load()
        elif profile == LoadProfile.DYNAMIC:
            self._start_dynamic_load_simulation()

    def _clear_all_loads(self) -> None:
        """Remove all loads from vehicle."""
        for axle in self.vehicle.axles:
            axle.current_load = 0.0
        for compartment in self.vehicle.cargo_compartments:
            compartment.current_load = 0.0
        self._log_event(
            "load",
            None,
            None,
            -self.vehicle.get_total_current_load(),
            "Cleared all loads",
        )

    def _apply_partial_load(self, distribution: str = "balanced") -> None:
        """Apply 50% of payload capacity."""
        target_load = self.vehicle.max_payload * 0.5
        self._distribute_load(target_load, distribution)

    def _apply_full_load(self, distribution: str = "balanced") -> None:
        """Apply 100% of payload capacity."""
        target_load = self.vehicle.max_payload
        self._distribute_load(target_load, distribution)

    def _apply_overload(self, distribution: str = "balanced") -> None:
        """Apply 120% of payload capacity."""
        target_load = self.vehicle.max_payload * 1.2
        self._distribute_load(target_load, distribution)

    def _apply_unbalanced_load(self) -> None:
        """Apply load with poor weight distribution."""
        if not self.vehicle.axles:
            return
        total_load = self.vehicle.max_payload * 0.8
        # Put 70% on first axle, 30% on others
        self.vehicle.axles[0].current_load = total_load * 0.7
        remaining = total_load * 0.3
        for axle in self.vehicle.axles[1:]:
            load = remaining / (len(self.vehicle.axles) - 1)
            axle.current_load = load
        self._log_event(
            "load",
            None,
            None,
            total_load,
            "Applied unbalanced load profile",
        )

    def _distribute_load(
        self, target_load: float, distribution: str = "balanced"
    ) -> None:
        """Distribute load across axles based on distribution method."""
        if distribution == "balanced":
            self._balanced_distribution(target_load)
        elif distribution == "front":
            self._front_heavy_distribution(target_load)
        elif distribution == "rear":
            self._rear_heavy_distribution(target_load)
        elif distribution == "random":
            self._random_distribution(target_load)

    def _balanced_distribution(self, target_load: float) -> None:
        """Distribute load evenly across axles."""
        if not self.vehicle.axles:
            return
        load_per_axle = target_load / len(self.vehicle.axles)
        for axle in self.vehicle.axles:
            axle.current_load = min(load_per_axle, axle.max_load)
        self._log_event(
            "load", None, None, target_load, "Applied balanced load distribution"
        )

    def _front_heavy_distribution(self, target_load: float) -> None:
        """Distribute load towards front axles."""
        if not self.vehicle.axles:
            return
        front_count = (len(self.vehicle.axles) + 1) // 2
        front_load = target_load * 0.6 / front_count
        rear_load = target_load * 0.4 / (len(self.vehicle.axles) - front_count)

        for i, axle in enumerate(self.vehicle.axles):
            if i < front_count:
                axle.current_load = min(front_load, axle.max_load)
            else:
                axle.current_load = min(rear_load, axle.max_load)
        self._log_event(
            "load", None, None, target_load, "Applied front-heavy load distribution"
        )

    def _rear_heavy_distribution(self, target_load: float) -> None:
        """Distribute load towards rear axles."""
        if not self.vehicle.axles:
            return
        rear_count = (len(self.vehicle.axles) + 1) // 2
        rear_load = target_load * 0.6 / rear_count
        front_load = target_load * 0.4 / (len(self.vehicle.axles) - rear_count)

        for i, axle in enumerate(self.vehicle.axles):
            if i >= len(self.vehicle.axles) - rear_count:
                axle.current_load = min(rear_load, axle.max_load)
            else:
                axle.current_load = min(front_load, axle.max_load)
        self._log_event(
            "load", None, None, target_load, "Applied rear-heavy load distribution"
        )

    def _random_distribution(self, target_load: float) -> None:
        """Distribute load randomly across axles."""
        if not self.vehicle.axles:
            return
        weights = np.random.rand(len(self.vehicle.axles))
        weights = weights / weights.sum() * target_load

        for axle, weight in zip(self.vehicle.axles, weights):
            axle.current_load = min(weight, axle.max_load)
        self._log_event(
            "load", None, None, target_load, "Applied random load distribution"
        )

    def _start_dynamic_load_simulation(self) -> None:
        """Start dynamic load simulation (to be called in update loop)."""
        self._log_event(
            "load", None, None, 0, "Started dynamic load simulation"
        )

    def update(self, delta_time: float) -> None:
        """Update simulation state."""
        self.current_time += timedelta(seconds=delta_time * self.simulation_speed)

    def generate_sensor_readings(self) -> Dict[str, float]:
        """Generate sensor readings based on current load state."""
        readings = {}
        load_sensors = self.sensor_system.get_sensors_by_type(SensorType.LOAD_CELL)

        for sensor in load_sensors:
            if "axle" in sensor.location:
                axle_id = int(sensor.location.split("_")[-1])
                if axle_id < len(self.vehicle.axles):
                    actual_value = self.vehicle.axles[axle_id].current_load
                    reading = sensor.generate_reading(actual_value)
                    readings[sensor.sensor_id] = reading.processed_value

        return readings

    def _log_event(
        self,
        event_type: str,
        axle_id: Optional[int],
        compartment_id: Optional[int],
        weight_change: float,
        description: str,
    ) -> None:
        """Log a load event."""
        event = LoadEvent(
            timestamp=self.current_time,
            event_type=event_type,
            axle_id=axle_id,
            compartment_id=compartment_id,
            weight_change=weight_change,
            description=description,
        )
        self.events.append(event)

    def get_event_history(self) -> List[Dict]:
        """Get event history as list of dictionaries."""
        return [
            {
                "timestamp": event.timestamp.isoformat(),
                "type": event.event_type,
                "axle_id": event.axle_id,
                "compartment_id": event.compartment_id,
                "weight_change": event.weight_change,
                "description": event.description,
            }
            for event in self.events
        ]
