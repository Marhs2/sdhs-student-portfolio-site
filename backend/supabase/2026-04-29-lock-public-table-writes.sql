alter table "userProfile" enable row level security;
alter table "portfoilo" enable row level security;
alter table "userHtml" enable row level security;

alter table "userProfile" alter column review_status set default 'review';
alter table "userProfile" alter column is_visible set default false;

revoke insert, update, delete on table "userProfile" from anon, authenticated;
revoke insert, update, delete on table "portfoilo" from anon, authenticated;
revoke insert, update, delete on table "userHtml" from anon, authenticated;
