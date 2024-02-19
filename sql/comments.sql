create table comments (
	id integer primary key autoincrement,
	phrase_id integer,
	user_id integer,
	words text default '',
	definition_status varchar(12) default 'NEW',
  timestamp timestamp default current_timestamp,
	constraint phrase_comment
	  foreign key(phrase_id)
	  references phrases(id)
		on delete cascade
	constraint user_comment
	  foreign key(user_id)
	  references users(id)
		on delete cascade
);
