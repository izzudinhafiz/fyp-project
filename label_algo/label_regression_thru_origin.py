import matplotlib.pyplot as plt
import numpy as np
from scipy import stats

test_data = [4,3,2,5,4,7,9,10,6,11,13,14,5,20]
x_data = [x for x in range(len(test_data))]

m, c, r, p, std_err = stats.linregress(x_data,test_data)
first_point = c
best_line = [x * m + c for x in range(len(test_data))]

mid_point = 0
if len(best_line) % 2 == 0:
    # 0,1,2,3,4,5,6,7,8,9
    mid_index = (len(x_data) - 1) / 2
    mid_point = (best_line[int(mid_index - 0.5)] + best_line[int(mid_index + 0.5)]) / 2
    plt.plot(mid_index, mid_point, "rx")
else:
    # 0,1,2,3,4,5,6,7,8
    mid_index = (len(best_line) - 1)/2
    mid_point = best_line[int(mid_index)]
    plt.plot(mid_index, mid_point, "rx")

new_intercept = test_data[0] - first_point + c
new_slope = (mid_point - test_data[0]) / mid_index
new_line = [x*new_slope+new_intercept for x in range(len(test_data))]

count = 0
slope = new_slope
intercept = new_line[0]
best_ssr = 999999999999999999999
best_slope = 0

while count < 100:
    test_line = [x*slope + intercept for x in range(len(x_data))]
    ssr = 0
    for item in zip(test_data, test_line):
        ssr += (item[0] - item[1])**2

    if ssr < best_ssr:
        best_ssr = ssr
        best_slope = slope

    if count < 50:
        slope = slope*1.01
    elif count == 50:
        slope = new_slope
    else:
        slope = 0.99*slope

    count += 1

test_line = [x*best_slope + intercept for x in range(len(x_data))]

ssr_new_line = 0
for item in zip(test_data, new_line):
    y = item[0]
    y_hat = item[1]
    ssr_new_line += (y - y_hat)**2

translated_data = np.asarray(test_data) - test_data[0]
x_vector = np.asarray(x_data)
a = np.square(x_vector).sum()
b = (-2*x_vector*translated_data).sum()
m_new = -(b / (2*a))

single_line = [x*m_new+test_data[0] for x in range(len(test_data))]

print(m, new_slope, m_new, best_slope)

plt.plot(x_data, test_data, "kx", linestyle=" ")
plt.plot(x_data, best_line, label="OLS-Line")
plt.plot(x_data, new_line, label="Rotate-Line")
plt.plot(x_data, single_line, label="RTO-Line")
plt.plot(x_data, test_line, label="Brute-Force-Line", linestyle="--")
plt.legend()
plt.show()
