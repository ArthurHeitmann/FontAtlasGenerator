import json
import os
import sys

from cliOptions import CliOptions
from fontAtlasGenerator import generateFontAtlas

# debugArgs = {
# 	"dstTexPath": "atlasTest.png",
# 	"fonts": {
# 		"0": {
# 			"path": "C:\\Windows\\Fonts\\arial.ttf",
# 			"height": 32,
# 			"scale": 1
# 		},
# 		"1": {
# 			"path": "CascadiaMono.ttf",
# 			"height": 32,
# 			"scale": 1
# 		}
# 	},
# 	"srcTexPaths": [
# 		"D:\\delete\\mods\\na\\blender\\extracted\\data009.cpk_unpacked\\ui\\nier2blender_extracted\\ui_core_us.dtt\\messcore.wtp.png"
# 	],
# 	"operations": [
# 		{
# 			"type": 1,
# 			"id": 0,
# 			"drawChar": "A",
# 			"charFontId": "0"
# 		},
# 		{
# 			"type": 1,
# 			"id": 1,
# 			"drawChar": "C",
# 			"charFontId": "0"
# 		},
# 		{
# 			"type": 1,
# 			"id": 2,
# 			"drawChar": "B",
# 			"charFontId": "1"
# 		},
# 	]
# }

if __name__ == "__main__":
	# print(sys.argv[1])
	# options = json.loads(sys.argv[1])
	options = json.loads(input())
	# options = debugArgs
	atlasMap = generateFontAtlas(CliOptions(options))
	print(json.dumps(atlasMap))
