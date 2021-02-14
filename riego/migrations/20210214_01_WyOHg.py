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
	"is_supervisor"	INTEGER,
	"is_disabled"	INTEGER DEFAULT 0,
	"remember_me"	TEXT UNIQUE,
	"created_at"	timestamp DEFAULT CURRENT_TIMESTAMP,
	PRIMARY KEY("id")'''
    ),(
    '''DROP TABLE users'''
    ),
    step(
    '''INSERT INTO "users"
    ("identity","password","is_supervisor") 
    VALUES ("admin","8c6976e5b5410415bde908bd4dee15dfb167a9c873fc4bb8a81f6f2ab448a918",1)'''
    ),(
    '''DELETE FROM users WHERE identity = "admin" '''
    )

]
