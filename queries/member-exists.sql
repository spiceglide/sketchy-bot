SELECT EXISTS (
	SELECT id
	FROM members
	WHERE id = ?
)
