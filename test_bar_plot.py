import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from mplib.bar_w_stats import bar_plot_w_stats

# Create mock data
np.random.seed(42)
data = []
groups = ['Control', 'Treatment']
attributes = ['Value1', 'Value2']

for group in groups:
    for _ in range(10):
        data.append({
            'Group': group,
            'Value1': np.random.normal(10 if group == 'Control' else 12, 2),
            'Value2': np.random.normal(20 if group == 'Treatment' else 22, 3)
        })

df = pd.DataFrame(data)

# Create plot
fig, ax = plt.subplots(figsize=(10, 6))
try:
    bar_plot_w_stats(ax, df, "Test Panel")
    plt.savefig("test_bar_plot.png")
    print("Plot created successfully: test_bar_plot.png")
except Exception as e:
    print(f"Error creating plot: {e}")
