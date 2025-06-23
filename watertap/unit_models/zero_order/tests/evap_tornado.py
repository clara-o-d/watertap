import pandas as pd
import matplotlib.pyplot as plt

# Load CSV
file_path = 'pond_sensitivity.csv'
df = pd.read_csv(file_path)

df.columns = df.columns.str.strip()
df = df.rename(columns={'# flow vol (m^3/h)': 'flow vol (m^3/h)'})

# Find baseline
baseline_row = df.iloc[(df['capex'] - df['capex'].median()).abs().argmin()]
baseline_capex = baseline_row['capex']

# Parameters to analyze
parameters = ['flow vol (m^3/h)', 'Li (kg/m^3)', 'solar radiation (mJ/m^2)', 'land cost', 'liner thickness (mm)']
sensitivity_data = []

# Calc sensitivities
for param in parameters:
    grouped = df.groupby(param)['capex'].mean()
    min_val = grouped.min()
    max_val = grouped.max()
    delta_min = min_val - baseline_capex
    delta_max = max_val - baseline_capex
    sensitivity_data.append((param, delta_min, delta_max))

sensitivity_df = pd.DataFrame(sensitivity_data, columns=['Parameter', 'MinEffect', 'MaxEffect'])
sensitivity_df['Range'] = sensitivity_df['MaxEffect'] - sensitivity_df['MinEffect']
sensitivity_df = sensitivity_df.sort_values(by='Range', ascending=True)

# Plot tornado chart
fig, ax = plt.subplots(figsize=(10, 6))
for idx, row in sensitivity_df.iterrows():
    ax.barh(row['Parameter'], row['MaxEffect'], color='skyblue', left=baseline_capex)
    ax.barh(row['Parameter'], row['MinEffect'], color='blue', left=baseline_capex)

ax.axvline(baseline_capex, color='black', linestyle='--', label='Baseline Capex')
ax.set_xlabel('Capital Expenditure (capex)')
ax.set_title('Tornado Plot of Parameter Sensitivities on Capex')
plt.legend()
plt.tight_layout()
plt.show()
