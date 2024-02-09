create table phrases (
	id integer primary key autoincrement,
	stack_id integer,
	words varchar(50),
	stale boolean default FALSE,
	constraint fk_stack
	  foreign key(stack_id)
	  references stacks(id)
		on delete cascade
);

