create table phrases (
	id integer primary key autoincrement,
	sentence_id integer references sentences(id),
	words text
);

