from typing import Tuple, Optional, Dict, Any
import time
import math
import csv
import os
from threading import Lock

"""
dose_accumulator.py

DoseAccumulator: a simple voxelized exposure accumulator for per-location dose tracking.
Designed to be called once-per-loop tick from your live loop. Logs to CSV for debugging.

Dose is computed from gas flow (CFM, treated as constant) normalized by spot area and assumed wound depth.

Usage:
    da = DoseAccumulator(voxel_mm=3.0, half_life_s=None, limits={'per_voxel': 100.0, 'neighborhood_radius_mm': 6.0})
    out = da.update(pose_xyz=(x,y,z), power_pct=50, standoff_mm=50, speed_mm_s=10, dt_s=0.2)
    decision = da.recommend(state, thermal_pred)
"""


class DoseAccumulator:
    def __init__(
        self,
        voxel_mm: float = 3.0,
        half_life_s: Optional[float] = None,
        limits: Optional[Dict[str, float]] = None,
        k: float = 1.0,
        log_path: str = "dose_accumulator_log.csv",
        default_flow_cfm: float = 20.0,
        spot_diam_mm: float = 10.0,
        depth_mm: float = 0.5,
        coupling_eff: float = 1e-6,
    ):
        """
        voxel_mm: voxel edge size in mm
        half_life_s: if provided, accumulated dose decays exponentially with this half-life
        limits: dict with keys:
            - per_voxel: maximum allowed dose for a single voxel
            - neighborhood_radius_mm: radius to check neighbors for max dose
            - neighborhood_max: optional, allowed max for neighborhood (if not present, uses per_voxel)
        k: calibration multiplier (to fit hardware)
        log_path: CSV file path for debug logs
        """
        self.voxel_mm = float(voxel_mm)
        self.half_life_s = half_life_s
        self.k = float(k)
        self.default_flow_cfm = float(default_flow_cfm)
        self.spot_diam_mm = float(spot_diam_mm)
        self.depth_mm = float(depth_mm)
        self.coupling_eff = float(coupling_eff)
        self.limits = limits or {'per_voxel': 100.0, 'neighborhood_radius_mm': 6.0}
        if 'neighborhood_max' not in self.limits:
            self.limits['neighborhood_max'] = self.limits['per_voxel']
        self._grid = {}  # dict[(ix,iy,iz)] -> {'dose': float, 'last_update': timestamp}
        self._lock = Lock()
        self._last_decay_ts = time.time()
        self.log_path = log_path
        self._ensure_log_header()

    # ---------- internal helpers ----------
    def _voxel_index(self, pos: Tuple[float, float, float]) -> Tuple[int, int, int]:
        x, y, z = pos
        return (int(round(x / self.voxel_mm)),
                int(round(y / self.voxel_mm)),
                int(round(z / self.voxel_mm)))

    def _apply_decay(self):
        if self.half_life_s is None:
            return
        now = time.time()
        dt = now - self._last_decay_ts
        if dt <= 0:
            return
        # exponential decay factor
        factor = math.exp(-math.log(2) * dt / self.half_life_s)
        if factor >= 0.999999:  # negligible
            self._last_decay_ts = now
            return
        with self._lock:
            to_delete = []
            for k, v in list(self._grid.items()):
                v['dose'] *= factor
                v['last_update'] = now
                # purge tiny doses
                if v['dose'] < 1e-6:
                    to_delete.append(k)
            for k in to_delete:
                del self._grid[k]
        self._last_decay_ts = now

    def _standoff_factor(self, standoff_mm: float) -> float:
        # simple inverse-square-ish attenuation, clamped
        s = max(float(standoff_mm), 1.0)
        return 1.0 / (s * s)

    def _cfm_to_mm3_s(self, flow_cfm: float) -> float:
        """Convert cubic-feet-per-minute to cubic-millimeters-per-second."""
        # 1 ft^3 = 0.028316846592 m^3, 1 m^3 = 1e9 mm^3
        m3_s = float(flow_cfm) * 0.028316846592 / 60.0
        return m3_s * 1e9

    def _spot_area_mm2(self, spot_diam_mm: float) -> float:
        d = max(float(spot_diam_mm), 0.1)
        r = 0.5 * d
        return math.pi * (r * r)


    def _neighborhood_indices(self, idx: Tuple[int,int,int]) -> Tuple[Tuple[int,int,int], ...]:
        rad_mm = float(self.limits.get('neighborhood_radius_mm', self.voxel_mm))
        r = int(math.ceil(rad_mm / self.voxel_mm))
        ix0, iy0, iz0 = idx
        inds = []
        for dx in range(-r, r+1):
            for dy in range(-r, r+1):
                for dz in range(-r, r+1):
                    inds.append((ix0+dx, iy0+dy, iz0+dz))
        return tuple(inds)

    def _ensure_log_header(self):
        header = ['ts', 'x','y','z', 'voxel_idx', 'dose_added', 'voxel_dose', 'neighborhood_max',
                  'flow_cfm', 'spot_diam_mm', 'depth_mm', 'coupling_eff', 'dose_mode',
                  'power_pct','standoff_mm','speed_mm_s','dt_s','action','reason']
        if not os.path.exists(self.log_path):
            with open(self.log_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(header)

    def _log(self, row: Dict[str, Any]):
        with open(self.log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                row.get('ts', time.time()),
                row.get('x'), row.get('y'), row.get('z'),
                row.get('voxel_idx'),
                row.get('dose_added'),
                row.get('voxel_dose'),
                row.get('neighborhood_max'),
                row.get('flow_cfm'),
                row.get('spot_diam_mm'),
                row.get('depth_mm'),
                row.get('coupling_eff'),
                row.get('dose_mode'),
                row.get('power_pct'),
                row.get('standoff_mm'),
                row.get('speed_mm_s'),
                row.get('dt_s'),
                row.get('action'),
                row.get('reason'),
            ])

    # ---------- public API ----------
    def update(
        self,
        pose_xyz: Tuple[float, float, float],
        power_pct: float,
        standoff_mm: float,
        speed_mm_s: float,
        dt_s: float,
        flow_cfm: Optional[float] = None,
        spot_diam_mm: Optional[float] = None,
        depth_mm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Record dose for this tick and return diagnostics + immediate action suggestion.
        Returns dict:
            dose_added: dimensionless ratio of delivered volume to tissue volume (depends on flow/spot/depth)
            voxel_dose, neighborhood_max, action, reason
        """
        if pose_xyz is None:
            return {'dose_added': 0.0, 'voxel_dose': 0.0, 'neighborhood_max': 0.0,
                    'action': 'continue', 'reason': 'no_pose'}

        self._apply_decay()

        idx = self._voxel_index(pose_xyz)
        speed = float(speed_mm_s)
        power = float(power_pct)
        dt = float(dt_s)

        # --- dose model (flow-normalized ratio) ---
        # We treat "dose" as a dimensionless ratio:
        #   dose_added = (delivered_flow_volume_mm3 * coupling) / (tissue_volume_mm3)
        # where tissue_volume_mm3 = spot_area_mm2 * depth_mm.
        # This makes thresholds easier to reason about across different nozzle sizes.
        eps_speed = 1.0  # mm/s minimum to avoid runaway; tune later
        standoff_f = self._standoff_factor(standoff_mm)

        use_spot_diam_mm = self.spot_diam_mm if spot_diam_mm is None else float(spot_diam_mm)
        use_depth_mm = self.depth_mm if depth_mm is None else float(depth_mm)

        # Flow is a constant (20 CFM by default). Thermal safety is handled by thermal_predictor.
        # We still allow an explicit flow_cfm override for testing, but if not provided, use default.
        use_flow_cfm = self.default_flow_cfm if flow_cfm is None else float(flow_cfm)

        # Convert flow to volume per second (mm^3/s)
        q_mm3_s = self._cfm_to_mm3_s(use_flow_cfm)

        # Tissue volume under the nozzle footprint
        area_mm2 = self._spot_area_mm2(use_spot_diam_mm)
        tissue_vol_mm3 = max(area_mm2 * max(use_depth_mm, 0.01), 1e-6)

        # Delivered volume for this tick, scaled by power, standoff attenuation, motion, and coupling efficiency
        delivered_mm3 = (q_mm3_s * self.coupling_eff) * (power / 100.0) * dt * standoff_f / max(speed, eps_speed)

        # Dimensionless ratio (how much "effective" volume vs tissue volume)
        dose_inc = self.k * (delivered_mm3 / tissue_vol_mm3)
        dose_mode = 'flow_ratio'

        with self._lock:
            cell = self._grid.get(idx)
            if cell is None:
                cell = {'dose': 0.0, 'last_update': time.time()}
                self._grid[idx] = cell
            cell['dose'] += dose_inc
            cell['last_update'] = time.time()

            # neighborhood max
            neigh_inds = self._neighborhood_indices(idx)
            neigh_max = 0.0
            for nidx in neigh_inds:
                v = self._grid.get(nidx)
                if v is not None:
                    if v['dose'] > neigh_max:
                        neigh_max = v['dose']

        # decide action based on thresholds
        per_voxel_limit = float(self.limits.get('per_voxel', 100.0))
        neighborhood_limit = float(self.limits.get('neighborhood_max', per_voxel_limit))
        action = 'continue'
        reason = 'ok'

        if cell['dose'] >= per_voxel_limit:
            action = 'stop'
            reason = 'voxel_limit_exceeded'
        elif neigh_max >= neighborhood_limit:
            action = 'move'
            reason = 'neighborhood_limit_exceeded'
        elif cell['dose'] >= 0.9 * per_voxel_limit:
            action = 'reduce_power'
            reason = 'approaching_voxel_limit'
        elif neigh_max >= 0.9 * neighborhood_limit:
            action = 'slow'
            reason = 'approaching_neighborhood_limit'

        # log for debugging
        self._log({
            'ts': time.time(),
            'x': pose_xyz[0], 'y': pose_xyz[1], 'z': pose_xyz[2],
            'voxel_idx': idx,
            'dose_added': dose_inc,
            'voxel_dose': cell['dose'],
            'neighborhood_max': neigh_max,
            'flow_cfm': use_flow_cfm,
            'spot_diam_mm': use_spot_diam_mm,
            'depth_mm': use_depth_mm,
            'coupling_eff': self.coupling_eff,
            'dose_mode': dose_mode,
            'power_pct': power_pct,
            'standoff_mm': standoff_mm,
            'speed_mm_s': speed_mm_s,
            'dt_s': dt_s,
            'action': action,
            'reason': reason,
        })

        return {
            'dose_added': dose_inc,
            'voxel_dose': cell['dose'],
            'neighborhood_max': neigh_max,
            'action': action,
            'reason': reason,
            'voxel_idx': idx
        }

    def get_dose_at(self, pose_xyz: Tuple[float, float, float]) -> float:
        "Return current accumulated dose at the voxel containing pose_xyz."
        if pose_xyz is None:
            return 0.0
        self._apply_decay()
        idx = self._voxel_index(pose_xyz)
        with self._lock:
            v = self._grid.get(idx)
            return float(v['dose']) if v is not None else 0.0

    def will_exceed(
        self,
        pose_xyz: Tuple[float, float, float],
        projected_dt: float,
        projected_power_pct: float,
        projected_standoff_mm: float,
        projected_speed_mm_s: float,
        projected_flow_cfm: Optional[float] = None,
        projected_spot_diam_mm: Optional[float] = None,
        projected_depth_mm: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Simulate whether continuing for projected_dt would cross thresholds.
        Returns dict:
            projected_voxel_dose, projected_neighborhood_max, will_exceed (bool), reason
        """
        if pose_xyz is None:
            return {'projected_voxel_dose': 0.0, 'projected_neighborhood_max': 0.0,
                    'will_exceed': False, 'reason': 'no_pose'}

        idx = self._voxel_index(pose_xyz)
        with self._lock:
            current = self._grid.get(idx, {'dose': 0.0})
            current_dose = float(current['dose'])

            # compute projected increment with same model (flow-normalized ratio)
            eps_speed = 1.0
            use_spot_diam_mm = self.spot_diam_mm if projected_spot_diam_mm is None else float(projected_spot_diam_mm)
            use_depth_mm = self.depth_mm if projected_depth_mm is None else float(projected_depth_mm)

            # Flow is a constant (20 CFM by default). Thermal safety is handled by thermal_predictor.
            use_flow_cfm = self.default_flow_cfm if projected_flow_cfm is None else float(projected_flow_cfm)

            standoff_f = self._standoff_factor(projected_standoff_mm)
            q_mm3_s = self._cfm_to_mm3_s(use_flow_cfm)
            area_mm2 = self._spot_area_mm2(use_spot_diam_mm)
            tissue_vol_mm3 = max(area_mm2 * max(use_depth_mm, 0.01), 1e-6)

            delivered_mm3 = (q_mm3_s * self.coupling_eff) * (projected_power_pct / 100.0) * projected_dt * standoff_f / max(projected_speed_mm_s, eps_speed)
            dose_inc = self.k * (delivered_mm3 / tissue_vol_mm3)
            proj_voxel = current_dose + dose_inc

            # neighborhood check
            neigh_inds = self._neighborhood_indices(idx)
            neigh_max = 0.0
            for nidx in neigh_inds:
                if nidx == idx:
                    val = proj_voxel
                else:
                    v = self._grid.get(nidx)
                    val = v['dose'] if v is not None else 0.0
                if val > neigh_max:
                    neigh_max = val

        per_voxel_limit = float(self.limits.get('per_voxel', 100.0))
        neighborhood_limit = float(self.limits.get('neighborhood_max', per_voxel_limit))

        will_exceed = (proj_voxel >= per_voxel_limit) or (neigh_max >= neighborhood_limit)
        reason = 'projected_voxel_exceed' if proj_voxel >= per_voxel_limit else ('projected_neighborhood_exceed' if neigh_max >= neighborhood_limit else 'ok')

        return {
            'projected_voxel_dose': proj_voxel,
            'projected_neighborhood_max': neigh_max,
            'will_exceed': bool(will_exceed),
            'reason': reason,
            'dose_inc': dose_inc,
            'flow_cfm': use_flow_cfm,
            'spot_diam_mm': use_spot_diam_mm,
            'depth_mm': use_depth_mm,
        }

    def recommend(
        self,
        state: Dict[str, Any],
        thermal_pred: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        High-level recommendation combining dose and (optional) thermal prediction.
        state is expected to have pose_xyz, power_pct, standoff_mm, speed_mm_s, dt_s (planned tick)
        thermal_pred can be a dict with keys like 'pred_temp' and 'temp_limit'
        Returns dict: action, reason, details
        """
        pose = state.get('pose_xyz')
        power = state.get('power_pct', 0.0)
        standoff = state.get('standoff_mm', 50.0)
        speed = state.get('speed_mm_s', 1.0)
        dt = state.get('dt_s', 0.1)

        proj = self.will_exceed(
            pose_xyz=pose,
            projected_dt=dt,
            projected_power_pct=power,
            projected_standoff_mm=standoff,
            projected_speed_mm_s=speed,
            projected_flow_cfm=state.get('flow_cfm'),
            projected_spot_diam_mm=state.get('spot_diam_mm'),
            projected_depth_mm=state.get('depth_mm'),
        )

        action = 'continue'
        reason = 'ok'
        details = {
            'projected': proj
        }

        if proj['will_exceed']:
            # if thermal pred indicates temp unsafe, prefer stop; otherwise prefer move/reduce
            temp_pred = (thermal_pred or {}).get('pred_temp')
            temp_limit = (thermal_pred or {}).get('temp_limit')
            if temp_pred is not None and temp_limit is not None and temp_pred >= temp_limit:
                action = 'stop'
                reason = 'dose_and_thermal_limit'
            else:
                # dose-only issue: try to move or reduce
                # prefer move if neighborhood high, reduce_power if voxel only near limit
                if proj['projected_neighborhood_max'] >= self.limits.get('neighborhood_max', self.limits['per_voxel']):
                    action = 'move'
                    reason = 'neighborhood_would_exceed'
                elif proj['projected_voxel_dose'] >= self.limits.get('per_voxel'):
                    action = 'stop'
                    reason = 'voxel_would_exceed'
                else:
                    action = 'reduce_power'
                    reason = 'would_approach_limit'
        else:
            # not exceeding; still check approaching thresholds
            pv = proj['projected_voxel_dose']
            nv = proj['projected_neighborhood_max']
            if pv >= 0.9 * self.limits.get('per_voxel', 100.0):
                action = 'reduce_power'
                reason = 'approaching_voxel'
            elif nv >= 0.9 * self.limits.get('neighborhood_max', self.limits.get('per_voxel', 100.0)):
                action = 'slow'
                reason = 'approaching_neighborhood'

        details['dose_now'] = self.get_dose_at(pose)
        return {'action': action, 'reason': reason, 'details': details}

    def export_grid(self) -> Dict[Tuple[int,int,int], float]:
        "Return a shallow copy of the grid doses for inspection or serialization."
        with self._lock:
            return {k: float(v['dose']) for k,v in self._grid.items()}