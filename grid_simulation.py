"""Small distribution-grid model used by the dashboard.

The model is intentionally compact so the project can be used as a student
exercise.  Pandapower is used when it is installed; otherwise a simple
voltage/loading approximation keeps the rest of the application usable.
"""

import numpy as np
import pandas as pd

try:
    import pandapower as pp
    PANDAPOWER_AVAILABLE = True
except ImportError:
    pp = None
    PANDAPOWER_AVAILABLE = False


class GridSimulator:
    def __init__(self):
        self.net = None
        if PANDAPOWER_AVAILABLE:
            self._build_network()

    def _build_network(self):
        net = pp.create_empty_network(name="Ayush_Smart_Grid")

        hv = pp.create_bus(net, vn_kv=110.0, name="Grid 110kV")
        mv0 = pp.create_bus(net, vn_kv=11.0, name="Substation 11kV")
        ind = pp.create_bus(net, vn_kv=11.0, name="Industrial Feeder")
        com = pp.create_bus(net, vn_kv=11.0, name="Commercial Feeder")
        res = pp.create_bus(net, vn_kv=11.0, name="Residential Feeder")
        lv1 = pp.create_bus(net, vn_kv=0.4, name="Residential LV")
        lv2 = pp.create_bus(net, vn_kv=0.4, name="Commercial LV")

        pp.create_ext_grid(net, bus=hv, vm_pu=1.0, name="Utility Supply")
        pp.create_transformer_from_parameters(
            net, hv, mv0, sn_mva=25.0, vn_hv_kv=110.0, vn_lv_kv=11.0,
            vkr_percent=0.4, vk_percent=12.0, pfe_kw=15.0, i0_percent=0.06,
            name="Main Transformer",
        )
        pp.create_transformer_from_parameters(
            net, res, lv1, sn_mva=0.4, vn_hv_kv=11.0, vn_lv_kv=0.4,
            vkr_percent=1.2, vk_percent=4.0, pfe_kw=0.8, i0_percent=0.25,
            name="Residential Transformer",
        )
        pp.create_transformer_from_parameters(
            net, com, lv2, sn_mva=0.63, vn_hv_kv=11.0, vn_lv_kv=0.4,
            vkr_percent=1.1, vk_percent=4.0, pfe_kw=1.1, i0_percent=0.22,
            name="Commercial Transformer",
        )

        for a, b, length, name in [
            (mv0, ind, 2.0, "Feeder 1"),
            (ind, com, 2.2, "Feeder 2"),
            (com, res, 2.6, "Feeder 3"),
        ]:
            pp.create_line_from_parameters(
                net, a, b, length_km=length,
                r_ohm_per_km=0.12, x_ohm_per_km=0.35,
                c_nf_per_km=210.0, max_i_ka=0.4, name=name,
            )

        pp.create_load(net, ind, p_mw=2.0, q_mvar=0.75, name="Industrial Load")
        pp.create_load(net, com, p_mw=1.35, q_mvar=0.45, name="Commercial Load")
        pp.create_load(net, res, p_mw=1.0, q_mvar=0.30, name="Residential MV Load")
        pp.create_load(net, lv1, p_mw=0.22, q_mvar=0.07, name="Residential LV Load")
        pp.create_load(net, lv2, p_mw=0.38, q_mvar=0.12, name="Commercial LV Load")
        pp.create_sgen(net, res, p_mw=0.65, q_mvar=0.0, name="Rooftop PV")
        self.net = net

    def run_power_flow(self, load_scaling=1.0, solar_generation_mw=0.65):
        if not PANDAPOWER_AVAILABLE or self.net is None:
            return self._fallback(load_scaling, solar_generation_mw)

        self.net.load["scaling"] = float(load_scaling)
        self.net.sgen.loc[0, "p_mw"] = float(solar_generation_mw)

        try:
            pp.runpp(self.net, algorithm="nr", max_iteration=30)
            vm = self.net.res_bus["vm_pu"]
            loading = self.net.res_line["loading_percent"]

            buses = pd.DataFrame({
                "Bus": self.net.bus["name"].values,
                "Voltage (p.u.)": vm.round(4).values,
                "Angle (deg)": self.net.res_bus["va_degree"].round(2).values,
            })
            buses["Status"] = np.where(
                buses["Voltage (p.u.)"].between(0.95, 1.05), "NORMAL", "CHECK"
            )

            lines = pd.DataFrame({
                "Line": self.net.line["name"].values,
                "Loading (%)": loading.round(2).values,
                "Current (kA)": self.net.res_line["i_ka"].round(4).values,
            })
            lines["Status"] = np.where(lines["Loading (%)"] <= 90.0, "NORMAL", "HIGH")

            return {
                "success": True,
                "buses": buses,
                "lines": lines,
                "total_load_mw": round(float(self.net.res_load["p_mw"].sum()), 3),
                "solar_gen_mw": float(solar_generation_mw),
                "total_loss_kw": round(float((self.net.res_line["pl_mw"].sum() + self.net.res_trafo["pl_mw"].sum()) * 1000), 2),
                "min_voltage_pu": round(float(vm.min()), 4),
                "max_line_loading_pct": round(float(loading.max()), 2),
            }
        except Exception as exc:
            return self._fallback(load_scaling, solar_generation_mw, error=str(exc))

    def _fallback(self, scale, solar, error=None):
        v = np.array([1.0, 0.998, 0.99 - 0.018 * scale, 0.982 - 0.028 * scale,
                      0.976 - 0.036 * scale + 0.012 * solar, 0.965 - 0.04 * scale,
                      0.97 - 0.035 * scale])
        loading = np.array([50.0, 42.0, 36.0]) * scale

        buses = pd.DataFrame({
            "Bus": ["Grid 110kV", "Substation 11kV", "Industrial Feeder",
                    "Commercial Feeder", "Residential Feeder", "Residential LV", "Commercial LV"],
            "Voltage (p.u.)": np.round(v, 4),
            "Angle (deg)": [0.0, -0.8, -1.9, -2.8, -3.7, -4.2, -3.9],
        })
        buses["Status"] = np.where(buses["Voltage (p.u.)"].between(0.95, 1.05), "NORMAL", "CHECK")

        lines = pd.DataFrame({
            "Line": ["Feeder 1", "Feeder 2", "Feeder 3"],
            "Loading (%)": np.round(loading, 1),
            "Current (kA)": np.round(loading / 200.0, 4),
        })
        lines["Status"] = np.where(lines["Loading (%)"] <= 90.0, "NORMAL", "HIGH")

        return {
            "success": True,
            "buses": buses,
            "lines": lines,
            "total_load_mw": round(5.0 * scale, 3),
            "solar_gen_mw": float(solar),
            "total_loss_kw": round(36.0 * scale ** 2, 2),
            "min_voltage_pu": round(float(v.min()), 4),
            "max_line_loading_pct": round(float(loading.max()), 1),
            "fallback_reason": error or "pandapower not installed",
        }


if __name__ == "__main__":
    result = GridSimulator().run_power_flow(load_scaling=1.1)
    print(result["buses"])
    print(result["lines"])
