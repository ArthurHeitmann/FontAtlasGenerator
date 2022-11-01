from __future__ import annotations
from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont

from cliOptions import CliOptions, OperationType

def getCustomFontCharSizes(options: CliOptions) -> dict[str, tuple[int, int]]:
	charSizes: dict[str, tuple[int, int]] = {}
	for op in options.operations:
		if op.type != OperationType.FROM_FONT:
			continue
		charBBox = options.fonts[op.charFontId].getbbox(op.drawChar)
		charSizes[op.drawChar] = (charBBox[2] - charBBox[0], charBBox[3] - charBBox[1])
	return charSizes

def estimateAtlasSize(options: CliOptions, charSizes: dict[str, tuple[int, int]]) -> int:
	allCharsWidth = sum(w for w, h in charSizes.values())
	allCharsHeight = max(h for w, h in charSizes.values())
	allCharsCount = len(charSizes)
	texOps = [op for op in options.operations if op.type == OperationType.FROM_TEXTURE]
	allCharsWidth += sum(op.width for op in texOps)
	allCharsHeight += sum(op.height for op in texOps)
	allCharsCount += len(texOps)

	avrCharWidth = allCharsWidth / allCharsCount
	avrCharHeight = allCharsHeight / allCharsCount

	estimatedAtlasArea = avrCharWidth * avrCharHeight * allCharsCount
	estimatedAtlasArea *= 1.5

	size = 256
	while size**2 < estimatedAtlasArea:
		size *= 2
	
	return size

def generateAtlas(options: CliOptions, charSizes: dict[str, tuple[int, int]], atlasSize: int) -> Image.Image:
	
	atlas = Image.new("RGBA", (atlasSize, atlasSize), color=(0, 0, 0, 0))
	draw = ImageDraw.Draw(atlas)

	curX = 0
	curY = 0
	curRowHeight = 0
	for op in options.operations:
		if op.type == OperationType.FROM_FONT:
			charWidth = charSizes[op.drawChar][0]
			charHeight = charSizes[op.drawChar][1]
		elif op.type == OperationType.FROM_TEXTURE:
			charWidth = op.width
			charHeight = op.height
		else:
			raise Exception("Unknown operation type")
		curRowHeight = max(curRowHeight, charHeight)
		if curX + charWidth > atlasSize:
			curX = 0
			curY += curRowHeight
			curRowHeight = 0
			if curY + charHeight > atlasSize:
				# big oof
				return generateAtlas(options, charSizes, atlasSize * 2)
		
		if op.type == OperationType.FROM_FONT:
			draw.text((curX, curY), op.drawChar, font=options.fonts[op.charFontId])
		elif op.type == OperationType.FROM_TEXTURE:
			atlas.paste(options.srcTex.crop((op.srcX, op.srcY, op.srcX + op.width, op.srcY + op.height)), (curX, curY))
		
		curX += charWidth
	
	return atlas

def generateFontAtlas(options: CliOptions):
	charSizes = getCustomFontCharSizes(options)
	atlasSize = estimateAtlasSize(options, charSizes)
	atlas = generateAtlas(options, charSizes, atlasSize)
	atlas.save(options.dstTexPath)
