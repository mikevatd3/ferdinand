create table definitions (
  id integer primary key autoincrement,
  phrase_id integer,
  stack_id integer,
	constraint fk_phrase_def
	  foreign key(phrase_id)
	  references phrases(id)
		on delete cascade
  constraint fk_def_stack
	  foreign key(stack_id)
	  references stacks(id)
		on delete cascade
);

