# MIP for Microgrid Dispatch
*Friday 9 of January*

*Roberto Araya Day* 

## 1. Introduction
Dispatching involves selecting the most cost-effective combination of generators to meet the current demand for electricity, taking into account factors such as:
 - The cost of each generator.
 - The amount of electricity it can produce.
 - Its availability.

The goal of dispatch is to minimize the cost of generation while meeting electricity demand. This may include costs associated with starting and stopping generators, emissions, or other operational considerations.

Several approaches can be used to solve a dispatch problem, including linear programming, dynamic programming and heuristics. For this example, mixed integer programming (MIP) is used, as its allows the modeling of discrete operational decisiones, such as:
 - Generator ON/OFF status.
 - Startup events.

## 1. Optimization Problem Definition

This document describes a microgrid dispatch problem over a discrete time horizon $ t \in T$. At each step time step, the model determines:
 - Which generators should be operating.
 - How much power each operating generator should produce.

The objective is to minimize total cost while satisfying electricity demand and respecting generator operational constraints.

## 2. System Components

### Generators
The microgrid consists of three generators:
- Diesel Generator (dispatchable, high cost)
- Natural Gas Generator (dispatchable, medium cost)
- Solar PV (non-dispatchable, zero marginal cost)

 Note: Diesel and gas are modeled as single units, each with a binary ON/OFF decision. Solar PV is modeled as a single aggregated generator with time-varying availability.
Solar generation has:
- No startup or shutdown costs
- No ON/OFF decision
- Zero marginal cost

## 3. Sets and Parameters

### Sets 
- $T$: sets of time periods
- $G = \{DG, NG\}$: set of dispatchable generatos.

### Parameters
- $D_t: $ electricity demand at time $t$ (MW).
- $P_{g}^{min}$: minimum power output of generator $g \in G_{disp}$ when ON (MW).
- $P_{g}^{max}$: maximum power output of generator $g \in G_{disp}$ when ON (MW).
- $c_{g}$: marginal cost of generator $g$ ($/MWh).
- $C_g^{start}:$ startup cost of generator $g$.
- $\hat{P}_{solar, t}$: available solar power at time $t$ (MW).
Solar generation is assumed to have zero marginal and startup costs.


### 3. Decision Variables
The optimization problem includes two types of decision variables.

### Continuous Variables
- $P_{g,t}$: Power output of generator $g\in G_{disp}$ at time t (MW)
- $P_{solar, t}$: Power output of the solar photovoltaic generator at time $𝑡$.

### Binary variables
- $_{g,t} \in \{0,1\}$: Commitment status of generator $g\in G_{disp}$ at time $t$. $1$ if generator is ON, and $0$ if OFF.
- $s_{g,t} \in \{0,1\}$: Startup indicator for generator $g\in G_{disp}$. $1$ if generator starts on time $t$, $0$ if not.

## 4. Objective Function
The objective is to minimize the total generation cost over the time horizon:

$$
\min{\sum_{t} \sum_{g\in G_{disp}}}(c_{g}P_{g,t} + C_{g}^{start}s_{g,t})
$$

where:

- $c_{g}$ is the marginal cost of generator g.
- $P_{g,t}$ is the power produced by generator $g$ at time $t$.
- $C_{g}^{start}$ is the startup cost of generator g.
- $s_{g,t} \in \{0, 1\}$ indicates whether generator g starts up at time $t$.
- $G_{disp}$ denotes the set of dispatchable generators.

## 5. Constraints

### 1. Power Balance Constraint
Ensures electricity demand is exactly met at each time step.
$$
\sum_{g} P_{g,t} + P_{solar, t} = D_{t} ~~~~~~~\forall t \in T
$$  

### 2. Generator Availability Constraints (Binary)
Each dispatchable generator can be ON or OFF.
$$
n_{g,t} \in \{0,1\}~~~~~~~\forall g \in G_{disp}, \forall t \in T
$$

### 3. Capacity Constranits (Diesel and Gas)
Constraints generation commitment to power output.
$$P_{g}^{min} n_{g,t}\leq P_{g,t} \leq P_{g}^{max} n_{g,t} ~~~~~~\forall g \in G_{disp}, \forall t \in T$$

### 4. Solar Generation Constraint
Models solar generation as non-dispatchable.
$$0 \leq P_{solar, t} \leq \hat{P}_{solar, t}~~~~ \forall t \in T$$

### 5. Startup Constraints
**start-up logic**
$$s_{g,t} \geq n_{g,t} - n_{g, t-1}~~~~~~ \forall g \in G_{disp}, \forall t \in T$$

**initial condition**: assuming zero generators online at startup simplifies the formulation.

$$n_{g,0} = 0 ~~~~~~~~ \forall g \in G_{disp}$$

### 6. Variable Domain Constraints
Defines variable types

$$P_{g,t} \ge 0 \qquad \forall g,t$$
$$n_{g,t}, s_{g,t} \in \{0,1\} \qquad \forall g,t$$

# Solution

The *Python* solution is implemented in *solver.py*. It uses open-source modeling library *PuLP* together with the CBC solver to compute the optimal dispatch.

For a microservice implementation, i propose using FastAPI to expose an endpoint that retuns the values of the decision variables for each time step  in response to a POST request.

The flow would be as follow:

```
[ Client / UI ]
       |
       | POST requests with inputs
       |
       v
[ Microservice (FastAPI) ]
       |
       | Pulp Model
       | CBC Solver
       |
       v
[ Dispatch Mapping Layer ]
       |
       | Map PuLP variables to JSON format
       |
       v
[ JSON Response ]
```

**API Contract**

`POST /dispatch`

- Request body

  Contains all inputs required to solve the optimization problem:

  - Electricity demand over the time horizon.
  - Solar availability/forecast.
  - Diesel and gas generator parameters
  (marginal cost, startup cost, minimum and maximum output)
- Response body:

  Returns the objective value, and the computed dispatch for each time step, including:
  - Diesel generator output and ON/OFF status.
  - Gas Generation output and ON/OFF status.
  - Solar generation.



Notes and implementation details:
- Check that demand and solar arrays have the same length as time horizon.
- Use Pydantics models in FastApi for input validation.
- Implement caching for repeated inputs.
- Solver method inside a services file: outside of the controller logic (most of the logic of the *solver.py* file) -> Keep controller thin.
- Implement integration tests (POST requests) to check that dispatch mathces demand and edge cases.

### Request (POST /dispatch) Example

```
{
  "time_horizon": [0, 1, 2],
  "demand": [60, 55, 70],
  "solar": [10, 20, 15],
  "generators": {
    "diesel": { "p_min": 10, "p_max": 50, "cost": 80, "startup_cost": 200 },
    "gas":    { "p_min": 20, "p_max": 70, "cost": 60, "startup_cost": 300 }
  }
}
```

### Response Example
```
{
  "status": "optimal",
  "objective_value": 10200,
  "dispatch": [
    { "time": 0, "diesel": { "on": true, "power": 40 }, "gas": { "on": false, "power": 10 }, "solar": 10 },
    { "time": 1, "diesel": { "on": true, "power": 35 }, "gas": { "on": false, "power": 0 },  "solar": 20 },
    { "time": 2, "diesel": { "on": true, "power": 45 }, "gas": { "on": true,  "power": 10 }, "solar": 15 }
  ]
}
```


**Sources**
- ChatGPT for understanding, definition of the problem (variables and constraints), and code writing assistance/refinement.
- [Dispatching Problem](https://medium.com/@amunagekar/optimizing-power-generation-by-solving-the-dispatching-problem-a600e3706700): Understanding problem Modeling and solver.