import pandas as pd

df = pd.read_csv("1_2_3", header=None)
mean_val = df[1].mean()

print(f'network delay: {mean_val:.4f}')

df = pd.read_csv("1_2_0", header=None)
mean_val = df[1].mean()

print(f'end-to-end delay: {mean_val:.4f}')
