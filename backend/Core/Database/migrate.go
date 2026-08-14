package Database

import (
	"context"
	"crypto/sha256"
	"database/sql"
	"encoding/hex"
	"errors"
	"fmt"
	"io/fs"
	"path"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

var (
	ErrMigrationDirty     = errors.New("migration state is dirty")
	ErrMigrationChecksum  = errors.New("migration checksum mismatch")
	ErrMigrationVersion   = errors.New("migration version conflict")
	ErrMigrationMalformed = errors.New("malformed migration filename")
)

type Migration struct {
	Version  uint64
	Name     string
	UpSQL    string
	DownSQL  string
	Checksum string
}

type MigrationRunner struct {
	DB        *DB
	FS        fs.FS
	Directory string
}

var migrationFileRE = regexp.MustCompile(`^([0-9]{3,})_([a-zA-Z0-9][a-zA-Z0-9_-]*)\.(up|down)\.sql$`)

func (r *MigrationRunner) EnsureTable(ctx context.Context) error {
	const migrationsTable = `
CREATE TABLE IF NOT EXISTS schema_migrations (
    version BIGINT UNSIGNED NOT NULL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    checksum CHAR(64) NOT NULL,
    dirty BOOLEAN NOT NULL DEFAULT FALSE,
    applied_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB`
	if _, err := r.DB.SQL.ExecContext(ctx, migrationsTable); err != nil {
		return fmt.Errorf("create schema_migrations: %w", err)
	}

	const lockTable = `
CREATE TABLE IF NOT EXISTS schema_migration_lock (
    id TINYINT UNSIGNED NOT NULL PRIMARY KEY,
    created_at TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6)
) ENGINE=InnoDB`
	if _, err := r.DB.SQL.ExecContext(ctx, lockTable); err != nil {
		return fmt.Errorf("create schema_migration_lock: %w", err)
	}
	return nil
}

func (r *MigrationRunner) Load() ([]Migration, error) {
	if r.FS == nil {
		return nil, errors.New("migration filesystem is required")
	}
	entries, err := fs.ReadDir(r.FS, r.Directory)
	if err != nil {
		return nil, fmt.Errorf("read migration directory: %w", err)
	}

	type part struct {
		version   uint64
		name      string
		up        string
		down      string
		upFound   bool
		downFound bool
	}
	parts := map[uint64]*part{}

	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		m := migrationFileRE.FindStringSubmatch(entry.Name())
		if m == nil {
			return nil, fmt.Errorf("%w: %s", ErrMigrationMalformed, entry.Name())
		}
		version, err := strconv.ParseUint(m[1], 10, 64)
		if err != nil {
			return nil, fmt.Errorf("%w: %s", ErrMigrationMalformed, entry.Name())
		}
		name := m[2]
		item := parts[version]
		if item == nil {
			item = &part{version: version, name: name}
			parts[version] = item
		}
		if item.name != name {
			return nil, fmt.Errorf("%w: version %d has multiple names", ErrMigrationVersion, version)
		}
		data, err := fs.ReadFile(r.FS, path.Join(r.Directory, entry.Name()))
		if err != nil {
			return nil, fmt.Errorf("read %s: %w", entry.Name(), err)
		}
		switch m[3] {
		case "up":
			if item.upFound {
				return nil, fmt.Errorf("%w: duplicate up migration %d", ErrMigrationVersion, version)
			}
			item.up = string(data)
			item.upFound = true
		case "down":
			if item.downFound {
				return nil, fmt.Errorf("%w: duplicate down migration %d", ErrMigrationVersion, version)
			}
			item.down = string(data)
			item.downFound = true
		}
	}

	migrations := make([]Migration, 0, len(parts))
	for _, item := range parts {
		if !item.upFound || !item.downFound {
			return nil, fmt.Errorf("%w: migration %d requires both up and down files", ErrMigrationVersion, item.version)
		}
		checksum := sha256.Sum256([]byte(normalizeSQL(item.up)))
		migrations = append(migrations, Migration{
			Version:  item.version,
			Name:     item.name,
			UpSQL:    item.up,
			DownSQL:  item.down,
			Checksum: hex.EncodeToString(checksum[:]),
		})
	}

	sort.Slice(migrations, func(i, j int) bool { return migrations[i].Version < migrations[j].Version })

	for i := 1; i < len(migrations); i++ {
		if migrations[i].Version == migrations[i-1].Version {
			return nil, fmt.Errorf("%w: duplicate version %d", ErrMigrationVersion, migrations[i].Version)
		}
	}
	return migrations, nil
}

type AppliedMigration struct {
	Version  uint64
	Name     string
	Checksum string
	Dirty    bool
}

func (r *MigrationRunner) Applied(ctx context.Context) (map[uint64]AppliedMigration, error) {
	rows, err := r.DB.SQL.QueryContext(ctx, `SELECT version, name, checksum, dirty FROM schema_migrations ORDER BY version`)
	if err != nil {
		return nil, fmt.Errorf("query schema_migrations: %w", err)
	}
	defer rows.Close()

	result := make(map[uint64]AppliedMigration)
	for rows.Next() {
		var m AppliedMigration
		if err := rows.Scan(&m.Version, &m.Name, &m.Checksum, &m.Dirty); err != nil {
			return nil, fmt.Errorf("scan schema migration: %w", err)
		}
		result[m.Version] = m
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate schema migrations: %w", err)
	}
	return result, nil
}

func (r *MigrationRunner) Up(ctx context.Context) error {
	if err := r.EnsureTable(ctx); err != nil {
		return err
	}
	unlock, err := r.acquireMigrationLock(ctx)
	if err != nil {
		return err
	}
	defer unlock()

	migrations, err := r.Load()
	if err != nil {
		return err
	}
	applied, err := r.Applied(ctx)
	if err != nil {
		return err
	}

	for _, migration := range migrations {
		if current, ok := applied[migration.Version]; ok {
			if current.Dirty {
				return fmt.Errorf("%w at version %d", ErrMigrationDirty, migration.Version)
			}
			if current.Name != migration.Name || current.Checksum != migration.Checksum {
				return fmt.Errorf("%w at version %d", ErrMigrationChecksum, migration.Version)
			}
			continue
		}
		if err := r.applyOne(ctx, migration); err != nil {
			return err
		}
	}
	return nil
}

func (r *MigrationRunner) applyOne(ctx context.Context, migration Migration) error {
	tx, err := r.DB.SQL.BeginTx(ctx, &sql.TxOptions{})
	if err != nil {
		return fmt.Errorf("begin migration %d: %w", migration.Version, err)
	}

	insert := `INSERT INTO schema_migrations(version, name, checksum, dirty) VALUES (?, ?, ?, TRUE)`
	if _, err := tx.ExecContext(ctx, insert, migration.Version, migration.Name, migration.Checksum); err != nil {
		_ = tx.Rollback()
		return fmt.Errorf("mark migration %d dirty: %w", migration.Version, err)
	}

	if _, err := tx.ExecContext(ctx, migration.UpSQL); err != nil {
		_ = tx.Rollback()
		// The dirty row is rolled back with the migration. This is deliberate:
		// a failed migration leaves no partially-created tables from that transaction.
		return fmt.Errorf("apply migration %d: %w", migration.Version, err)
	}

	if _, err := tx.ExecContext(ctx,
		`UPDATE schema_migrations SET dirty = FALSE, applied_at = CURRENT_TIMESTAMP(6) WHERE version = ?`,
		migration.Version,
	); err != nil {
		_ = tx.Rollback()
		return fmt.Errorf("finalize migration %d: %w", migration.Version, err)
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit migration %d: %w", migration.Version, err)
	}
	return nil
}

func (r *MigrationRunner) Down(ctx context.Context, target uint64) error {
	if err := r.EnsureTable(ctx); err != nil {
		return err
	}
	unlock, err := r.acquireMigrationLock(ctx)
	if err != nil {
		return err
	}
	defer unlock()

	migrations, err := r.Load()
	if err != nil {
		return err
	}
	applied, err := r.Applied(ctx)
	if err != nil {
		return err
	}

	byVersion := make(map[uint64]Migration, len(migrations))
	for _, m := range migrations {
		byVersion[m.Version] = m
	}

	versions := make([]uint64, 0, len(applied))
	for version, record := range applied {
		if record.Dirty {
			return fmt.Errorf("%w at version %d", ErrMigrationDirty, version)
		}
		if version > target {
			versions = append(versions, version)
		}
	}
	sort.Slice(versions, func(i, j int) bool { return versions[i] > versions[j] })

	for _, version := range versions {
		migration, ok := byVersion[version]
		if !ok {
			return fmt.Errorf("%w: applied migration %d is missing from filesystem", ErrMigrationVersion, version)
		}
		if applied[version].Checksum != migration.Checksum {
			return fmt.Errorf("%w at version %d", ErrMigrationChecksum, version)
		}
		if err := r.rollbackOne(ctx, migration); err != nil {
			return err
		}
	}
	return nil
}

func (r *MigrationRunner) rollbackOne(ctx context.Context, migration Migration) error {
	tx, err := r.DB.SQL.BeginTx(ctx, &sql.TxOptions{})
	if err != nil {
		return fmt.Errorf("begin rollback %d: %w", migration.Version, err)
	}

	if _, err := tx.ExecContext(ctx, migration.DownSQL); err != nil {
		_ = tx.Rollback()
		return fmt.Errorf("rollback migration %d: %w", migration.Version, err)
	}
	if _, err := tx.ExecContext(ctx, `DELETE FROM schema_migrations WHERE version = ?`, migration.Version); err != nil {
		_ = tx.Rollback()
		return fmt.Errorf("remove migration record %d: %w", migration.Version, err)
	}
	if err := tx.Commit(); err != nil {
		return fmt.Errorf("commit rollback %d: %w", migration.Version, err)
	}
	return nil
}

func (r *MigrationRunner) acquireMigrationLock(ctx context.Context) (func(), error) {
	tx, err := r.DB.SQL.BeginTx(ctx, &sql.TxOptions{Isolation: sql.LevelReadCommitted})
	if err != nil {
		return nil, fmt.Errorf("begin migration lock: %w", err)
	}
	if _, err := tx.ExecContext(ctx, `INSERT IGNORE INTO schema_migration_lock(id) VALUES(1)`); err != nil {
		_ = tx.Rollback()
		return nil, fmt.Errorf("initialize migration lock: %w", err)
	}
	var id int
	if err := tx.QueryRowContext(ctx, `SELECT id FROM schema_migration_lock WHERE id=1 FOR UPDATE`).Scan(&id); err != nil {
		_ = tx.Rollback()
		return nil, fmt.Errorf("lock migration runner: %w", err)
	}
	return func() { _ = tx.Rollback() }, nil
}

func normalizeSQL(s string) string {
	return strings.Join(strings.Fields(s), " ")
}
