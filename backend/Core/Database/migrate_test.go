package Database

import (
	"testing"
	"testing/fstest"
)

func TestLoadMigrations(t *testing.T) {
	fsys := fstest.MapFS{
		"migrations/001_users.up.sql":   {Data: []byte("CREATE TABLE users (id BIGINT PRIMARY KEY);")},
		"migrations/001_users.down.sql": {Data: []byte("DROP TABLE users;")},
		"migrations/002_jobs.up.sql":    {Data: []byte("CREATE TABLE jobs (id BIGINT PRIMARY KEY);")},
		"migrations/002_jobs.down.sql":  {Data: []byte("DROP TABLE jobs;")},
	}

	r := &MigrationRunner{FS: fsys, Directory: "migrations"}
	got, err := r.Load()
	if err != nil {
		t.Fatal(err)
	}
	if len(got) != 2 || got[0].Version != 1 || got[1].Version != 2 {
		t.Fatalf("unexpected migrations: %+v", got)
	}
	if got[0].Checksum == "" {
		t.Fatal("checksum must be populated")
	}
}

func TestLoadRejectsMissingDown(t *testing.T) {
	fsys := fstest.MapFS{
		"migrations/001_users.up.sql": {Data: []byte("CREATE TABLE users (id BIGINT PRIMARY KEY);")},
	}
	r := &MigrationRunner{FS: fsys, Directory: "migrations"}
	if _, err := r.Load(); err == nil {
		t.Fatal("expected missing down migration error")
	}
}

func TestLoadRejectsMalformedFile(t *testing.T) {
	fsys := fstest.MapFS{
		"migrations/notes.sql": {Data: []byte("-- no")},
	}
	r := &MigrationRunner{FS: fsys, Directory: "migrations"}
	if _, err := r.Load(); err == nil {
		t.Fatal("expected malformed migration error")
	}
}
