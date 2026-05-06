
# Copyright(c) 2021 Björn Ottosson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this softwareand associated documentation files(the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and /or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions :
# The above copyright noticeand this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

#include <cmath>
#include <cfloat>
from numpy import ndarray, array, cbrt, sqrt, pi, cos, sin, atan2
from sys import float_info

# struct Lab { float L; float a; float b; };
# struct RGB { float r; float g; float b; };
# struct HSV { float h; float s; float v; };
# struct HSL { float h; float s; float l; };
# struct LC { float L; float C; };
Lab = ndarray
RGB = ndarray
HSV = ndarray
HSL = ndarray
LC = ndarray


# Alternative representation of (L_cusp, C_cusp)
# Encoded so S = C_cusp/L_cusp and T = C_cusp/(1-L_cusp) 
# The maximum value for C in the triangle is then found as fmin(S*L, T*(1-L)), for a given L
# struct ST { float S; float T; };
ST = ndarray


# constexpr float pi = 3.1415926535897932384626433832795028841971693993751058209749445923078164062f;

def clamp(x: float, min: float, max: float) -> float:
	if (x < min):
		return min
	if (x > max):
		return max

	return x


def sgn(x: float) -> float:
	return (0.0 < x) - (x < 0.0)

def srgb_transfer_function(a: float) -> float:
	return 12.92 * a if .0031308 >= a else 1.055 * pow(a, .4166666666666667) - .055

def srgb_transfer_function_inv(a: float) -> float:
	return pow((a + .055) / 1.055, 2.4) if .04045 < a else a / 12.92

def linear_srgb_to_oklab(c: RGB) -> Lab:
    r, g, b = c
    l: float = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m: float = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s: float = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_: float = cbrt(l)
    m_: float = cbrt(m)
    s_: float = cbrt(s)

    return array([
		0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
		1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
		0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
	])


def oklab_to_linear_srgb(c: Lab) -> RGB:
    L, a, b = c
    l_: float = L + 0.3963377774 * a + 0.2158037573 * b
    m_: float = L - 0.1055613458 * a - 0.0638541728 * b
    s_: float = L - 0.0894841775 * a - 1.2914855480 * b

    l: float = l_ * l_ * l_
    m: float = m_ * m_ * m_
    s: float = s_ * s_ * s_

    return array([
		+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
		-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
		-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
	])

# Finds the maximum saturation possible for a given hue that fits in sRGB
# Saturation here is defined as S = C/L
# a and b must be normalized so a^2 + b^2 == 1
def compute_max_saturation(a: float, b: float) -> float:
	# Max saturation will be when one of r, g or b goes below zero.

	# Select different coefficients depending on which component goes below zero first
	# k0, k1, k2, k3, k4, wl, wm, ws

	if (-1.88170328 * a - 0.80936493 * b > 1):
		# Red component
		k0 = +1.19086277; k1 = +1.76576728; k2 = +0.59662641; k3 = +0.75515197; k4 = +0.56771245
		wl = +4.0767416621; wm = -3.3077115913; ws = +0.2309699292
	elif (1.81444104 * a - 1.19445276 * b > 1):
		# Green component
		k0 = +0.73956515; k1 = -0.45954404; k2 = +0.08285427; k3 = +0.12541070; k4 = +0.14503204
		wl = -1.2684380046; wm = +2.6097574011; ws = -0.3413193965
	else:
		# Blue component
		k0 = +1.35733652; k1 = -0.00915799; k2 = -1.15130210; k3 = -0.50559606; k4 = +0.00692167
		wl = -0.0041960863; wm = -0.7034186147; ws = +1.7076147010

	# Approximate max saturation using a polynomial:
	S: float = k0 + k1 * a + k2 * b + k3 * a * a + k4 * a * b

	# Do one step Halley's method to get closer
	# this gives an error less than 10e6, except for some blue hues where the dS/dh is close to infinite
	# this should be sufficient for most applications, otherwise do two/three steps 

	k_l: float = +0.3963377774 * a + 0.2158037573 * b
	k_m: float = -0.1055613458 * a - 0.0638541728 * b
	k_s: float = -0.0894841775 * a - 1.2914855480 * b

	l_: float = 1.0 + S * k_l
	m_: float = 1.0 + S * k_m
	s_: float = 1.0 + S * k_s

	l: float = l_ * l_ * l_
	m: float = m_ * m_ * m_
	s: float = s_ * s_ * s_

	l_dS: float = 3.0 * k_l * l_ * l_
	m_dS: float = 3.0 * k_m * m_ * m_
	s_dS: float = 3.0 * k_s * s_ * s_

	l_dS2: float = 6.0 * k_l * k_l * l_
	m_dS2: float = 6.0 * k_m * k_m * m_
	s_dS2: float = 6.0 * k_s * k_s * s_

	f: float = wl * l + wm * m + ws * s
	f1: float = wl * l_dS + wm * m_dS + ws * s_dS
	f2: float = wl * l_dS2 + wm * m_dS2 + ws * s_dS2

	return S - f * f1 / (f1 * f1 - 0.5 * f * f2)


# finds L_cusp and C_cusp for a given hue
# a and b must be normalized so a^2 + b^2 == 1
def find_cusp(a: float, b: float) -> LC:
	# First, find the maximum saturation (saturation S = C/L)
	S_cusp: float = compute_max_saturation(a, b)

	# Convert to linear sRGB to find the first point where at least one of r,g or b >= 1:
	(r_at_max, g_at_max, b_at_max) = oklab_to_linear_srgb(array([ 1, S_cusp * a, S_cusp * b ]))
	L_cusp: float = cbrt(1. / max(max(r_at_max, g_at_max), b_at_max))
	C_cusp: float = L_cusp * S_cusp

	return array([ L_cusp , C_cusp ])


# Finds intersection of the line defined by 
# L = L0 * (1 - t) + t * L1;
# C = t * C1;
# a and b must be normalized so a^2 + b^2 == 1
def find_gamut_intersection_6(a: float, b: float, L1: float, C1: float, L0: float, cusp: LC) -> float:
	# Find the intersection for upper and lower half seprately
    t: float
    cusp_C, cusp_L = cusp
    if (((L1 - L0) * cusp_C - (cusp_L - L0) * C1) <= 0.0):
		# Lower half

        t = cusp_C * L0 / (C1 * cusp_L + cusp_C * (L0 - L1))
    else:
        # Upper half

        # First intersect with triangle
        t = cusp_C * (L0 - 1.0) / (C1 * (cusp_L - 1.0) + cusp_C * (L0 - L1))

		# Then one step Halley's method
        dL: float = L1 - L0
        dC: float = C1

        k_l: float = +0.3963377774 * a + 0.2158037573 * b
        k_m: float = -0.1055613458 * a - 0.0638541728 * b
        k_s: float = -0.0894841775 * a - 1.2914855480 * b

        l_dt: float = dL + dC * k_l
        m_dt: float = dL + dC * k_m
        s_dt: float = dL + dC * k_s


		# If higher accuracy is required, 2 or 3 iterations of the following block can be used:
        for _ in range(2):
            L: float = L0 * (1.0 - t) + t * L1
            C: float = t * C1

            l_: float = L + C * k_l
            m_: float = L + C * k_m
            s_: float = L + C * k_s

            l: float = l_ * l_ * l_
            m: float = m_ * m_ * m_
            s: float = s_ * s_ * s_

            ldt: float = 3 * l_dt * l_ * l_
            mdt: float = 3 * m_dt * m_ * m_
            sdt: float = 3 * s_dt * s_ * s_

            ldt2: float = 6 * l_dt * l_dt * l_
            mdt2: float = 6 * m_dt * m_dt * m_
            sdt2: float = 6 * s_dt * s_dt * s_

            r: float = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s - 1
            r1: float = 4.0767416621 * ldt - 3.3077115913 * mdt + 0.2309699292 * sdt
            r2: float = 4.0767416621 * ldt2 - 3.3077115913 * mdt2 + 0.2309699292 * sdt2

            u_r: float = r1 / (r1 * r1 - 0.5 * r * r2)
            t_r: float = -r * u_r

            g: float = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s - 1
            g1: float = -1.2684380046 * ldt + 2.6097574011 * mdt - 0.3413193965 * sdt
            g2: float = -1.2684380046 * ldt2 + 2.6097574011 * mdt2 - 0.3413193965 * sdt2

            u_g: float = g1 / (g1 * g1 - 0.5 * g * g2)
            t_g: float = -g * u_g

            b: float = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s - 1
            b1: float = -0.0041960863 * ldt - 0.7034186147 * mdt + 1.7076147010 * sdt
            b2: float = -0.0041960863 * ldt2 - 0.7034186147 * mdt2 + 1.7076147010 * sdt2

            u_b: float = b1 / (b1 * b1 - 0.5 * b * b2)
            t_b: float = -b * u_b

            t_r = t_r if u_r >= 0.0 else float_info.max
            t_g = t_g if u_g >= 0.0 else float_info.max
            t_b = t_b if u_b >= 0.0 else float_info.max

            t += min(t_r, min(t_g, t_b))

    return t


def find_gamut_intersection_5(a: float, b: float, L1: float, C1: float, L0: float) -> float:
	# Find the cusp of the gamut triangle
	cusp: LC = find_cusp(a, b)

	return find_gamut_intersection_6(a, b, L1, C1, L0, cusp)


def gamut_clip_preserve_chroma(rgb: RGB) -> RGB:
	rgb_r, rgb_g, rgb_b = rgb
	if (rgb_r < 1 and rgb_g < 1 and rgb_b < 1 and rgb_r > 0 and rgb_g > 0 and rgb_b > 0):
		return rgb

	lab: Lab = linear_srgb_to_oklab(rgb)
	lab_L, lab_a, lab_b = lab

	L: float  = lab_L
	eps: float  = 0.00001
	C: float  = max(eps, sqrt(lab_a * lab_a + lab_b * lab_b))
	a_: float  = lab_a / C
	b_: float  = lab_b / C

	L0: float = clamp(L, 0, 1)

	t: float = find_gamut_intersection_5(a_, b_, L, C, L0)
	L_clipped: float = L0 * (1 - t) + t * L
	C_clipped: float = t * C

	return oklab_to_linear_srgb(array((L_clipped, C_clipped * a_, C_clipped * b_)))


def gamut_clip_project_to_0_5(rgb: RGB) -> RGB:
	rgb_r, rgb_g, rgb_b = rgb
	if (rgb_r < 1 and rgb_g < 1 and rgb_b < 1 and rgb_r > 0 and rgb_g > 0 and rgb_b > 0):
		return rgb

	lab: Lab = linear_srgb_to_oklab(rgb)
	lab_L, lab_a, lab_b = lab

	L: float  = lab_L
	eps: float  = 0.00001
	C: float  = max(eps, sqrt(lab_a * lab_a + lab_b * lab_b))
	a_: float  = lab_a / C
	b_: float  = lab_b / C

	L0: float  = 0.5

	t: float  = find_gamut_intersection_5(a_, b_, L, C, L0)
	L_clipped: float  = L0 * (1 - t) + t * L
	C_clipped: float  = t * C

	return oklab_to_linear_srgb(array((L_clipped, C_clipped * a_, C_clipped * b_)))


def gamut_clip_project_to_L_cusp(rgb: RGB) -> RGB:
	rgb_r, rgb_g, rgb_b = rgb

	if (rgb_r < 1 and rgb_g < 1 and rgb_b < 1 and rgb_r > 0 and rgb_g > 0 and rgb_b > 0):
		return rgb

	lab: Lab = linear_srgb_to_oklab(rgb)
	lab_L, lab_a, lab_b = lab

	L: float = lab_L
	eps: float = 0.00001
	C: float = max(eps, sqrt(lab_a * lab_a + lab_b * lab_b))
	a_: float = lab_a / C
	b_: float = lab_b / C

	# The cusp is computed here and in find_gamut_intersection, an optimized solution would only compute it once.
	cusp: LC = find_cusp(a_, b_)
	cusp_L, _ = cusp

	L0: float = cusp_L

	t: float = find_gamut_intersection_5(a_, b_, L, C, L0)

	L_clipped: float = L0 * (1 - t) + t * L
	C_clipped: float = t * C

	return oklab_to_linear_srgb(array((L_clipped, C_clipped * a_, C_clipped * b_)))


def gamut_clip_adaptive_L0_0_5(rgb: RGB , alpha: float = 0.05) -> RGB:
	rgb_r, rgb_g, rgb_b = rgb

	if (rgb_r < 1 and rgb_g < 1 and rgb_b < 1 and rgb_r > 0 and rgb_g > 0 and rgb_b > 0):
		return rgb

	lab: Lab = linear_srgb_to_oklab(rgb)
	lab_L, lab_a, lab_b = lab

	L: float = lab_L
	eps: float = 0.00001
	C: float = max(eps, sqrt(lab_a * lab_a + lab_b * lab_b))
	a_: float = lab_a / C
	b_: float = lab_b / C

	Ld: float = L - 0.5
	e1: float = 0.5 + abs(Ld) + alpha * C
	L0: float = 0.5 * (1.0 + sgn(Ld) * (e1 - sqrt(e1 * e1 - 2.0 * abs(Ld))))

	t: float = find_gamut_intersection_5(a_, b_, L, C, L0)
	L_clipped: float = L0 * (1.0 - t) + t * L
	C_clipped: float = t * C

	return oklab_to_linear_srgb(array((L_clipped, C_clipped * a_, C_clipped * b_)))


def gamut_clip_adaptive_L0_L_cusp(rgb: RGB, alpha: float = 0.05) -> RGB:
	rgb_r, rgb_g, rgb_b = rgb

	if (rgb_r < 1 and rgb_g < 1 and rgb_b < 1 and rgb_r > 0 and rgb_g > 0 and rgb_b > 0):
		return rgb

	lab: Lab  = linear_srgb_to_oklab(rgb)
	lab_L, lab_a, lab_b = lab

	L: float  = lab_L
	eps: float  = 0.00001
	C: float  = max(eps, sqrt(lab_a * lab_a + lab_b * lab_b))
	a_: float  = lab_a / C
	b_: float  = lab_b / C

	# The cusp is computed here and in find_gamut_intersection, an optimized solution would only compute it once.
	cusp: LC = find_cusp(a_, b_)
	cusp_L, _ = cusp

	Ld: float = L - cusp_L
	k: float = 2.0 * (1.0 - cusp_L if Ld > 0 else cusp_L)

	e1: float = 0.5 * k + abs(Ld) + alpha * C / k
	L0: float = cusp_L + 0.5 * (sgn(Ld) * (e1 - sqrt(e1 * e1 - 2.0 * k * abs(Ld))))

	t: float = find_gamut_intersection_5(a_, b_, L, C, L0)
	L_clipped: float = L0 * (1.0 - t) + t * L
	C_clipped: float = t * C

	return oklab_to_linear_srgb(array((L_clipped, C_clipped * a_, C_clipped * b_)))


def toe(x: float) -> float:
	k_1: float = 0.206
	k_2: float = 0.03
	k_3: float = (1.0 + k_1) / (1.0 + k_2)
	return 0.5 * (k_3 * x - k_1 + sqrt((k_3 * x - k_1) * (k_3 * x - k_1) + 4 * k_2 * k_3 * x))


def toe_inv(x: float) -> float:
	k_1: float = 0.206
	k_2: float = 0.03
	k_3: float = (1.0 + k_1) / (1.0 + k_2)
	return (x * x + k_1 * x) / (k_3 * (x + k_2))


def to_ST(cusp: LC) -> ST: 
	cusp_L, cusp_C = cusp
	L: float = cusp_L
	C: float = cusp_C
	return array((C / L, C / (1 - L)))


# Returns a smooth approximation of the location of the cusp
# This polynomial was created by an optimization process
# It has been designed so that S_mid < S_max and T_mid < T_max
def get_ST_mid(a_: float, b_: float) -> ST:
	S: float = 0.11516993 + 1.0 / (
		+7.44778970 + 4.15901240 * b_
		+ a_ * (-2.19557347 + 1.75198401 * b_
			+ a_ * (-2.13704948 - 10.02301043 * b_
				+ a_ * (-4.24894561 + 5.38770819 * b_ + 4.69891013 * a_
					)))
		)

	T: float = 0.11239642 + 1.0 / (
		+1.61320320 - 0.68124379 * b_
		+ a_ * (+0.40370612 + 0.90148123 * b_
			+ a_ * (-0.27087943 + 0.61223990 * b_
				+ a_ * (+0.00299215 - 0.45399568 * b_ - 0.14661872 * a_
					)))
		)

	return array((S, T))


# Cs { float C_0; float C_mid; float C_max; };
Cs = ndarray
def get_Cs(L: float, a_: float, b_: float) -> Cs:
	cusp: LC = find_cusp(a_, b_)

	C_max: float = find_gamut_intersection_6(a_, b_, L, 1, L, cusp)
	ST_max: ST = to_ST(cusp)
	ST_max_S, ST_max_T = ST_max
	
	# Scale factor to compensate for the curved part of gamut shape:
	k: float = C_max / min((L * ST_max_S), (1 - L) * ST_max_T)

	C_mid: float 
	ST_mid: ST = get_ST_mid(a_, b_)
	ST_mid_S, ST_mid_T = ST_mid

	# Use a soft minimum function, instead of a sharp triangle shape to get a smooth value for chroma.
	C_a: float = L * ST_mid_S
	C_b: float = (1.0 - L) * ST_mid_T
	C_mid = 0.9 * k * sqrt(sqrt(1.0 / (1.0 / (C_a * C_a * C_a * C_a) + 1.0 / (C_b * C_b * C_b * C_b))))

	C_0: float
	# for C_0, the shape is independent of hue, so ST are constant. Values picked to roughly be the average values of ST.
	C_a: float = L * 0.4
	C_b: float = (1.0 - L) * 0.8

	# Use a soft minimum function, instead of a sharp triangle shape to get a smooth value for chroma.
	C_0 = sqrt(1.0 / (1.0 / (C_a * C_a) + 1.0 / (C_b * C_b)))

	return array((C_0, C_mid, C_max))


def okhsl_to_srgb(hsl: HSL) -> RGB:
	hsl_h, hsl_s, hsl_l = hsl

	h: float = hsl_h
	s: float = hsl_s
	l: float = hsl_l

	if (l == 1.0):
		return array((1.0, 1.0, 1.0))

	elif (l == 0.0):
		return array((0.0, 0.0, 0.0))

	a_: float = cos(2.0 * pi * h)
	b_: float = sin(2.0 * pi * h)
	L: float = toe_inv(l)

	cs: Cs = get_Cs(L, a_, b_)
	cs_C_0, cs_C_mid, cs_C_max = cs

	C_0: float = cs_C_0
	C_mid: float = cs_C_mid
	C_max: float = cs_C_max

	mid: float = 0.8
	mid_inv: float = 1.25

	C, t, k_0, k_1, k_2 = array(0.0)

	if (s < mid):
		t = mid_inv * s

		k_1 = mid * C_0
		k_2 = (1.0 - k_1 / C_mid)

		C = t * k_1 / (1.0 - k_2 * t)
	else:
		t = (s - mid)/ (1 - mid)

		k_0 = C_mid
		k_1 = (1.0 - mid) * C_mid * C_mid * mid_inv * mid_inv / C_0
		k_2 = (1.0 - (k_1) / (C_max - C_mid))

		C = k_0 + t * k_1 / (1.0 - k_2 * t)

	rgb: RGB = oklab_to_linear_srgb(array((L, C * a_, C * b_)))
	rgb_r, rgb_g, rgb_b = rgb

	return array((
		srgb_transfer_function(rgb_r),
		srgb_transfer_function(rgb_g),
		srgb_transfer_function(rgb_b),
	))


def srgb_to_okhsl(rgb: RGB) -> HSL:
	rgb_r, rgb_g, rgb_b = rgb

	lab: Lab = linear_srgb_to_oklab(array((
		srgb_transfer_function_inv(rgb_r),
		srgb_transfer_function_inv(rgb_g),
		srgb_transfer_function_inv(rgb_b)
	)))
	lab_L, lab_a, lab_b = lab

	C: float = sqrt(lab_a * lab_a + lab_b * lab_b)
	a_: float = lab_a / C
	b_: float = lab_b / C

	L: float = lab_L
	h: float = 0.5 + 0.5 * atan2(-lab_b, -lab_a) / pi

	cs: Cs = get_Cs(L, a_, b_)
	cs_C_0, cs_C_mid, cs_C_max = cs
	
	C_0: float = cs_C_0
	C_mid: float = cs_C_mid
	C_max: float = cs_C_max

	# Inverse of the interpolation in okhsl_to_srgb:

	mid: float = 0.8
	mid_inv: float = 1.25

	s: float
	if (C < C_mid):
		k_1: float = mid * C_0
		k_2: float = (1.0 - k_1 / C_mid)

		t: float = C / (k_1 + k_2 * C)
		s = t * mid
	else:
		k_0: float = C_mid
		k_1: float = (1.0 - mid) * C_mid * C_mid * mid_inv * mid_inv / C_0
		k_2: float = (1.0 - (k_1) / (C_max - C_mid))

		t: float = (C - k_0) / (k_1 + k_2 * (C - k_0))
		s = mid + (1.0 - mid) * t

	l: float = toe(L)
	return array((h, s, l))


def okhsv_to_srgb( hsv: HSV) -> RGB: 
	h, s, v = hsv

	a_: float  = cos(2.0 * pi * h)
	b_: float  = sin(2.0 * pi * h)
	cusp: LC = find_cusp(a_, b_)
	ST_max: LC  = to_ST(cusp)
	ST_max_S, ST_max_T = ST_max
	S_max: ST  = ST_max_S
	T_max: float  = ST_max_T
	S_0: float  = 0.5
	k: float  = 1 - S_0 / S_max

	# first we compute L and V as if the gamut is a perfect triangle:

	# L, C when v==1:
	L_v: float = 1     - s * S_0 / (S_0 + T_max - T_max * k * s)
	C_v: float = s * T_max * S_0 / (S_0 + T_max - T_max * k * s)

	L: float = v * L_v
	C: float = v * C_v

	# then we compensate for both toe and the curved top part of the triangle:
	L_vt: float = toe_inv(L_v)
	C_vt: float = C_v * L_vt / L_v

	L_new: float = toe_inv(L)
	C = C * L_new / L
	L = L_new

	rgb_scale: RGB = oklab_to_linear_srgb(array((L_vt, a_ * C_vt, b_ * C_vt)))
	rgb_scale_r, rgb_scale_g, rgb_scale_b = rgb_scale
	scale_L: float = cbrt(1.0 / max(max(rgb_scale_r, rgb_scale_g), max(rgb_scale_b, 0.0)))

	L = L * scale_L
	C = C * scale_L

	rgb: RGB = oklab_to_linear_srgb(array((L, C * a_, C * b_)))
	rgb_r, rgb_g, rgb_b = rgb
	return array((
		srgb_transfer_function(rgb_r),
		srgb_transfer_function(rgb_g),
		srgb_transfer_function(rgb_b),
	))


def srgb_to_okhsv(rgb: RGB) -> HSV:
	rgb_r, rgb_g, rgb_b = rgb
	lab: Lab = linear_srgb_to_oklab(array((
		srgb_transfer_function_inv(rgb_r),
		srgb_transfer_function_inv(rgb_g),
		srgb_transfer_function_inv(rgb_b)
	)))

	lab_L, lab_a, lab_b = lab

	C: float = sqrt(lab_a * lab_a + lab_b * lab_b)
	a_: float = lab_a / C
	b_: float = lab_b / C

	L: float = lab_L
	h: float = 0.5 + 0.5 * atan2(-lab_b, -lab_a) / pi

	cusp: LC = find_cusp(a_, b_)
	ST_max: ST = to_ST(cusp)
	ST_max_S, ST_max_T = ST_max
	S_max: float = ST_max_S
	T_max: float = ST_max_T
	S_0: float = 0.5
	k: float = 1 - S_0 / S_max

	# first we find L_v, C_v, L_vt and C_vt

	t: float = T_max / (C + L * T_max)
	L_v: float = t * L
	C_v: float = t * C

	L_vt: float = toe_inv(L_v)
	C_vt: float = C_v * L_vt / L_v

	# we can then use these to invert the step that compensates for the toe and the curved top part of the triangle:
	rgb_scale: RGB = oklab_to_linear_srgb(array((L_vt, a_ * C_vt, b_ * C_vt)))
	rgb_scale_r, rgb_scale_g, rgb_scale_b = rgb_scale

	scale_L: float = cbrt(1.0 / max(max(rgb_scale_r, rgb_scale_g), max(rgb_scale_b, 0.0)))

	L = L / scale_L
	C = C / scale_L

	C = C * toe(L) / L
	L = toe(L)

	# we can now compute v and s:

	v: float = L / L_v
	s: float = (S_0 + T_max) * C_v / ((T_max * S_0) + T_max * k * C_v)

	return array((h, s, v))


# } # namespace ok_color
