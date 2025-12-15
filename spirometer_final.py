import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import time

# ---------------- Spirometry Calculations ----------------
def calculate_spirometry(age, height, sex, smoker):
    if sex.lower() == "male":
        fvc_pred = 0.052 * height - 0.022 * age - 3.60
        fev1_pred = 0.041 * height - 0.018 * age - 2.69
    else:
        fvc_pred = 0.041 * height - 0.018 * age - 2.69
        fev1_pred = 0.034 * height - 0.013 * age - 1.74

    if smoker:
        fvc_pred *= 0.9
        fev1_pred *= 0.85

    return max(fvc_pred, 1.5), max(fev1_pred, 1.0)

# ---------------- Breath Simulation ----------------
def simulate_breath(fvc_pred, fev1_pred, canvas, fig, ax,
                    time_var, flow_var, volume_var):

    ax.clear()
    total_points = 120
    t = np.linspace(0, 6, total_points)
    flow = np.zeros(total_points)
    volume = np.zeros(total_points)

    peak_flow = fvc_pred * (0.8 + 0.4 * np.random.rand())
    decay = 2.5 + np.random.rand()

    for i in range(total_points):
        flow[i] = (peak_flow * (i / total_points)) * np.exp(-decay * i / total_points)
        flow[i] += np.random.normal(0, 0.03)

        if i > 0:
            volume[i] = np.trapz(flow[:i+1], t[:i+1])

        if i % 20 == 0:
            time_var.set(f"{t[i]:.1f} s")
            flow_var.set(f"{flow[i]:.2f} L/s")
            volume_var.set(f"{volume[i]:.2f} L")

        ax.clear()
        ax.plot(t[:i+1], flow[:i+1], linewidth=2)
        ax.fill_between(t[:i+1], 0, flow[:i+1], alpha=0.3)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Flow (L/s)")
        ax.set_title("Real-Time Spirometry Flow")
        ax.grid(True)

        canvas.draw()
        time.sleep(0.02)

    fev1_measured = np.trapz(flow[:int(total_points/6)], t[:int(total_points/6)])
    fvc_measured = np.trapz(flow, t)

    return fvc_measured, fev1_measured

# ---------------- Interpretation ----------------
def interpret_results(fvc, fev1):
    ratio = fev1 / fvc
    if ratio >= 0.7:
        return "Normal Lung Function"
    elif ratio >= 0.5:
        return "Mild Obstruction"
    else:
        return "Severe Obstruction"

# ---------------- GUI Setup ----------------
root = tk.Tk()
root.title("Digital Spirometer Simulator")
root.geometry("1000x720")
root.configure(bg="#f2f2f2")
root.resizable(False, False)

style = ttk.Style(root)
style.theme_use("clam")
style.configure("TButton", font=("Helvetica", 12, "bold"), padding=8)
style.configure("TLabel", font=("Helvetica", 12))
style.configure("TLabelframe.Label", font=("Helvetica", 12, "bold"))

# ---------------- Input Frame ----------------
input_frame = ttk.LabelFrame(root, text="Patient Data", padding=15)
input_frame.pack(fill=tk.X, padx=20, pady=10)

ttk.Label(input_frame, text="Age (years):").grid(row=0, column=0, padx=10, pady=5)
age_entry = ttk.Entry(input_frame, width=10)
age_entry.grid(row=0, column=1)

ttk.Label(input_frame, text="Height (cm):").grid(row=1, column=0, padx=10, pady=5)
height_entry = ttk.Entry(input_frame, width=10)
height_entry.grid(row=1, column=1)

ttk.Label(input_frame, text="Sex:").grid(row=0, column=2, padx=20)
sex_combo = ttk.Combobox(input_frame, values=["Male", "Female"], state="readonly", width=10)
sex_combo.grid(row=0, column=3)
sex_combo.current(0)

ttk.Label(input_frame, text="Smoker:").grid(row=1, column=2, padx=20)
smoker_combo = ttk.Combobox(input_frame, values=["No", "Yes"], state="readonly", width=10)
smoker_combo.grid(row=1, column=3)
smoker_combo.current(0)

# ---------------- Real-Time Data Display ----------------
data_frame = ttk.LabelFrame(root, text="Live Device Readings", padding=15)
data_frame.pack(fill=tk.X, padx=20, pady=10)

time_var = tk.StringVar(value="0.0 s")
flow_var = tk.StringVar(value="0.0 L/s")
volume_var = tk.StringVar(value="0.0 L")

ttk.Label(data_frame, text="Time:").grid(row=0, column=0, padx=15)
ttk.Label(data_frame, textvariable=time_var, font=("Helvetica", 16, "bold")).grid(row=0, column=1)

ttk.Label(data_frame, text="Flow:").grid(row=0, column=2, padx=15)
ttk.Label(data_frame, textvariable=flow_var, font=("Helvetica", 16, "bold")).grid(row=0, column=3)

ttk.Label(data_frame, text="Volume:").grid(row=0, column=4, padx=15)
ttk.Label(data_frame, textvariable=volume_var, font=("Helvetica", 16, "bold")).grid(row=0, column=5)

# ---------------- Graph ----------------
graph_frame = ttk.Frame(root)
graph_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

fig, ax = plt.subplots(figsize=(9, 4))
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

# ---------------- Start Test ----------------
def start_test():
    try:
        age = float(age_entry.get())
        height = float(height_entry.get())
        sex = sex_combo.get()
        smoker = smoker_combo.get() == "Yes"

        fvc_pred, fev1_pred = calculate_spirometry(age, height, sex, smoker)

        def run():
            fvc, fev1 = simulate_breath(
                fvc_pred, fev1_pred,
                canvas, fig, ax,
                time_var, flow_var, volume_var
            )
            result = interpret_results(fvc, fev1)
            messagebox.showinfo(
                "Final Results",
                f"FVC: {fvc:.2f} L\n"
                f"FEV1: {fev1:.2f} L\n"
                f"FEV1/FVC: {fev1/fvc:.2f}\n\n"
                f"Interpretation: {result}"
            )

        threading.Thread(target=run, daemon=True).start()

    except ValueError:
        messagebox.showerror("Input Error", "Please enter valid numeric values.")

ttk.Button(input_frame, text="Start Test", command=start_test).grid(
    row=0, column=4, rowspan=2, padx=30
)

# ---------------- Main Loop ----------------
root.mainloop()
