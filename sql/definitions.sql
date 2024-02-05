create table definitions (
  id integer primary key autoincrement,
  phrase_id integer references phrases(id),
  sentence_id integer references sentences(id),
  timestamp timestamp default current_timestamp
);

