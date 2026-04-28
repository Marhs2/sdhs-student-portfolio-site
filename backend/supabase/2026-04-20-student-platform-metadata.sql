alter table "userProfile"
  add column if not exists school text default '',
  add column if not exists department text default '',
  add column if not exists track text default '',
  add column if not exists tags text[] default '{}',
  add column if not exists featured_rank integer default 9999,
  add column if not exists review_status text default 'draft',
  add column if not exists is_visible boolean default true;

alter table "portfoilo"
  add column if not exists project_role text default '',
  add column if not exists skill_tags text[] default '{}',
  add column if not exists is_featured boolean default false,
  add column if not exists custom_link_url text default '';
