CREATE TABLE reminders (
	id INTEGER PRIMARY KEY,
	title TEXT,
	member INTEGER NOT NULL,
	time INTEGER NOT NULL,
	FOREIGN KEY(member) REFERENCES members(id)
)
