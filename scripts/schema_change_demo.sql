-- Step 7 demo: change the source schema while the pipeline is running.
-- Run with:
--   Get-Content scripts\schema_change_demo.sql | docker exec -i mysql mysql -uroot -prootpass shop
--
-- What happens downstream:
--   * Debezium records the ALTER in its schema history and adds sales_channel to new events.
--   * Spark keeps writing: bronze stores the row as JSON, so a new field changes nothing there.
--   * dbt's silver_orders reads sales_channel; rows changed before the ALTER show NULL (unknown).
--   * The replayer keeps working because its INSERT into orders names its columns explicitly.

ALTER TABLE orders ADD COLUMN sales_channel VARCHAR(20) NULL COMMENT 'added later: web or mobile_app';

-- Tag the orders that are still open, so the new column appears in update events right away.
UPDATE orders
SET sales_channel = IF(RAND() < 0.3, 'mobile_app', 'web')
WHERE order_status IN ('created', 'approved');
