-- 0 - restricted
-- 1 - read only
-- 2 - read/write
-- 3 - admin (only creator)

create table permissions (
	user_id integer primary key,
	project_id integer primary key,
	level integer default 0,
	constraint project_permission
	  foreign key(project_id)
		references projects(id)
		on delete cascade
	constraint user_permission
	  foreign key(user_id)
		references users(id)
		on delete cascade
);
