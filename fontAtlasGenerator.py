from __future__ import annotations
from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont

from cliOptions import CliOptions, OperationType

def getCustomFontCharSizes(options: CliOptions) -> dict[str, tuple[int, int]]:
	charSizes: dict[str, tuple[int, int]] = {}
	for op in options.operations:
		if op.type != OperationType.FROM_FONT:
			continue
		charBBox = options.fonts[op.charFontId][0].getbbox(op.drawChar)
		charWidth = charBBox[2] - charBBox[0]
		charHeight = charBBox[3] - charBBox[1]
		charHeight = max(charHeight, options.fonts[op.charFontId][1])
		charSizes[op.drawChar] = (charWidth, charHeight)
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

def generateAtlas(options: CliOptions, charSizes: dict[str, tuple[int, int]], atlasSize: int) -> tuple[Image.Image, dict]:
	atlasMap = {
		"size": atlasSize,
		"symbols": {},
	}
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
			draw.text((curX, curY), op.drawChar, font=options.fonts[op.charFontId][0])
		elif op.type == OperationType.FROM_TEXTURE:
			srcTex = options.srcTextures[op.srcTexId]
			atlas.paste(srcTex.crop((op.srcX, op.srcY, op.srcX + op.width, op.srcY + op.height)), (curX, curY))
		
		atlasMap["symbols"][op.id] = {
			"x": curX,
			"y": curY,
			"width": charWidth,
			"height": charHeight,
		}
		curX += charWidth
	
	return atlas, atlasMap

def generateFontAtlas(options: CliOptions) -> dict:
	charSizes = getCustomFontCharSizes(options)
	atlasSize = estimateAtlasSize(options, charSizes)
	atlas, atlasMap = generateAtlas(options, charSizes, atlasSize)
	atlas.save(options.dstTexPath)
	return atlasMap
