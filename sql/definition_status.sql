create table definition_status (
	definition_id int references definitions(id),
	status varchar(5)
);

