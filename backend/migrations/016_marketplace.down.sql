DROP TABLE IF EXISTS settlements;
DROP TABLE IF EXISTS ratings;
ALTER TABLE tasks
 DROP FOREIGN KEY fk_tasks_service, DROP INDEX idx_tasks_location_status, DROP INDEX idx_tasks_service_status,
 DROP COLUMN service_id, DROP COLUMN country, DROP COLUMN county, DROP COLUMN city, DROP COLUMN area, DROP COLUMN latitude, DROP COLUMN longitude;
DROP TABLE IF EXISTS service_listings;
DROP TABLE IF EXISTS provider_locations;
DROP TABLE IF EXISTS provider_profiles;
DROP TABLE IF EXISTS service_categories;
