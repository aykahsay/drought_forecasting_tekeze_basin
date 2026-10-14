# AI-DREWS Drought Index Methodology
## Theoretical Formulations, Parameterizations, and Standard Normal Transformation

**Document ID:** `AI-DREWS-DOC-DIM-2026-10`  
**Reference Standards:** McKee et al. (1993); Vicente-Serrano et al. (2010); Beguería et al. (2014); Hosking (1990)  
**Status:** **ACTIVE METHODOLOGY SPECIFICATION**

---

### 1. Standardized Precipitation Index (SPI-3)

The Standardized Precipitation Index (SPI) quantifies precipitation deficits over a specified aggregation scale (3 months for seasonal agricultural drought).

#### 1.1 Accumulation
For monthly precipitation $P_t$:
$$P_t^{(3)} = P_t + P_{t-1} + P_{t-2}$$

#### 1.2 Two-Parameter Gamma Distribution
Precipitation accumulations $x = P_t^{(3)} > 0$ follow a Gamma density function:
$$g(x) = \frac{1}{\beta^\alpha \Gamma(\alpha)} x^{\alpha - 1} e^{-x/\beta}, \quad x > 0$$

Where $\alpha > 0$ is the shape parameter, $\beta > 0$ is the scale parameter, and $\Gamma(\alpha)$ is the gamma function.

#### 1.3 Thom (1958) Maximum Likelihood Estimation
Over non-zero observations ($x_i > 0$):
$$A = \ln(\bar{x}) - \frac{1}{n} \sum_{i=1}^n \ln(x_i)$$
$$\hat{\alpha} = \frac{1}{4 A} \left( 1 + \sqrt{1 + \frac{4 A}{3}} \right), \quad \hat{\beta} = \frac{\bar{x}}{\hat{\alpha}}$$

#### 1.4 Zero-Precipitation Mixed Probability
If zero rainfall occurs with sample probability $q = \frac{m}{n}$ (where $m$ is the count of zeros in the calibration sample):
$$H(x) = q + (1 - q) G(x)$$
Where $G(x) = \frac{1}{\Gamma(\hat{\alpha})} \gamma(\hat{\alpha}, x/\hat{\beta})$ is the incomplete gamma function.

---

### 2. Standardized Precipitation-Evapotranspiration Index (SPEI-3)

The SPEI incorporates evaporative demand alongside precipitation by standardizing the climatic water balance:
$$D_t = P_t - \text{PET}_t$$
$$D_t^{(3)} = D_t + D_{t-1} + D_{t-2}$$

#### 2.1 Generalized Logistic (GLO) Distribution
Because $D_t^{(3)}$ can take both negative and positive values and often displays heavy skewness, the 3-parameter Generalized Logistic distribution (Hosking 1990; Beguería et al. 2014) is employed.

##### Probability Density Function
$$f(x) = \frac{\alpha^{-1} e^{-(1 - k) y}}{(1 + e^{-y})^2}, \quad y = -k^{-1} \ln\left[ 1 - \frac{k(x - \xi)}{\alpha} \right]$$

##### Cumulative Distribution Function (Complete Pair)
$$F(x) = \frac{1}{1 + \left[ 1 - \frac{k(x - \xi)}{\alpha} \right]^{1/k}}, \quad k \neq 0$$
$$\lim_{k \to 0} F(x) = \frac{1}{1 + \exp\left(-\frac{x - \xi}{\alpha}\right)}$$

##### Quantile Function (Inverse CDF)
$$x(F) = \xi + \frac{\alpha}{k}\left[ 1 - \left( \frac{1 - F}{F} \right)^k \right], \quad k \neq 0$$

#### 2.2 Unbiased Sample L-Moments
Parameters $(\xi, \alpha, k)$ are estimated from sample probability-weighted moments (PWMs):
$$b_r = \frac{1}{n} \sum_{i=1}^n \frac{\binom{i-1}{r}}{\binom{n-1}{r}} x_{(i)}, \quad r \in \{0, 1, 2\}$$
$$l_1 = b_0, \quad l_2 = 2 b_1 - b_0, \quad l_3 = 6 b_2 - 6 b_1 + b_0$$
$$\tau_3 = \frac{l_3}{l_2} \implies k = -\tau_3, \quad \alpha = \frac{l_2 \sin(k \pi)}{k \pi}, \quad \xi = l_1 - \frac{\alpha}{k}\left[1 - \frac{k \pi}{\sin(k \pi)}\right]$$

---

### 3. Month-Specific Calibration over Fixed Normal (1991–2020)

Because climate regimes in Northern Ethiopia are strongly seasonal, separate distributions are fitted for each of the 12 ending calendar months:
* For ending calendar month $m \in \{1, \dots, 12\}$:
  * Extract calibration observations $\{D_{3, y, m} \mid y \in [1991, 2020]\}$.
  * Fit distribution parameters $(\xi_m, \alpha_m, k_m)$.
  * Standardize all months ending in calendar month $m$.

---

### 4. Standard Normal Transformation

Non-exceedance probability $H(x)$ or $F(x)$ is converted to standard normal deviate $Z \sim \mathcal{N}(0, 1)$:
$$Z = \Phi^{-1}(P) = \sqrt{2} \cdot \text{erf}^{-1}(2P - 1)$$
Implemented via `scipy.special.ndtri` with unclipped mathematical outputs.
