from math import tau, e
from numpy import array, pow, sqrt, cbrt, sin, cos
from numpy.linalg import norm
from random import random

phi = ((1 + sqrt(5)) / 2)

def distribute_disc(n):
    return array([
        pow(e, tau * i * 1j / phi) * sqrt(i / n)
        for i in range(n)
    ])

class Image:
    scale = (2560 + 1440j)
    icon_scale = scale.imag / 2
    center = scale / 2

class Colors:
    bg = "black"
    debug = "white"

def oklch_to_oklab(c):
    (l, c, h) = c
    return (l, c * cos(h), c * sin(h))


# https://bottosson.github.io/posts/oklab/
def linear_srgb_to_oklab(c):
    (r, g, b) = c
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l_ = cbrt(l)
    m_ = cbrt(m)
    s_ = cbrt(s)
    return (
        0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_,
        1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_,
        0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_,
    )

# https://bottosson.github.io/posts/oklab/
def oklab_to_linear_srgb(c):
    (L, a, b) = c
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l = l_*l_*l_
    m = m_*m_*m_
    s = s_*s_*s_
    return (
		+4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
		-1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
		-0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s,
	)

# https://entropymine.com/imageworsener/srgbformula/
def linear_srgb_to_srgb(c):
    (r, g, b) = c

    def f(L):
        if L <= 0.00313066844250063:
            return L * 12.92 
        else:
            return 1.055 * pow(L, 1 / 2.4) - 0.055

    return (f(r), f(g), f(b))
            
def oklch_to_rgb(c):
    (r, g, b) = linear_srgb_to_srgb(oklab_to_linear_srgb(oklch_to_oklab(c)))
    return (r * 256, g * 256, b * 256)


hexagon = pow(e, array([-i / 6 for i in range(6)]) * 1j * tau) * 0.5

# https://brand.nixos.org/documents/nixos-branding-guide.pdf
upper_apex = hexagon[2] + 0.125 * (hexagon[2] - hexagon[3]) / norm(hexagon[2] - hexagon[3]) + 0.0625 * (hexagon[5] - hexagon[2]) / norm(hexagon[5] - hexagon[2]) 
upper_notch = hexagon[2] + 0.125 * (hexagon[3] - hexagon[2]) / norm(hexagon[3] - hexagon[2]) + 0.0625 * (hexagon[5] - hexagon[2]) / norm(hexagon[5] - hexagon[2])
midpoint_join = -0.125+0j
rear_notch = hexagon[4] + 0.125 * (hexagon[3] - hexagon[4]) / norm(hexagon[3] - hexagon[4])
rear_foot = hexagon[4]
rear_heal = hexagon[4] + 0.125
joint_crotch = midpoint_join + 0.25 * (hexagon[4] - hexagon[3]) / norm(hexagon[4] - hexagon[3])
forward_heel = hexagon[5] - 0.125
forward_tip = hexagon[5] + 0.125

nix_lambda = array([
    upper_apex,
    upper_notch,
    midpoint_join,
    rear_notch,
    rear_foot,
    rear_heal,
    joint_crotch,
    forward_heel,
    forward_tip
])



background = f"""
    <rect width="{
        Image.scale.real
    }" height="{
        Image.scale.imag
    }" fill="{
        Colors.bg
    }" />
"""

circle = f"""
    <circle stroke="{
        Colors.debug
    }" fill="none" cx="{
        Image.center.real
    }" cy="{
        Image.center.imag
    }" r="{
        Image.icon_scale / 2
    }" />
"""

debug_hexagon = f"""
    <polygon stroke="{
        Colors.debug
    }" fill="none" points="{
        ''.join([f"{c.real},{c.imag} " for c in hexagon * Image.icon_scale + Image.center])
    }" />
"""

polygon_lambda = f"""
    <polygon fill="{
        Colors.debug
    }" points="{
        ''.join([f"{c.real},{c.imag} " for c in (nix_lambda * Image.icon_scale + Image.center)])
    }" />
"""

nix_logo = ""
for i in range(6):
    # (r, g, b) = oklch_to_rgb((1, 0, 0))
    color = "#4d6fb7" if i % 2 == 0 else "#5fb8f2"

    logo = (nix_lambda - rear_foot + hexagon[4] * (9 / 4)) * hexagon[i]

    nix_logo += f"""
        <polygon fill="{color}" points="{
            ''.join([f"{c.real},{c.imag} " for c in (logo * Image.icon_scale + Image.center)])
        }" />
    """

little_lambdas = ""
for p in distribute_disc(2500) * abs(Image.scale) / 2:
    bounds = Image.scale / 1.9

    if (
        p.real > bounds.real
        or p.real < -bounds.real
        or p.imag > bounds.imag
        or p.imag < -bounds.imag
        or abs(p) < Image.icon_scale / 1.7
    ):
        continue
    
    points = (
        nix_lambda
        * Image.icon_scale / 25
        * pow(e, random() * 1j * tau)
        + p
    ) + Image.center

    (r, g, b) = oklch_to_rgb((
        random() * 0.25 + 0.1, 0.1, random() * 360
    ))
    
    little_lambdas += f"""
        <polygon fill="rgb({round(r)} {round(g)} {round(b)})" points="{
            ''.join([f"{c.real},{c.imag} " for c in points])
        }" />
    """
    

data = f"""
    <svg
        version="1.1"
        width="{Image.scale.real}"
        height="{Image.scale.imag}"
        xmlns="http://www.w3.org/2000/svg"
    >
        {background}
        {little_lambdas}
        {nix_logo}
    </svg>
"""

with open("python.svg", "w") as svg:
    svg.write(data)
