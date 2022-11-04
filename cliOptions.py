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
	letXPadding: int
	letYPadding: int
	letXOffset: int
	letYOffset: int
	bottomBaseline: int|None

	def __init__(self, d: dict):
		self.fontPath = d.get("path")
		self.fontHeight = d.get("height")
		self.fontScale = d.get("scale", 1)
		self.letXPadding = d.get("letXPadding", 0)
		self.letYPadding = d.get("letYPadding", 0)
		self.letXOffset = d.get("letXOffset", 0) + self.letXPadding
		self.letYOffset = d.get("letYOffset", 0) + self.letYPadding
		self.font = ImageFont.truetype(self.fontPath, size=int(self.fontHeight * self.fontScale))
		self.bottomBaseline = None

class CliOptions:
	srcTexPaths: list[tuple[int, str]]
	srcTextures: dict[int, Image.Image|None]
	fonts: dict[str, FontOptions]
	dstTexPath: str
	letterSpacing: int
	operations: list[ImgOperation]

	def __init__(self, argsJson: dict):
		self.srcTexPaths = argsJson.get("srcTexPaths", [])
		self.dstTexPath = argsJson.get("dstTexPath", None)
		self.letterSpacing = argsJson.get("letterSpacing", 0)
		self.operations = [ImgOperation(d) for d in argsJson.get("operations", [])]

		self.srcTextures = {}
		for srcTexId, srcTexPath in enumerate(self.srcTexPaths):
			self.srcTextures[srcTexId] = Image.open(srcTexPath)

		self.fonts = {}
		for fontId, fontOptions in argsJson.get("fonts", {}).items():
			self.fonts[fontId] = FontOptions(fontOptions)
