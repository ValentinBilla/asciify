import itertools as it
import argparse
import json
import time
import os

from PIL import Image, ImageEnhance
import cv2

# COMMAND PARSER CONFIGURATION
parser = argparse.ArgumentParser(
  prog='ProgramName',
  description='What the program does',
  epilog='Text at the bottom of help'
)
parser.add_argument('filename')
parser.add_argument('-v', '--video', action='store_true')
parser.add_argument('-W', '--width', type=int, default=80)
parser.add_argument('-H', '--height', type=int, default=35)
parser.add_argument('-c', '--colored', action='store_true')
parser.add_argument('-p', '--palette', default='vscode')
parser.add_argument('-g', '--greyscale', default='@%#U*+=-:. ')
parser.add_argument('-r', '--ratio', type=float, default=11/25)
parser.add_argument('-d', '--dithered', action='store_true')
parser.add_argument('-t', '--transpose', action='store_true')
parser.add_argument('-b', '--bold', action='store_true')
parser.add_argument('-s', '--save', action='store_true')

args = parser.parse_args()

# RETRIEVING THE COLOR PALETTE
ANSI_CODES: list[str] = [f'\x1b[{i + (30 if i < 8 else 82)}m' for i in range(16)]

with open('palettes.json', 'r') as file:
  palettes = json.loads(file.read())
  if args.palette not in palettes:
    args.palette = 'vscode'
  
  hex_colors = palettes[args.palette]

rgb_colors: list[tuple[int]] = list()

for color in hex_colors:
  rgb_colors.append(tuple(int(color[1:], 16) >> bitshift & 255 for bitshift in (16, 8, 0)))

palette_image = Image.new('P', (1,1))
palette_image.putpalette(it.chain.from_iterable(rgb_colors))


def resize(image: Image.Image) -> Image.Image:
  if args.transpose:
    image = image.transpose(Image.Transpose.ROTATE_90)

  width, height = image.size
  ratio = args.ratio * height / width
  ascii_width = min(args.width, int(args.height / ratio))
  ascii_height = min(args.height, int(args.width * ratio))

  return image.resize((ascii_width, ascii_height))


def clear_screen() -> None: 
  os.system('cls' if os.name == 'nt' else 'clear')


def greyscaled_ascii(image: Image.Image) -> str:
  width, height = image.size
  grey_levels = image.convert('L').quantize(
    colors=len(args.greyscale),
    dither=Image.Dither.FLOYDSTEINBERG if args.dithered else Image.Dither.NONE).load()

  lines: list[str] = [''.join(args.greyscale[grey_levels[i, j]] for i in range(width)) for j in range(height)]
  return '\n'.join(lines)


def colored_ascii(image: Image.Image) -> str:
  width, height = image.size


  image = ImageEnhance.Color(image).enhance(4)
  quantized = image.convert('RGB').quantize(
    palette=palette_image,
    dither=Image.Dither.FLOYDSTEINBERG if args.dithered else Image.Dither.NONE).load()
  grey_levels = image.convert('L').quantize(
    colors=len(args.greyscale),
    dither=Image.Dither.FLOYDSTEINBERG if args.dithered else Image.Dither.NONE).load()

  chars: list[str] = list()
  current_color: int = -1

  if args.bold:
    chars.append('\x1b[1m')

  for j in range(height):
    for i in range(width):
      char = args.greyscale[grey_levels[i, j]]

      if args.colored and char != ' ':
        pixel_color = quantized[i, j]

        if pixel_color != current_color:
          chars.append(ANSI_CODES[pixel_color])
          current_color = pixel_color

      chars.append(char)
    chars.append('\n')
  chars.append('\x1b[0m')

  return ''.join(chars)


def show(image: Image.Image, *, clear: bool = False, save: bool = False) -> None:
  image = resize(image)

  if args.colored:
    text = colored_ascii(image)
  else:
    text = greyscaled_ascii(image)

  if clear:
    clear_screen()

  print(text)

  if save:
    text_filename = '.'.join((*args.filename.split('.')[:-1], 'txt'))
    with open(text_filename, 'w') as file:
      file.write(text)


def video() -> None:
  if args.filename.startswith('https'):
    video = pafy.new(args.filename)
    to_capture = video.getbest(preftype="webm")
  if args.filename == 'webcam':
    to_capture = 0
  else:
    to_capture = args.filename
  
  cap = cv2.VideoCapture(to_capture)
  fps = cap.get(cv2.CAP_PROP_FPS)

  last = time.time()
  while True:
    retrieved, frame = cap.read()
    
    if not retrieved:
        break
  
    color_converted = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    image = Image.fromarray(color_converted)

    time.sleep(max(0, 1/fps - (time.time() - last)))
    show(image, clear=True)
    last = time.time()


def image() -> None:
  image = Image.open(args.filename)
  
  show(image, save=args.save)

if __name__ == '__main__':
  if args.video:
    video()
  else:
    image()