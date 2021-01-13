"""

"""

from yoyo import step

__depends__ = {'20201209_02_i5rFY'}

steps = [
    step(
	"INSERT INTO options (key,value) VALUES ('startTime', '19:00')",
	"DELETE FROM options WHERE key = 'startTime'"
	),
    step(
	"INSERT INTO options (key,value) VALUES ('maxDuration', '4')",
	"DELETE FROM options WHERE key = 'maxDuration'"
	),
    step(
	"INSERT INTO options (key,value) VALUES ('heat', '0')",
	"DELETE FROM options WHERE key = 'heat'"
	),
    step(
	"INSERT INTO options (key,value) VALUES ('rain', '0')",
	"DELETE FROM options WHERE key = 'rain'"
	),
    step(
	"INSERT INTO options (key,value) VALUES ('pause', '0')",
	"DELETE FROM options WHERE key = 'pause'"
	),
    step(
	"INSERT INTO options (key,value) VALUES ('disable', '0')",
	"DELETE FROM options WHERE key = 'enable'"
	)

]
