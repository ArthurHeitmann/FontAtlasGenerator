from __future__ import annotations
from dataclasses import dataclass
from PIL import Image, ImageDraw, ImageOps, ImageFilter, ImageEnhance
from PIL.ImageFont import FreeTypeFont

from cliOptions import FontOptions

from cliOptions import CliOptions, OperationType
def adjustFonts(options: CliOptions):
	# for each font:
	# 1. find largest bbox height extents
	# 2. optionally adjust yOffset and scale
	#   2.1. if max height is > fontHeight, scale font to fit
	#   2.2. if top most edge is != 0, adjust yOffset
	# 3. save bottom baseline

	font: FontOptions
	for fontId, font in options.fonts.items():
		# 1.
		testChars = {
			c for c in
			"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789ÄÖÜßÈÉÊËÀÂÄÇÌÍÎÏÒÓÔÖÙÚÛÜÑŸÆŒÆŒ[]"
		}
		testChars = {
			op.drawChar
			for op in options.operations
			if op.type == OperationType.FROM_FONT and op.charFontId == fontId
		}.union(testChars)
		minTop = 999999
		maxBottom = 0
		for c in testChars:
			bbox = font.font.getbbox(c)
			minTop = min(minTop, bbox[1])
			maxBottom = max(maxBottom, bbox[3])
		
		# 2.1.
		maxHeight = maxBottom - minTop + font.letYPadding*2
		if maxHeight > font.fontHeight:
			tooBigByFactor = maxHeight / font.fontHeight
			font.font = FreeTypeFont(font.fontPath, int(font.fontHeight / tooBigByFactor))
		# 2.2.
		if minTop != 0:
			font.letYOffset -= minTop
	
		# 3.
		fontMetrics = font.font.getmetrics()
		additionalYOffset = 0
		font.bottomBaseline = fontMetrics[0] + fontMetrics[1]
		if font.bottomBaseline < font.fontHeight:
			additionalYOffset = fontMetrics[1] // 2
		font.letYOffset += additionalYOffset
		font.bottomBaseline += additionalYOffset

@dataclass
class FontCharSize:
	char: str
	width: int
	height: int
	xOff: int
	yOff: int

def getCustomFontCharSizes(options: CliOptions) -> dict[str, FontCharSize]:
	charSizes: dict[str, FontCharSize] = {}
	for op in options.operations:
		if op.type != OperationType.FROM_FONT:
			continue
		fontOpt = options.fonts[op.charFontId]
		charBBox = fontOpt.font.getbbox(op.drawChar)
		charWidth = charBBox[2] - charBBox[0] + fontOpt.letXPadding*2
		charHeight = charBBox[3] - charBBox[1]
		charHeight = max(charHeight, fontOpt.fontHeight)
		xOff = fontOpt.letXOffset
		yOff = fontOpt.letYOffset
		charSizes[op.id] = FontCharSize(op.drawChar, charWidth, charHeight, xOff, yOff)
	return charSizes

def estimateAtlasSize(options: CliOptions, charSizes: dict[str, FontCharSize]) -> int:
	allCharsWidth = 0
	allCharsHeight = 0
	allCharsCount = 0
	if charSizes:
		allCharsWidth = sum(s.width for s in charSizes.values())
		allCharsHeight = max(s.height for s in charSizes.values())
		allCharsCount = len(charSizes)
	texOps = [op for op in options.operations if op.type == OperationType.FROM_TEXTURE]
	if texOps:
		allCharsWidth += sum(op.width for op in texOps)
		allCharsHeight += sum(op.height for op in texOps)
		allCharsCount += len(texOps)

	avrCharWidth = allCharsWidth / allCharsCount + options.letterSpacing
	avrCharHeight = allCharsHeight / allCharsCount + options.letterSpacing

	estimatedAtlasArea = avrCharWidth * avrCharHeight * allCharsCount
	estimatedAtlasArea *= 1.2

	size = 256
	while size**2 < estimatedAtlasArea:
		size *= 2
	
	return size

def generateAtlas(options: CliOptions, charSizes: dict[str, FontCharSize], atlasSize: int) -> tuple[Image.Image, dict]:
	atlasMap = {
		"size": atlasSize,
		"fontParams": {
			fontId: {
				"baseline": font.bottomBaseline,
				"scale": font.font.size / font.fontHeight,
			}
			for fontId, font in options.fonts.items()
		},
		"symbols": {},
	}
	atlas = Image.new("RGBA", (atlasSize, atlasSize), color=(0, 0, 0, 0))
	draw = ImageDraw.Draw(atlas)

	curX = 0
	curY = 0
	curRowHeight = 0
	for op in options.operations:
		if op.type == OperationType.FROM_FONT:
			charWidth = charSizes[op.id].width
			charHeight = charSizes[op.id].height
		elif op.type == OperationType.FROM_TEXTURE:
			charWidth = op.width
			charHeight = op.height
		else:
			raise Exception("Unknown operation type")
		curRowHeight = max(curRowHeight, charHeight)
		if curX + charWidth + options.letterSpacing > atlasSize:
			curX = options.letterSpacing
			curY += curRowHeight + options.letterSpacing
			curRowHeight = 0
			if curY + charHeight > atlasSize:
				# big oof
				return generateAtlas(options, charSizes, atlasSize * 2)

		if op.type == OperationType.FROM_FONT:
			font = options.fonts[op.charFontId]
			xOff = charSizes[op.id].xOff
			yOff = charSizes[op.id].yOff
			draw.text((curX + xOff, curY + yOff), op.drawChar, font=font.font)
		elif op.type == OperationType.FROM_TEXTURE:
			srcTex = options.srcTextures[op.srcTexId]
			atlas.paste(srcTex.crop((op.srcX, op.srcY, op.srcX + op.width, op.srcY + op.height)), (curX, curY))
		
		atlasMap["symbols"][op.id] = {
			"x": curX,
			"y": curY,
			"width": charWidth,
			"height": charHeight,
		}
		curX += charWidth + options.letterSpacing
	
	# fix half transparent pixels
	mask = atlas.getchannel("A")
	out = Image.new("RGBA", atlas.size, color=(0, 0, 0, 255))
	out.paste(mask)
	# out = out.filter(ImageFilter.BoxBlur(radius=0.25))
	# out = ImageEnhance.Brightness(out).enhance(1.5)
	out.putalpha(mask)
	
	
	return out, atlasMap

def generateFontAtlas(options: CliOptions) -> dict:
	options.operations.sort(key=lambda op: options.fonts[op.charFontId].fontHeight if op.type == OperationType.FROM_FONT else op.height)
	adjustFonts(options)
	charSizes = getCustomFontCharSizes(options)
	atlasSize = estimateAtlasSize(options, charSizes)
	atlas, atlasMap = generateAtlas(options, charSizes, atlasSize)
	atlas.save(options.dstTexPath)
	return atlasMap
