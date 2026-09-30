"""
Main Entry Point

Initializes the 3D Heavy Vehicles Load Monitoring System and starts the simulation.
"""

import sys
from src.core.vehicle_model import VehicleModel, VehicleType
from src.core.sensor_system import SensorSystem, Sensor, SensorType
from src.simulation.load_simulator import LoadSimulator, LoadProfile
from src.data.logger import DataLogger


def setup_vehicle() -> VehicleModel:
    """
    Set up a sample heavy truck vehicle with axles and compartments.
    """
    vehicle = VehicleModel(
        vehicle_id="TRUCK_001",
        vehicle_type=VehicleType.TRUCK,
        length=12.0,
        width=2.5,
        height=3.5,
        tare_weight=8000,  # kg
        max_gross_weight=25000,  # kg
    )

    # Add axles
    vehicle.add_axle(
        axle_id=1,
        position=(1.0, 0.0, 0.5),
        max_load=6000,  # kg per axle
        wheel_count=2,
    )
    vehicle.add_axle(
        axle_id=2,
        position=(4.0, 0.0, 0.5),
        max_load=8000,
        wheel_count=4,
    )
    vehicle.add_axle(
        axle_id=3,
        position=(7.0, 0.0, 0.5),
        max_load=8000,
        wheel_count=4,
    )

    # Add cargo compartment
    vehicle.add_cargo_compartment(
        compartment_id=1,
        name="Main Cargo Bay",
        position=(4.0, 0.0, 2.0),
        dimensions=(8.0, 2.4, 2.0),
        max_capacity=17000,  # kg
    )

    return vehicle


def setup_sensors(vehicle: VehicleModel) -> SensorSystem:
    """
    Set up sensor system with load cells on axles.
    """
    sensor_system = SensorSystem(vehicle_id=vehicle.vehicle_id)

    # Add load sensors for each axle
    for i, axle in enumerate(vehicle.axles):
        sensor = Sensor(
            sensor_id=f"LOAD_CELL_AXLE_{i+1}",
            sensor_type=SensorType.LOAD_CELL,
            location=f"axle_{i+1}",
            accuracy=98.0,
            noise_level=10.0,  # kg
        )
        sensor.activate()
        sensor_system.add_sensor(sensor)

    # Add accelerometer
    accel_sensor = Sensor(
        sensor_id="ACCELEROMETER_01",
        sensor_type=SensorType.ACCELEROMETER,
        location="center",
        accuracy=95.0,
        noise_level=0.1,
    )
    accel_sensor.activate()
    sensor_system.add_sensor(accel_sensor)

    return sensor_system


def main():
    """
    Main simulation loop.
    """
    print("="* 60)
    print("3D Heavy Vehicles - Load Monitoring System Simulation")
    print("="* 60)
    print()

    # Setup vehicle and sensors
    print("[1/4] Setting up vehicle...")
    vehicle = setup_vehicle()
    print(f"    ✓ Vehicle '{vehicle.vehicle_id}' created")
    print(f"      Type: {vehicle.vehicle_type.value}")
    print(f"      Dimensions: {vehicle.dimensions[0]}m x {vehicle.dimensions[1]}m x {vehicle.dimensions[2]}m")
    print(f"      Max Gross Weight: {vehicle.max_gross_weight} kg")
    print(f"      Number of Axles: {len(vehicle.axles)}")
    print()

    # Setup sensors
    print("[2/4] Setting up sensor system...")
    sensor_system = setup_sensors(vehicle)
    print(f"    ✓ Sensor system initialized")
    print(f"      Total Sensors: {len(sensor_system.sensors)}")
    sensor_health = sensor_system.get_health_report()
    print(f"      Active Sensors: {sensor_health['active_sensors']}")
    print()

    # Setup logger
    print("[3/4] Initializing data logger...")
    logger = DataLogger(vehicle_id=vehicle.vehicle_id)
    print(f"    ✓ Data logger initialized")
    print(f"      Session ID: {logger.session_id}")
    print()

    # Setup simulator
    print("[4/4] Initializing load simulator...")
    simulator = LoadSimulator(vehicle, sensor_system)
    print(f"    ✓ Load simulator ready")
    print()

    # Run simulation scenarios
    print("="* 60)
    print("Running Simulation Scenarios")
    print("="* 60)
    print()

    scenarios = [
        (LoadProfile.EMPTY, "balanced", "Empty Vehicle"),
        (LoadProfile.PARTIAL_LOAD, "balanced", "Partial Load (50%)"),
        (LoadProfile.FULL_LOAD, "balanced", "Full Load (100%)"),
        (LoadProfile.UNBALANCED, "random", "Unbalanced Load"),
    ]

    for profile, distribution, description in scenarios:
        print(f"Scenario: {description}")
        print("-" * 40)

        # Apply load profile
        simulator.apply_load_profile(profile, distribution)

        # Generate sensor readings
        readings = simulator.generate_sensor_readings()

        # Log telemetry
        telemetry = {
            "gross_weight": vehicle.get_gross_weight(),
            "payload": vehicle.get_total_current_load(),
            "load_balance": vehicle.get_load_balance_ratio(),
            "payload_utilization": vehicle.get_payload_utilization(),
            "is_overloaded": vehicle.is_overloaded(),
        }
        logger.log_telemetry(telemetry)

        # Log axle loads
        axle_data = [
            {"id": axle.id, "current_load": axle.current_load, "load_percentage": axle.get_load_percentage()}
            for axle in vehicle.axles
        ]
        logger.log_axle_loads(axle_data)

        # Display results
        print(f"  Gross Weight: {telemetry['gross_weight']:.2f} kg")
        print(f"  Payload: {telemetry['payload']:.2f} kg")
        print(f"  Payload Utilization: {telemetry['payload_utilization']:.2f}%")
        print(f"  Load Balance Ratio: {telemetry['load_balance']:.4f}")
        print(f"  Status: {'⚠️  OVERLOADED' if telemetry['is_overloaded'] else '✓ OK'}")

        print("  Axle Loads:")
        for axle in vehicle.axles:
            print(f"    - Axle {axle.id}: {axle.current_load:.2f} kg ({axle.get_load_percentage():.1f}%)")
        print()

    # Display summary
    print("="* 60)
    print("Simulation Summary")
    print("="* 60)
    print(f"Vehicle: {vehicle.vehicle_id}")
    print(f"Session: {logger.session_id}")
    print(f"Total Telemetry Records: {len(logger.get_telemetry_history(limit=10000))}")
    print(f"Sensor Health Status: {sensor_health['system_status']}")
    print(f"Sensor Availability: {sensor_health['availability']:.1f}%")
    print()
    print("✓ Simulation completed successfully!")
    print()


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Error during simulation: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
