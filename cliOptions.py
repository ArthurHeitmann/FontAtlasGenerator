from __future__ import annotations
from PIL import Image, ImageFont
from PIL.ImageFont import FreeTypeFont

class OperationType:
	FROM_TEXTURE = 0
	FROM_FONT = 1

class ImgOperation:
	type: int
	# for font operations
	id: int
	drawChar: str|None
	charFontId: int|None
	# for texture operations
	srcTexId: int|None
	srcX: int|None
	srcY: int|None
	width: int|None
	height: int|None

	def __init__(self, d: dict):
		self.type = d.get("type")
		self.id = d.get("id")
		self.drawChar = d.get("drawChar", None)
		self.charFontId = d.get("charFontId", None)
		self.srcTexId = d.get("srcTexId", None)
		self.srcX = d.get("srcX", None)
		self.srcY = d.get("srcY", None)
		self.width = d.get("width", None)
		self.height = d.get("height", None)

class CliOptions:
	srcTexPaths: list[tuple[int, str]]
	srcTextures: dict[int, Image.Image|None]
	fonts: dict[int, tuple[FreeTypeFont, int]]
	dstTexPath: str
	operations: list[ImgOperation]

	def __init__(self, argsJson: dict):
		self.srcTexPaths = argsJson.get("srcTexPaths", [])
		self.dstTexPath = argsJson.get("dstTexPath", None)
		self.operations = [ImgOperation(d) for d in argsJson.get("operations", [])]

		self.srcTextures = {}
		for srcTexId, srcTexPath in self.srcTexPaths:
			self.srcTextures[srcTexId] = Image.open(srcTexPath)

		self.fonts = {}
		for fontId, fontOptions in argsJson.get("fonts", {}).items():
			fontPath = fontOptions.get("path")
			fontSize = fontOptions.get("size")
			self.fonts[fontId] = (ImageFont.truetype(fontPath, fontSize), fontSize)
