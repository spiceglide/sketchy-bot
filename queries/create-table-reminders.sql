CREATE TABLE reminders (
	id INTEGER PRIMARY KEY,
	member INTEGER,
	FOREIGN KEY(member) REFERENCES members(id)
)
