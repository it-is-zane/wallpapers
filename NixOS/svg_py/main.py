from math import tau, e
from numpy import array, pow, sqrt, isnan
from random import random
import Okhsv

phi = ((1 + sqrt(5)) / 2)

def distribute_disc(n):
    return array([
        pow(e, tau * i * 1j / phi) * sqrt(i / n)
        for i in range(n)
    ])

class Image:
    scale = (2560 + 1440j)
    icon_scale = scale.imag / 4
    center = scale / 2

class Colors:
    bg = "black"
    debug = "white"


# https://brand.nixos.org/documents/nixos-branding-guide.pdf
THICKNESS = (1 / 4)
GAP = (1 / 16) # it is listed as 1 / 32 in the guide but 1 / 16 looks correct
RADIUS = (1)

hexagon = pow(e, array([-i / 6 for i in range(6)]) * 1j * tau)

upper_apex = hexagon[2] * RADIUS + hexagon[1] * THICKNESS + hexagon[5] * GAP
upper_notch = hexagon[2] * RADIUS - hexagon[1] * THICKNESS + hexagon[5] * GAP
midpoint_join = -THICKNESS
rear_notch = hexagon[4] * RADIUS + hexagon[2] * THICKNESS
rear_foot = hexagon[4]
rear_heal = hexagon[4] + THICKNESS
joint_crotch = midpoint_join + hexagon[5] * 2 * THICKNESS
forward_heel = hexagon[5] - THICKNESS
forward_tip = hexagon[5] + THICKNESS

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
        Image.icon_scale
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
            ''.join([f"{c.real},{c.imag} " for c in (logo * (4 / 9) * Image.icon_scale + Image.center)])
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
        or abs(p) < Image.icon_scale * 0.1
    ):
        continue
    
    points = (
        nix_lambda
        * Image.icon_scale / 32
        * pow(e, random() * 1j * tau)
        + p
    ) + Image.center

    # print(colour.COLOURSPACE_MODELS)
    # Oklch (0-1, 0-0.4, 1.0) yeah the ranges are weird
    # srgb (0-1, 0-1, 1.0)
    rgb = Okhsv.okhsv_to_srgb(array((
        random(), 1, abs(p / abs(Image.scale) * 2) 
    ))) * 255

    r, g, b = (0,0,0) if isnan(rgb).any() else rgb

    little_lambdas += f"""
        <polygon
            {
                #stroke="rgb({r2} {g2} {b2})"
                ""
            }
            fill="rgb({round(r)} {round(g)} {round(b)})"
            points="{
                ''.join([f"{c.real},{c.imag} " for c in points])
            }"
        />
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
