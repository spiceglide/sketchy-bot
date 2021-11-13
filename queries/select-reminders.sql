SELECT title, member
FROM reminders
WHERE time < ?
ORDER BY time