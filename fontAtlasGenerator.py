from __future__ import annotations
from dataclasses import dataclass
from PIL import Image, ImageDraw
from PIL.ImageFont import FreeTypeFont

from cliOptions import CliOptions, OperationType

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
		charWidth = charBBox[2] - charBBox[0]
		charHeight = charBBox[3] - charBBox[1]
		charHeight = max(charHeight, fontOpt.fontHeight)
		xOff = fontOpt.letXOffset - charBBox[0]/2
		yOff = fontOpt.letYOffset - charBBox[1]/2
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

	avrCharWidth = allCharsWidth / allCharsCount
	avrCharHeight = allCharsHeight / allCharsCount

	estimatedAtlasArea = avrCharWidth * avrCharHeight * allCharsCount
	estimatedAtlasArea *= 1.5

	size = 256
	while size**2 < estimatedAtlasArea:
		size *= 2
	
	return size

def generateAtlas(options: CliOptions, charSizes: dict[str, FontCharSize], atlasSize: int) -> tuple[Image.Image, dict]:
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
			charWidth = charSizes[op.id].width
			charHeight = charSizes[op.id].height
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
		curX += charWidth
	
	return atlas, atlasMap

def generateFontAtlas(options: CliOptions) -> dict:
	charSizes = getCustomFontCharSizes(options)
	# options.operations.sort(key=lambda op: charSizes[op.id].height if op.type == OperationType.FROM_FONT else op.height)
	atlasSize = estimateAtlasSize(options, charSizes)
	atlas, atlasMap = generateAtlas(options, charSizes, atlasSize)
	atlas.save(options.dstTexPath)
	return atlasMap
