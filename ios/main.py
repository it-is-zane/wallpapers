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
    scale = (1290 + 2796j)
    icon_scale = abs(scale) / 6
    center = scale / 2

class Colors:
    bg = "black"
    debug = "white"


background = f"""
    <rect width="{
        Image.scale.real
    }" height="{
        Image.scale.imag
    }" fill="{
        Colors.bg
    }" />
"""

# path used by apple.com for their apple logo
# <path d="m13.0729 17.6825a3.61 3.61 0 0 0 -1.7248 3.0365 3.5132 3.5132 0 0 0 2.1379 3.2223 8.394 8.394 0 0 1 -1.0948 2.2618c-.6816.9812-1.3943 1.9623-2.4787 1.9623s-1.3633-.63-2.613-.63c-1.2187 0-1.6525.6507-2.644.6507s-1.6834-.9089-2.4787-2.0243a9.7842 9.7842 0 0 1 -1.6628-5.2776c0-3.0984 2.014-4.7405 3.9969-4.7405 1.0535 0 1.9314.6919 2.5924.6919.63 0 1.6112-.7333 2.8092-.7333a3.7579 3.7579 0 0 1 3.1604 1.5802zm-3.7284-2.8918a3.5615 3.5615 0 0 0 .8469-2.22 1.5353 1.5353 0 0 0 -.031-.32 3.5686 3.5686 0 0 0 -2.3445 1.2084 3.4629 3.4629 0 0 0 -.8779 2.1585 1.419 1.419 0 0 0 .031.2892 1.19 1.19 0 0 0 .2169.0207 3.0935 3.0935 0 0 0 2.1586-1.1368z"></path> 
defs = """
    <defs>
        <symbol id="apple" overflow="visible">
            <path d="M 0.38109484,-0.15913632 A 0.2265396,0.2265396 0 0 0 0.27285786,0.03141424 0.22046509,0.22046509 0 0 0 0.40701827,0.23362438 0.52675167,0.52675167 0 0 1 0.33831588,0.37555995 c -0.0427726,0.0615737 -0.087497,0.12314085 -0.15554673,0.12314085 -0.0680497,0 -0.0855517,-0.0395345 -0.16397452,-0.0395345 -0.07647752,0 -0.10369992,0.0408337 -0.16591989,0.0408337 -0.0622199,0 -0.10563899,-0.0570363 -0.15554672,-0.12703162 a 0.61399137,0.61399137 0 0 1 -0.10434629,-0.3311873 c 0,-0.19443498 0.12638526,-0.29748226 0.25081889,-0.29748226 0.0661107,0 0.12120184,0.043419 0.1626818,0.043419 0.0395346,0 0.1011082,-0.046017 0.17628673,-0.046017 a 0.23582083,0.23582083 0 0 1 0.19832569,0.0991629 z M 0.14712524,-0.34060648 A 0.22349608,0.22349608 0 0 0 0.20027104,-0.47991892 0.09634523,0.09634523 0 0 0 0.19832568,-0.5 a 0.22394162,0.22394162 0 0 0 -0.14712521,0.0758312 0.2173086,0.2173086 0 0 0 -0.05509123,0.13545311 0.08904701,0.08904701 0 0 0 0.001946,0.0181483 0.0746765,0.0746765 0 0 0 0.0136112,0.001299 0.1941275,0.1941275 0 0 0 0.1354588,-0.071338 z"></path>
        </symbol>
    </defs>
"""

apple_logo = f'<use href="#apple" fill="rgb(255 255 255)" transform="translate({Image.center.real} {Image.center.imag}) scale({Image.icon_scale})"/>'


little_apples = ""
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
    
    # print(colour.COLOURSPACE_MODELS)
    # Oklch (0-1, 0-0.4, 1.0) yeah the ranges are weird
    # srgb (0-1, 0-1, 1.0)
    rgb = Okhsv.okhsv_to_srgb(array((
        random(), 1, abs(p / abs(Image.scale) * 2) 
    ))) * 255

    r, g, b = (0,0,0) if isnan(rgb).any() else rgb

    p += Image.center
    little_apples += f"""
        f'<use href="#apple" fill="rgb({r} {g} {b})" transform="translate({p.real} {p.imag}) scale({Image.icon_scale / 16}) rotate({random() * 360})"/>'
    """

data = f"""
    <svg
        version="1.1"
        width="{Image.scale.real}"
        height="{Image.scale.imag}"
        xmlns="http://www.w3.org/2000/svg"
    >
        {defs}
        {background}
        {little_apples}
        {apple_logo}
    </svg>
"""

with open("python.svg", "w") as svg:
    svg.write(data)
