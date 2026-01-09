import pulp as pl


# Sets
T = range(1, 5)
G = ['diesel', 'gas']

# Parameters
D = {
    1: 50,
    2: 60,
    3: 55,
    4: 45,
}


P_min = {
    'diesel': 10,
    'gas': 5,
}

P_max = {
    'diesel': 60,
    'gas': 40,
}

c = {
    'diesel': 80,
    "gas": 50,
}

C_start = {
    'diesel': 200,
    'gas': 100,
}

P_solar_hat = {
    1: 10,
    2: 20, 
    3: 15,
    4: 5,
}


# Model
model = pl.LpProblem("MicroGridDispatch", pl.LpMinimize)

# Decision Variables
P = pl.LpVariable.dicts("P", (G, T), lowBound=0)
n = pl.LpVariable.dicts("n", (G, T), cat="Binary")
s = pl.LpVariable.dicts("s", (G, T), cat="Binary")
P_solar = pl.LpVariable.dicts("P_solar", T, lowBound=0)


# Objective Function
total_cost = 0

for generator in G:
    for t in T:
        # Add generation cost
        total_cost += c[generator] * P[generator][t]
        # Add startup cost
        total_cost += C_start[generator] * s[generator][t]

# Set the objective
model += total_cost, "Total_Operational_Cost"

# Constraints
# 1. Power balance
for t in T:
    model += (
        pl.lpSum(P[g][t] for g in G) + P_solar[t] == D[t],
        f"Power_Balance_{t}"
    )

# 2. Capacity constraints
for g in G:
    for t in T:
        model += P[g][t] >= P_min[g] * n[g][t]
        model += P[g][t] <= P_max[g] * n[g][t]

# 3. Solar availability
for t in T:
    model += P_solar[t] <= P_solar_hat[t]

# 4. Startup constraint
for g in G:
    for t in T:
        if t == 1:
            model += s[g][t] >= n[g][t]
        else:
            model += s[g][t] >= n[g][t] - n[g][t - 1]


# Solve
model.solve(pl.PULP_CBC_CMD(msg=False))

# Results
print("Status:", pl.LpStatus[model.status])
print("\nDispatch Results:\n")

for t in T:
    print(f"Time period: {t}")

    # print each generator
    for g in G:
        on_status = int(n[g][t].value())
        power_output = P[g][t].value()
        startup_status = int(s[g][t].value())

        print(f"  Generator {g}:")
        print(f"    ON: {on_status}")
        print(f"    Power: {power_output:.1f} MW")
        print(f"    Startup: {startup_status}")
    
    # Print solar
    print(f"  Solar Power: {P_solar[t].value():.1f} MW\n")