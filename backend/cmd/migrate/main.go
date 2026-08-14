package main

import (
	"context"
	"embed"
	"errors"
	"flag"
	"fmt"
	"log"
	"os"
	"strconv"
	"time"

	"github.com/alumasinde/jijenge/Core/Database"
)

//go:embed migrations/*.sql
var migrationFS embed.FS

func main() {
	command := flag.String("command", "up", "migration command: up, down, status")
	target := flag.Uint64("target", 0, "down target version; 0 means rollback all")
	flag.Parse()

	driver := os.Getenv("DB_DRIVER")
	dsn := os.Getenv("DB_DSN")
	if driver == "" {
		driver = "mysql"
	}
	if dsn == "" {
		log.Fatal("DB_DSN is required")
	}

	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()

	db, err := Database.Open(ctx, driver, Database.Config{
		DSN:             dsn,
		MaxOpenConns:    envInt("DB_MAX_OPEN_CONNS", 10),
		MaxIdleConns:    envInt("DB_MAX_IDLE_CONNS", 5),
		ConnMaxLifetime: envDuration("DB_CONN_MAX_LIFETIME", 30*time.Minute),
		ConnMaxIdleTime: envDuration("DB_CONN_MAX_IDLE_TIME", 5*time.Minute),
	})
	if err != nil {
		log.Fatal(err)
	}
	defer db.Close()

	runner := &Database.MigrationRunner{
		DB:        db,
		FS:        migrationFS,
		Directory: "migrations",
	}

	switch *command {
	case "up":
		err = runner.Up(ctx)
	case "down":
		err = runner.Down(ctx, *target)
	case "status":
		err = status(ctx, runner)
	default:
		err = errors.New("unsupported migration command")
	}

	if err != nil {
		log.Fatal(err)
	}
}

func status(ctx context.Context, runner *Database.MigrationRunner) error {
	if err := runner.EnsureTable(ctx); err != nil {
		return err
	}
	applied, err := runner.Applied(ctx)
	if err != nil {
		return err
	}
	migrations, err := runner.Load()
	if err != nil {
		return err
	}
	for _, migration := range migrations {
		record, ok := applied[migration.Version]
		if !ok {
			fmt.Printf("%03d %-40s pending\n", migration.Version, migration.Name)
			continue
		}
		state := "applied"
		if record.Dirty {
			state = "DIRTY"
		}
		fmt.Printf("%03d %-40s %s\n", migration.Version, migration.Name, state)
	}
	return nil
}

func envInt(key string, fallback int) int {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	n, err := strconv.Atoi(value)
	if err != nil || n <= 0 {
		return fallback
	}
	return n
}

func envDuration(key string, fallback time.Duration) time.Duration {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	d, err := time.ParseDuration(value)
	if err != nil || d <= 0 {
		return fallback
	}
	return d
}
