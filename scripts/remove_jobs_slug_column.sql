-- Optional: remove `slug` if you ran the old migration before switching to `publicSlug` / publicslug.

ALTER TABLE jobs DROP COLUMN IF EXISTS slug;
