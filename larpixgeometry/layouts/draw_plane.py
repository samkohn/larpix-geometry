'''
Generate a PDF of a pixel plane YAML file.

'''
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch, cm
import yaml
from larpixgeometry.pixelplane import PixelPlane
from larpixgeometry.layouts import load
import  numpy as np
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('layoutversion')
parser.add_argument('--pixelside', action='store_true')
args = parser.parse_args()
version = args.layoutversion
pixelside = args.pixelside
if pixelside:
    sidename = 'pixel'
else:
    sidename = 'chip'

pixelplane = PixelPlane.fromDict(load('layout-' + version + '.yaml'))
dimensions = pixelplane.dimensions
x_orig = dimensions['x']
y_orig = dimensions['y']
width_orig = dimensions['width']
height_orig = dimensions['height']

colors = np.array([[228, 26, 28], [55, 126, 184], [77, 175, 74], [152,
    78, 163], [255, 127, 0]])/256.0
colors = np.tile(colors, (10,1))


canvas_width, canvas_height = letter
c = canvas.Canvas('layout-' + version + '-' + sidename + 'side.pdf', pagesize=letter)

margin = 1*inch
page_center_x = canvas_width/2
page_center_y = canvas_height/2

remaining_width = canvas_width - 2*margin
remaining_height = canvas_height - 2*margin
width_scalefactor = remaining_width/width_orig
height_scalefactor = remaining_height/height_orig
scalefactor = min(width_scalefactor, height_scalefactor)
x_scaled = x_orig * scalefactor
y_scaled = y_orig * scalefactor
width_final = width_orig * scalefactor
height_final = height_orig * scalefactor
center_scaled_x = x_scaled + width_final/2
center_scaled_y = y_scaled + height_final/2
translation_x = page_center_x - center_scaled_x
translation_y = page_center_y - center_scaled_y
x_final = x_scaled + translation_x
y_final = y_scaled + translation_y
c.rect(x_final, y_final, width_final, height_final, fill=0, stroke=1)

def transform_x(xcoord):
    result = xcoord * scalefactor + translation_x
    if pixelside:
        result = canvas_width - result
    return result

def transform_y(ycoord):
    return canvas_height - (ycoord * scalefactor + translation_y)

c.setFont('Helvetica', 20)
c.drawString(3*inch, 10*inch, 'Layout %s (%d chips)' % (version,
    len(pixelplane.chips)))
c.drawString(3*inch, 9.6*inch, '(view from %s side)' % sidename)
c.setFont('Courier', 7)
colorkey = []
for pixel in pixelplane.pixels.values():
    c.circle(transform_x(pixel.x), transform_y(pixel.y), 0.4)
    c.drawCentredString(transform_x(pixel.x), transform_y(pixel.y),
            str(pixel.pixelid))
for chip, color in zip(pixelplane.chips.values(), colors):
    c.setFont('Courier-Bold', 9)
    c.setFillColorRGB(*color, alpha=1)
    colorkey.append(['Chip %d' % chip.chipid, color])
    x_sum = 0
    y_sum = 0
    count = 0
    for channel, pixel in enumerate(chip.channel_connections):
        if pixel != pixelplane.unconnected_pixel:
            c.drawCentredString(transform_x(pixel.x),
                    transform_y(pixel.y)-6,
                    str(channel))
            x_sum += transform_x(pixel.x)
            y_sum += transform_y(pixel.y) - 5
            count += 1
    x_avg = x_sum/float(count)
    y_avg = y_sum/float(count)
    font = ('Helvetica', 56)
    c.setFont(*font)
    c.setFillColorRGB(*color, alpha=0.45)
    width = c.stringWidth(str(chip.chipid), *font)
    c.drawCentredString(x_avg, y_avg-16, str(chip.chipid))
c.showPage()
c.save()
