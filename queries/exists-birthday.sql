SELECT EXISTS (
	SELECT id
	FROM birthdays
	WHERE id = ?
)
