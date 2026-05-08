alter table "userProfile"
  add column if not exists badges text[] default '{}';
