from __future__ import annotations
from PIL import Image, ImageFont
from PIL.ImageFont import FreeTypeFont

class OperationType:
	FROM_TEXTURE = 0
	FROM_FONT = 1

class ImgOperation:
	type: int
	id: int
	# for font operations
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

class FontOptions:
	fontPath: str
	font: FreeTypeFont
	fontHeight: int
	fontScale: int
	letXOffset: int
	letYOffset: int

	def __init__(self, d: dict):
		self.fontPath = d.get("path")
		self.fontHeight = d.get("height")
		self.fontScale = d.get("scale", 1)
		self.letXOffset = d.get("letXOffset", 0)
		self.letYOffset = d.get("letYOffset", 0)
		self.font = ImageFont.truetype(self.fontPath, size=int(self.fontHeight * self.fontScale))

class CliOptions:
	srcTexPaths: list[tuple[int, str]]
	srcTextures: dict[int, Image.Image|None]
	fonts: dict[int, FontOptions]
	dstTexPath: str
	operations: list[ImgOperation]

	def __init__(self, argsJson: dict):
		self.srcTexPaths = argsJson.get("srcTexPaths", [])
		self.dstTexPath = argsJson.get("dstTexPath", None)
		self.operations = [ImgOperation(d) for d in argsJson.get("operations", [])]

		self.srcTextures = {}
		for srcTexId, srcTexPath in enumerate(self.srcTexPaths):
			self.srcTextures[srcTexId] = Image.open(srcTexPath)

		self.fonts = {}
		for fontId, fontOptions in argsJson.get("fonts", {}).items():
			self.fonts[fontId] = FontOptions(fontOptions)
