CREATE TABLE birthdays (
	id INTEGER PRIMARY KEY,
	date TEXT NOT NULL,
	FOREIGN KEY(id) REFERENCES members(id) ON DELETE SET NULL
)