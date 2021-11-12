SELECT EXISTS (
	SELECT id
	FROM roles
	WHERE id = ?
)
