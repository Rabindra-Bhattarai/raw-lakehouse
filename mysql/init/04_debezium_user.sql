-- Debezium reads the binlog as its own user, with only the rights it needs:
-- SELECT for the first snapshot, REPLICATION for the binlog stream, RELOAD for snapshot locks.

CREATE USER IF NOT EXISTS 'debezium'@'%' IDENTIFIED BY 'debezium';
GRANT SELECT, RELOAD, SHOW DATABASES, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'debezium'@'%';
FLUSH PRIVILEGES;
