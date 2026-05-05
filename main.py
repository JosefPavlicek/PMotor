import time
from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


DATA_DIR = Path("./data")      # složka, kde se bude objevovat data.txt
DATA_FILE = DATA_DIR / "data.txt"

REF_TORQUE = 15.0              # referenční moment
BASE_TOLERANCE = 2.0           # základní tolerance
DROP_THRESHOLD = 3.0           # skokový pokles momentu
MAX_POINTS = 500


def load_data():
    if not DATA_FILE.exists():
        return pd.DataFrame()

    df = pd.read_csv(
        DATA_FILE,
        sep=r"\s+",
        header=None,
        engine="python"
    )

    df.columns = [
        "time_ms",
        "status_word",
        "rpm_smooth",
        "torque_drive",
        "rpm_actual",
        "dc_link",
        "current",
        "output_voltage"
    ]

    # korekce hodnot typu 65535 jako signed 16-bit
    df["torque_drive"] = df["torque_drive"].apply(to_signed_16)

    return df


def to_signed_16(value):
    value = int(value)
    if value >= 32768:
        return value - 65536
    return value


def detect_state(df):
    if len(df) < 2:
        return "ČEKÁM NA DATA"

    current = df["torque_drive"].iloc[-1]
    previous = df["torque_drive"].iloc[-2]

    diff = current - previous

    lower = REF_TORQUE - BASE_TOLERANCE
    upper = REF_TORQUE + BASE_TOLERANCE

    if diff < -DROP_THRESHOLD:
        return "SKOKOVÝ POKLES MOMENTU"

    if current < lower:
        return "MOMENT POD REFERENCÍ"

    if current > upper:
        return "MOMENT NAD REFERENCÍ"

    return "OK"


fig, ax1 = plt.subplots(figsize=(12, 6))
ax2 = ax1.twinx()


def update(frame):
    df = load_data()

    if df.empty:
        return

    df = df.tail(MAX_POINTS)

    x = range(len(df))
    rpm = df["rpm_smooth"]
    torque = df["torque_drive"]

    state = detect_state(df)

    ax1.clear()
    ax2.clear()

    ax1.plot(x, rpm, label="rpm")
    ax2.plot(x, torque, label="Moment opr. [Nm]")

    ax2.axhline(REF_TORQUE, linestyle="--", label="Reference")
    ax2.axhline(REF_TORQUE - BASE_TOLERANCE, linestyle=":")
    ax2.axhline(REF_TORQUE + BASE_TOLERANCE, linestyle=":")

    ax1.set_ylabel("rpm")
    ax2.set_ylabel("Moment [Nm]")
    ax1.set_xlabel("Vzorky")

    ax1.grid(True)

    ax1.set_title(f"Online měření | Stav: {state}")

    ax1.legend(loc="upper left")
    ax2.legend(loc="upper right")


ani = FuncAnimation(fig, update, interval=1000)

plt.tight_layout()
plt.show()
