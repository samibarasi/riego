"""

"""

from yoyo import step

__depends__ = {'20210131_01_QndU0'}

steps = [
    step(
    '''CREATE TABLE "users" (
	"id"	INTEGER,
	"identity"	TEXT UNIQUE,
	"password"	TEXT,
    "permissions"	TEXT,
	"is_superuser"	INTEGER DEFAULT 0,
	"is_disabled"	INTEGER DEFAULT 0,
	"remember_me"	TEXT,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id"))'''
    ),(
    '''DROP TABLE users'''
    ),
    step(
    '''INSERT INTO "users"
    ("identity","password","is_superuser")
    VALUES ("admin","$2b$12$SsmDaUnej3koYln39Dq9Ue2VBjYd.FyGMeAV9kK3edRjAzLztIaCC",1)'''
    ),(
    '''DELETE FROM users WHERE identity = "admin" '''
    )

]
