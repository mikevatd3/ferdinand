create table notes (
	id integer primary key autoincrement,
	phrase_id integer,
	words text default '',
	definition_status varchar(12) default 'NEW',
	constraint phrase_notes
	  foreign key(phrase_id)
	  references phrases(id)
		on delete cascade
);

