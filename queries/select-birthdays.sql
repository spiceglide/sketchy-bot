SELECT id
FROM birthdays
WHERE strftime('%m-%d', date) = strftime('%m-%d', ?)