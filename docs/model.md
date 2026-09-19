# Model and numerical contract

Free-Dose Check 0.1.0 implements a closed, well-mixed, conserved, single-affinity equilibrium system. One ligand molecule occupies one accessible site; the output describes incubation before separation or washing.

The finite-bath binding equations and depletion-related interpretation are established, rather than novel contributions of this software ([Hulme and Trevethick, 2010](https://pmc.ncbi.nlm.nih.gov/articles/PMC3000649/)). Accessible-site quantification and conditions matter in cell-binding assays ([Hunter and Cochran, 2016](https://pmc.ncbi.nlm.nih.gov/articles/PMC6067677/)).

## Units and conservation

Public concentration units are nM and final incubation volume is µL. With exact Avogadro constant \(N_A=6.02214076\times10^{23}\ \mathrm{mol}^{-1}\), cell count \(N\), and accessible sites per cell \(r\), use

\[
R_T = \frac{Nr\,10^{15}}{N_A V_{\mu L}}\quad\text{nM}.
\]

The equilibrium constraint is

\[
K_d=\frac{(R_T-B)(L_T-B)}{B}.
\]

Bound ligand \(B\), free ligand \(L_f\), and unoccupied sites are nonnegative. Ligand mass is conserved: \(B+L_f=L_T\).

## Stable evaluation

The familiar quadratic root subtracts nearly equal numbers in important limiting regimes. Production code uses the rationalized bound solution

\[
B=\frac{2R_TL_T}{R_T+L_T+K_d+\sqrt{(R_T-L_T)^2+K_d^2+2K_d(R_T+L_T)}}.
\]

Free ligand is evaluated independently, not obtained only by subtracting bound from total. With \(a=K_d+R_T-L_T\), the positive free-ligand root is

\[
L_f=\begin{cases}
2K_dL_T/(\sqrt{a^2+4K_dL_T}+a),&a\geq0,\\
(\sqrt{a^2+4K_dL_T}-a)/2,&a<0.
\end{cases}
\]

Concentrations are scaled by their maximum before multiplication. The small difference \(R_T-L_T\) is formed before scaling, and `math.fsum` accumulates the unscaled terms in \(a\): independently scaling nearly equal totals can erase their meaningful difference. This edge case is covered by a near-equality oracle test.

The verified input domain is \(10^{-12}\) through \(10^{12}\) nM for positive \(R_T,L_T,K_d\). Zero ligand is handled separately. Free or bound outputs may fall below the input-domain floor; their small positive values are preserved. The range is a software verification boundary, not a statement about experimental plausibility.

The core checks concentration bounds and ligand mass balance with relative tolerance \(10^{-12}\). Material violations raise `NumericalError`; only floating-point-scale negative occupancy error is floored at zero. Raw concentrations are not clipped to conceal invalid states.

## Measurements versus modeled quantities

- **Depletion:** \(B/L_T\), the fraction of added ligand bound.
- **Occupancy:** \(B/R_T\), the fraction of available sites occupied.
- **Naive occupancy:** \(L_T/(K_d+L_T)\), substituting added concentration for free.
- **Occupancy error:** \(100(\theta_{\mathrm{naive}}-\theta)\), in percentage points.
- **Half-occupancy concentration:** \(K_d+R_T/2\), a model-implied total concentration, not a fitted EC50 or functional potency.

At zero ligand, bound, free, and occupancy are zero. Depletion is null and assessment is `not_applicable`; a zero control never provides evidence for passing the depletion criterion.

## Bounds and decisions

The calculation evaluates each distinct combination of low/high sites and low/high affinity. Every output gets its own marginal minimum and maximum, without averaging corners or inventing a nominal value. These bounds are not probability distributions, confidence intervals, or joint trajectories.

Depletion increases with site concentration and decreases with \(K_d\) in this model. The conservative design corner therefore uses the highest sites per cell and lowest \(K_d\). Occupancy and other endpoints are independently bounded.

For tolerance \(\epsilon\), `within_tolerance` means the maximum is at or below the threshold; `exceeds_tolerance` means even the minimum exceeds it; otherwise the interval `crosses_tolerance`. Comparison uses `value <= epsilon * (1 + 1e-10)` to avoid classifying roundoff at the analytical boundary as a biological difference. This is a numerical tolerance, not measurement uncertainty.

Overall assessment gives precedence to any exceeding dose, then any crossing dose, then within tolerance. Every positive dose is included.

## Exact design limit

Substitute \(B=\epsilon L_T\) into the equilibrium constraint:

\[
R_{\mathrm{cap}}=\epsilon L_T+\frac{\epsilon K_d}{1-\epsilon}.
\]

The lowest positive input dose imposes the tightest site-capacity limit. The resulting volume and cell limits are algebraic, not rule-of-thumb tenfold ratios. Recommended volume is rounded upward to 0.001 µL and cell count downward to an integer, then each is evaluated through the forward model.

The implementation never recommends decreasing volume or increasing cells merely to use the limit. If the current condition is already within tolerance, it retains the current count and volume. Both supplied constraints apply to each option, including the variable held fixed.

Maintaining concentration while increasing volume requires proportionally more ligand molecules. Reducing cells can reduce experimental signal, which this model does not predict. Combined count-and-volume changes are not optimized in v0.1.0.
