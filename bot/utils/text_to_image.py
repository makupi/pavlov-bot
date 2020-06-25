import io

import discord
from PIL import Image, ImageDraw, ImageFont

W_TEXT_PADDING = 40
H_TEXT_PADDING = 80
FONTSIZE = 32
BACKGROUND = (44, 47, 51)  # discord color
TEXT_COLOR = (255, 255, 255)
ROBOTO_MONO = "bot/utils/fonts/RobotoMono-Light.ttf"
FONT = ImageFont.truetype(ROBOTO_MONO, FONTSIZE)


def text_to_image(text: str, file_name: str) -> discord.File:

    text_w, text_h = list(), list()

    for line in text.split("\n"):
        w, h = FONT.getsize(line)
        text_w.append(w)
        text_h.append(h)

    image = Image.new(
        "RGBA", (max(text_w) + W_TEXT_PADDING, sum(text_h) + H_TEXT_PADDING), BACKGROUND
    )
    draw = ImageDraw.Draw(image)

    draw.text((W_TEXT_PADDING / 2, 0), text, TEXT_COLOR, font=FONT)
    data = io.BytesIO()
    image.save(data, format="PNG")
    data.seek(0)
    return discord.File(data, file_name)
