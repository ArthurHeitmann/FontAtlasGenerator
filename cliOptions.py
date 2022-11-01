from __future__ import annotations
from PIL import Image, ImageFont
from PIL.ImageFont import FreeTypeFont

class OperationType:
	FROM_TEXTURE = 0
	FROM_FONT = 1

class ImgOperation:
	type: int
	drawChar: str|None
	charFontId: int|None
	srcX: int|None
	srcY: int|None
	width: int|None
	height: int|None

	def __init__(self, d: dict):
		self.type = d.get("type")
		self.drawChar = d.get("drawChar", None)
		self.charFontId = d.get("charFontId", None)
		self.srcX = d.get("srcX", None)
		self.srcY = d.get("srcY", None)
		self.width = d.get("width", None)
		self.height = d.get("height", None)

class CliOptions:
	srcTexPath: str|None
	srcTex: Image.Image|None
	fonts: dict[int, FreeTypeFont] = {}
	dstTexPath: str
	operations: list[ImgOperation]

	def __init__(self, argsJson: dict):
		self.srcTexPath = argsJson.get("srcTexPath", None)
		self.dstTexPath = argsJson.get("dstTexPath", None)
		self.operations = [ImgOperation(d) for d in argsJson.get("operations", [])]

		if self.srcTexPath is not None:
			self.srcTex = Image.open(self.srcTexPath)

		for fontId, fontOptions in argsJson.get("fonts", {}).items():
			fontPath = fontOptions.get("path")
			fontSize = fontOptions.get("size")
			self.fonts[fontId] = ImageFont.truetype(fontPath, fontSize)
