"""
Docstring for software.thermal_predictor

predict temperature of tissue 5 seconds into the future (>40°C -> risk of damage -> take necessary precautions)
"""

import argparse
import numpy as np
import os

MODEL_PATH = "software/thermal_model.npz"

class ThermalSafetyAgent:
    def __init__(self, model_path=None, max_temp_c=40.0):
        self.max_temp = max_temp_c
        self.model_path = model_path or MODEL_PATH

        # Weights!
        self.w = None
        self.x_mean = None
        self.x_std = None
        self.y_mean = None
        self.y_std = None

        # load model if exists
        if os.path.exists(self.model_path):
            self.load(self.model_path)

    def _make_feature(self, current_temp, speed_mm_s, power_pct, standoff_mm, tissue_type):
        # feature vector
        return np.array([current_temp, speed_mm_s, power_pct, standoff_mm, tissue_type, 1.0], dtype=float)

    def predict(self, state: dict) -> float:
        x = self._make_feature(
            state["current_temp"],
            state.get("planned_speed", 0.0),
            state.get("plasma_power", 100.0),
            state.get("standoff_mm", 10.0),
            state.get("tissue_type", 0),
        )
        if self.w is None:
            # fallback: naive persistence (no heating)
            return float(state["current_temp"])
        # normalize (use saved mean/std)
        x_norm = (x[:-1] - self.x_mean) / (self.x_std + 1e-8)
        x_with_bias = np.concatenate([x_norm, [1.0]])
        y_norm = x_with_bias.dot(self.w)
        y = y_norm * self.y_std + self.y_mean
        return float(y)

    def recommend_action(self, state: dict):
        pred = self.predict(state)
        if pred > self.max_temp:
            # if we can slow, recommend slow; otherwise stop
            speed = state.get("planned_speed", 0.0)
            if speed > 30.0:
                return {"action": "slow", "reason": f"Predicted T={pred:.2f}C > {self.max_temp}C", "predicted_temp": pred, "recommended_speed_reduction": 0.5}
            else:
                return {"action": "stop", "reason": f"Predicted T={pred:.2f}C unsafe", "predicted_temp": pred}
        return {"action": "safe", "reason": "Within safe envelope", "predicted_temp": pred}

    def train_from_csv(self, csv_path):
        data = np.loadtxt(csv_path, delimiter=",", skiprows=1)
        X = data[:, :5]  # inputs
        y = data[:, 5]   # future_temp
        # normalize
        self.x_mean = X.mean(axis=0)
        self.x_std = X.std(axis=0) + 1e-8
        self.y_mean = y.mean()
        self.y_std = y.std() + 1e-8
        Xn = (X - self.x_mean) / self.x_std
        # add bias column
        Xb = np.hstack([Xn, np.ones((Xn.shape[0], 1))])
        # closed-form linear regression
        w, *_ = np.linalg.lstsq(Xb, (y - self.y_mean) / self.y_std, rcond=None)
        self.w = w
        self.save(self.model_path)
        return {"train_samples": X.shape[0]}
    
    def save(self, path):
        np.savez(path, w=self.w, x_mean=self.x_mean, x_std=self.x_std, y_mean=self.y_mean, y_std=self.y_std)

    def load(self, path):
        data = np.load(path)
        self.w = data["w"]
        self.x_mean = data["x_mean"]
        self.x_std = data["x_std"]
        self.y_mean = data["y_mean"]
        self.y_std = data["y_std"]

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--train", help="CSV training file", default=None)
    p.add_argument("--predict", action="store_true", help="demo predict")
    args = p.parse_args()

    agent = ThermalSafetyAgent()
    if args.train:
        print("Training from", args.train)
        stats = agent.train_from_csv(args.train)
        print("Trained:", stats)
    if args.predict:
        sample = {"current_temp": 36.5, "planned_speed": 60.0, "plasma_power": 80.0, "standoff_mm": 10.0, "tissue_type": 0}
        out = agent.recommend_action(sample)
        print("Sample predict ->", out)

if __name__ == "__main__":
    main()