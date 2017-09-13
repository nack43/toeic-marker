-- drop table if exists user;
-- user table
create table
if not exists user (
  user_id integer primary key autoincrement,
  first_name text not null,
  last_name text not null,
  password text not null
);

-- exam table 
create table
if not exists exam (
  exam_id integer primary key,
  exam_name text not null
);

-- part table
create table
if not exists part (
  part_id integer primary key,
  part_type text not null
);

-- problem table
create table
if not exists problem (
  exam_id integer not null,
  problem_id integer not null,
  part_id integer not null,
  correct_answer text not null,
  foreign key(exam_id) references exam(exam_id),
  foreign key(part_id) references part(part_id),
  primary key(exam_id, part_id)
);

-- exam date table
create table
if not exists exam_date (
  exam_date_id integer primary key autoincrement,
  exam_id integer unique,
  user_id integer unique,
  exam_date text unique,
  foreign key(exam_id) references exam(exam_id),
  foreign key(user_id) references user(user_id)
);

-- user answer table
create table
if not exists user_answer (
  exam_date_id integer not null,
  problem_id integer not null,
  user_answer text,
  foreign key(exam_date_id) references exam_date(exam_date_id),
  foreign key(problem_id) references problem(problem_id),
  primary key(exam_date_id, problem_id)
);

-- answer ratio table
create table
if not exists answer_ratio (
  exam_date_id integer primary key,
  total_ratio real,
  total_answer_flag text not null,
  foreign key(exam_date_id) references exam_date(exam_date_id)
);

-- part answer ratio table
create table
if not exists part_answer_ratio (
  exam_date_id integer not null,
  part_id integer not null,
  part_ratio real,
  part_answer_flag text not null,
  foreign key(exam_date_id) references exam(exam_date_id),
  foreign key(part_id) references part(part_id),
  primary key(exam_date_id, part_id)
);

