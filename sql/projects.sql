create table projects (
	id integer primary key autoincrement,
	project_name varchar(100),
	description text default '',
	creator integer,
  created_at timestamp default current_timestamp,
	constraint project_creator
	  foreign key(creator)
	  references users(id)
		on delete cascade
);
