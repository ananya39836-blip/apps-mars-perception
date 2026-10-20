"""Level 6 Part 39: Lunar South Pole Infrastructure & Megawatt Cryo-Grids.
Chapters 480 to 489: PSR Ice Excavation, Fission Micro-Grids & Thermal Wadis.

Implements autonomous cryogenic mining in 40 K permanently shadowed regions (PSR),
megawatt Stirling fission micro-grid dispatch, and thermal wadi night energy storage.
"""
import math
from typing import Dict, Any, List, Optional
import numpy as np

PROTOTYPE_LOCK: bool = True
NAVIGATION_READY: bool = False


class PSRIceHarvester:
    """Models cryogenic regolith water ice excavation in 40 K permanently shadowed craters."""

    def __init__(self, auger_diameter_m: float = 0.45, rated_power_kw: float = 6.5):
        self.auger_diameter_m = auger_diameter_m
        self.power_kw = rated_power_kw
        self.accumulated_ice_kg = 0.0

    def mine_psr_sector(self, depth_m: float, duration_hours: float, ice_weight_pct: float = 8.5) -> Dict[str, Any]:
        """Calculates cryogenic ice mass yield under extreme low-temperature shear resistance."""
        # 40 K regolith is hard as granite: cutting rate ~ 0.4 m^3/hr per kW
        vol_excavated_m3 = (self.power_kw / 5.0) * 0.35 * duration_hours
        density_cryo_regolith = 1850.0  # kg/m^3
        total_mass_kg = vol_excavated_m3 * density_cryo_regolith
        ice_yield_kg = total_mass_kg * (ice_weight_pct / 100.0) * 0.92  # 92% recovery efficiency

        self.accumulated_ice_kg += ice_yield_kg

        return {
            "duration_hours": duration_hours,
            "excavated_volume_m3": round(vol_excavated_m3, 3),
            "ice_extracted_kg": round(ice_yield_kg, 2),
            "accumulated_ice_total_kg": round(self.accumulated_ice_kg, 2),
            "psr_ambient_temp_k": 40.0,
            "shear_resistance_mpa": 4.2,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class MegawattFissionMicrogrid:
    """Dispatches 1.2 MW thermal Stirling fission power and manages 10 kV HVDC distribution."""

    def __init__(self, reactor_thermal_mw: float = 1.2, stirlings_count: int = 4):
        self.reactor_thermal_mw = reactor_thermal_mw
        self.stirlings_count = stirlings_count
        self.efficiency = 0.32  # 32% thermal-to-electric efficiency
        self.electric_capacity_kw = self.reactor_thermal_mw * 1000.0 * self.efficiency

    def dispatch_power(self, loads_kw: Dict[str, float]) -> Dict[str, Any]:
        """Dispatches power across mining, habitat, life support, and sintering loads."""
        total_demand = sum(loads_kw.values())
        grid_stable = total_demand <= self.electric_capacity_kw
        reserve_margin_pct = ((self.electric_capacity_kw - total_demand) / self.electric_capacity_kw) * 100.0

        return {
            "electric_capacity_kw": self.electric_capacity_kw,
            "total_demand_kw": round(total_demand, 2),
            "grid_stable": grid_stable,
            "reserve_margin_pct": round(reserve_margin_pct, 1),
            "hvdc_bus_voltage_kv": 10.0,
            "stirling_units_active": self.stirlings_count,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }


class ThermalWadiReservoir:
    """Models concentrated solar / nuclear thermal storage in sintered basalt wadis."""

    def __init__(self, mass_tons: float = 80.0, core_temp_c: float = 650.0):
        self.mass_kg = mass_tons * 1000.0
        self.core_temp_c = core_temp_c
        self.specific_heat = 850.0  # J/kg*K

    def compute_night_thermal_reserve(self, elapsed_lunar_night_hours: float) -> Dict[str, Any]:
        """Calculates available thermal wattage buffering rover survival across 354 hr night."""
        # Exponential heat loss model into space
        decay_rate = 0.0018  # 1/hr
        current_temp_c = 40.0 + (self.core_temp_c - 40.0) * math.exp(-decay_rate * elapsed_lunar_night_hours)
        available_energy_kwh = (self.mass_kg * self.specific_heat * (current_temp_c - 20.0)) / 3.6e6

        return {
            "elapsed_night_hours": elapsed_lunar_night_hours,
            "current_core_temp_c": round(current_temp_c, 1),
            "available_thermal_energy_kwh": round(available_energy_kwh, 2),
            "sufficient_for_survival": current_temp_c >= 120.0,
            "prototype_lock": PROTOTYPE_LOCK,
            "navigation_ready": NAVIGATION_READY
        }
