create table sentences (
	id integer primary key autoincrement,
	stack_id integer,
	words text,
  timestamp timestamp default current_timestamp,
	constraint fk_stack_sentences
	  foreign key(stack_id)
		references stacks(id)
		on delete cascade
);

