import locale
import json
import sys

common = ["en_US.UTF-8","zh_CN.UTF-8","ru_RU.UTF-8","fr_FR.UTF-8","es_ES.UTF-8","en_GB.UTF-8","de_DE.UTF-8","pt_BR.UTF-8","en_CA.UTF-8","es_MX.UTF-8","it_IT.UTF-8","ja_JP.UTF-8"]

loc = locale.getlocale()
if loc[0] and loc[1]:
	print(json.dumps(loc[0]+"."+loc[1]))
else:
	supported = [v for k,v in locale.locale_alias.items() if v.endswith("UTF-8")]
	print(json.dumps(supported),file=sys.stderr)
	for cc in common:
		if cc in supported:
			print(json.dumps(cc))
			sys.exit(0)
	if supported:
		print(json.dumps(supported[0]))
	else:
		# desperate, give a default and cross fingers
		print(json.dumps(common[0]))
